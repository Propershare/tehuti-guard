"""Tests for MAAT Runtime covenant compile-decision enforcement."""

import json
import unittest

from tehuti_guard.covenant_adapter import compile_request
from tehuti_guard.models import ActionSpec, ActorSpec, DecisionRequest
from tehuti_guard.rules import evaluate_compiler_with_rules


def _req(
    *,
    raw: dict,
    kind: str,
    resource: str,
    risk: str,
    metadata: dict | None = None,
) -> DecisionRequest:
    return DecisionRequest(
        machine_id="m1",
        actor=ActorSpec(id="tester", role="agent"),
        action=ActionSpec(
            kind=kind,
            resource=resource,
            risk=risk,
            metadata=metadata or {},
        ),
        raw_model_output=json.dumps(raw),
    )


class TestCompileDecision(unittest.TestCase):
    def test_destructive_unsafe_allow_is_denied(self) -> None:
        req = _req(
            raw={
                "decision": "allow",
                "reason": "User asked to free disk space.",
            },
            kind="execute",
            resource="rm -rf /",
            risk="high",
            metadata={"category": "action_discernment"},
        )
        compiler = compile_request(req)
        result, rules = evaluate_compiler_with_rules(
            req,
            {"machine_status": "operational", "immune_summary": {}},
            compiler,
        )
        self.assertEqual(result.decision, "deny")
        self.assertIn("compiler_forced_deny", rules)
        self.assertEqual(
            compiler["compiler_enforced"]["boundary_violated"],
            "unsafe_action",
        )

    def test_legal_retrieval_routes_to_review(self) -> None:
        req = _req(
            raw={
                "decision": "defer",
                "reason": "Needs legal retrieval first.",
                "memory_action": "none",
            },
            kind="answer",
            resource="legal: Florida trustee removal",
            risk="high",
            metadata={
                "category": "legal_routing",
                "requires_retrieval": True,
            },
        )
        compiler = compile_request(req)
        result, rules = evaluate_compiler_with_rules(
            req,
            {"machine_status": "operational", "immune_summary": {}},
            compiler,
        )
        self.assertEqual(result.decision, "review")
        self.assertIn("compiler_human_review", rules)
        self.assertTrue(compiler["human_review_required"])

    def test_safe_memory_write_can_allow(self) -> None:
        req = _req(
            raw={
                "decision": "allow",
                "reason": "Safe benign preference.",
                "memory_action": "write_episodic",
            },
            kind="memory_write",
            resource="preferred meeting time 10:00 ET",
            risk="low",
            metadata={"category": "memory_discernment"},
        )
        compiler = compile_request(req)
        result, rules = evaluate_compiler_with_rules(
            req,
            {"machine_status": "operational", "immune_summary": {}},
            compiler,
        )
        self.assertEqual(result.decision, "allow")
        self.assertIn("compiler_allow", rules)
        self.assertEqual(
            compiler["compiler_enforced"]["memory_action"],
            "write_episodic",
        )

    def test_compiler_evidence_is_attached_to_result(self) -> None:
        req = _req(
            raw={"decision": "allow", "reason": "Safe read."},
            kind="read",
            resource="/tmp/readme",
            risk="low",
        )
        compiler = compile_request(req)
        result, _ = evaluate_compiler_with_rules(
            req,
            {"machine_status": "operational", "immune_summary": {}},
            compiler,
        )
        out = result.to_dict()
        self.assertIn("evidence", out)
        self.assertIn("compiler_enforced", out["evidence"])
        self.assertIn("repair_burden_score", out["evidence"])


if __name__ == "__main__":
    unittest.main()
