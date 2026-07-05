"""Unit tests for Guard v1 rules (no network)."""

import unittest

from tehuti_guard.models import ActionSpec, ActorSpec, DecisionRequest
from tehuti_guard.rules import (
    compute_explanation_id,
    evaluate,
    evaluate_with_rules,
    explain_envelope,
    policy_rules_document,
)


def _req(mid: str, risk: str = "medium", kind: str = "write") -> DecisionRequest:
    return DecisionRequest(
        machine_id=mid,
        actor=ActorSpec(id="a1", role="agent"),
        action=ActionSpec(kind=kind, resource="/tmp/x", risk=risk),
    )


class TestRules(unittest.TestCase):
    def test_no_sentinel(self) -> None:
        r = evaluate(_req("m1"), None)
        self.assertEqual(r.decision, "review")
        self.assertIn("sentinel", r.reason.lower())

    def test_constitutional_breach_deny_high(self) -> None:
        view = {
            "machine_status": "constitutional_breach",
            "blocking_actions": ["unset X"],
            "immune_summary": {},
        }
        r = evaluate(_req("m1", risk="high"), view)
        self.assertEqual(r.decision, "deny")
        self.assertEqual(r.blocking_actions, ["unset X"])

    def test_unsafe_deny_high_impact(self) -> None:
        view = {"machine_status": "unsafe", "immune_summary": {}}
        r = evaluate(_req("m1", risk="high"), view)
        self.assertEqual(r.decision, "deny")

    def test_immune_constitutional_escalate(self) -> None:
        view = {
            "machine_status": "operational",
            "immune_summary": {"recent_constitutional_count": 2},
            "blocking_actions": [],
        }
        r = evaluate(_req("m1", risk="high", kind="deploy"), view)
        self.assertEqual(r.decision, "escalate")

    def test_operational_low_allow(self) -> None:
        view = {"machine_status": "operational", "immune_summary": {}}
        r = evaluate(_req("m1", risk="low", kind="read"), view)
        self.assertEqual(r.decision, "allow")

    def test_evaluate_with_rules_matches_evaluate(self) -> None:
        view = {"machine_status": "operational", "immune_summary": {}}
        req = _req("m1", risk="low", kind="read")
        r1 = evaluate(req, view)
        r2, rules = evaluate_with_rules(req, view)
        self.assertEqual(r1.decision, r2.decision)
        self.assertEqual(rules, ["operational_low_risk_allow"])

    def test_policy_rules_document(self) -> None:
        doc = policy_rules_document()
        self.assertIn("policy_version", doc)
        self.assertIn("rules", doc)
        self.assertIsInstance(doc["rules"], list)
        self.assertGreaterEqual(len(doc["rules"]), 3)
        ids = {r["id"] for r in doc["rules"]}
        self.assertIn("sentinel_unreachable", ids)

    def test_explain_sentinel_unreachable(self) -> None:
        ex = explain_envelope(_req("m1"), None)
        self.assertEqual(ex["decision"], "review")
        self.assertEqual(ex["matched_rules"], ["sentinel_unreachable_review"])
        self.assertIn("policy_rejection", ex["tags"])
        eid = ex["explanation_id"]
        self.assertTrue(eid.startswith("sha256:"))
        self.assertEqual(len(eid), 7 + 64)
        ex2 = explain_envelope(_req("m1"), None)
        self.assertEqual(ex["explanation_id"], ex2["explanation_id"])

    def test_explain_operational_allow_no_policy_rejection_dup(self) -> None:
        view = {"machine_status": "operational", "immune_summary": {}}
        req = _req("m1", risk="low", kind="read")
        ex = explain_envelope(req, view)
        self.assertEqual(ex["decision"], "allow")
        self.assertEqual(ex["matched_rules"], ["operational_low_risk_allow"])
        self.assertNotIn("policy_rejection", ex["tags"])
        self.assertEqual(
            ex["explanation_id"],
            compute_explanation_id(req, ["operational_low_risk_allow"]),
        )


if __name__ == "__main__":
    unittest.main()
