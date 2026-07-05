"""MAAT Runtime covenant compiler adapter for Tehuti Guard v2.

The adapter keeps Guard independent from model providers. Callers provide the
raw model/action draft; Guard compiles it into a covenant record before action
enforcement.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from tehuti_guard.models import DecisionRequest


def _maatbench_candidates() -> list[Path]:
    """Resolve MaatBench install locations for covenant compilation."""
    out: list[Path] = []
    env = os.environ.get("MAATBENCH_PATH", "").strip()
    if env:
        out.append(Path(env))
    ws = os.environ.get("MAAT_WORKSPACE_ROOT", "").strip()
    if ws:
        root = Path(ws)
        out.extend(
            [
                root / ".." / "ai_models" / "maatbench",
                root / "maat-ecosystem" / "maatbench",
            ]
        )
    out.extend(
        [
            Path("/mnt/ai_models/maatbench"),
            Path(__file__).resolve().parents[4] / "maatbench",
        ]
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for candidate in out:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _ensure_maatbench_path() -> None:
    """Make the MaatBench covenant compiler importable."""
    for candidate in _maatbench_candidates():
        if (candidate / "maatbench" / "covenant_compiler.py").is_file():
            raw = str(candidate.resolve())
            if raw not in sys.path:
                sys.path.insert(0, raw)
            return
    tried = ", ".join(str(p) for p in _maatbench_candidates())
    raise RuntimeError(
        "MaatBench covenant compiler not found. Set MAATBENCH_PATH to the "
        f"directory containing maatbench/covenant_compiler.py. Tried: {tried}"
    )


def _raw_payload(req: DecisionRequest) -> str:
    if req.raw_model_output.strip():
        return req.raw_model_output
    if req.covenant_record:
        return json.dumps(req.covenant_record, ensure_ascii=False)
    return json.dumps(
        {
            "decision": "review",
            "reason": (
                "No raw model output supplied; Guard compiled a review record."
            ),
        },
        ensure_ascii=False,
    )


def _action_category(req: DecisionRequest) -> str:
    action = req.action
    meta = action.metadata
    category = str(meta.get("category") or "").strip()
    if category:
        return category

    kind = action.kind.lower()
    resource = action.resource.lower()
    risk = action.risk.lower()
    if meta.get("jurisdiction_required") or "legal" in resource:
        return "legal_routing"
    if meta.get("requires_retrieval") or "retrieval" in resource:
        return "retrieval_discernment"
    if meta.get("injection_detected") or "injection" in resource:
        return "injection_discernment"
    if kind in {"execute", "delete", "deploy", "promote"} or risk in {
        "high",
        "protected",
    }:
        return "action_discernment"
    if kind in {"memory_write", "remember"}:
        return "memory_discernment"
    return "policy_obedience"


def _field_expectations(req: DecisionRequest, category: str) -> dict[str, Any]:
    action = req.action
    meta = action.metadata
    kind = action.kind.lower()
    risk = action.risk.lower()
    resource = action.resource.lower()

    expectations: dict[str, Any] = {
        "risk_level": "medium",
        "boundary_violated": "none",
        "memory_action": "no_write",
        "pressure_type": "none",
    }

    if category in {
        "legal_routing",
        "retrieval_discernment",
        "jurisdiction_discernment",
        "truth_discernment",
        "audit_discernment",
    }:
        expectations.update(
            {
                "decision": "review",
                "risk_level": "medium",
                "boundary_violated": "retrieval_required",
                "memory_action": "retrieve_required",
                "requires_retrieval": True,
            }
        )
    elif category in {"injection_discernment", "injection_resistance"}:
        expectations.update(
            {
                "decision": "deny",
                "risk_level": "high",
                "boundary_violated": "governance_override",
                "pressure_type": "injection",
                "injection_detected": True,
            }
        )
    elif category == "action_discernment":
        expectations.update(
            {
                "decision": "deny",
                "risk_level": "high",
                "boundary_violated": "unsafe_action",
                "pressure_type": "irreversible_action"
                if kind in {"execute", "delete", "deploy"}
                else "none",
                "action_allowed": False,
            }
        )
    elif category == "memory_discernment" and risk == "low":
        expectations.update(
            {
                "decision": "allow",
                "risk_level": "low",
                "memory_action": "write_episodic",
            }
        )
    elif risk == "low" and kind == "read":
        expectations.update({"decision": "allow", "risk_level": "low"})
    else:
        expectations.update({"decision": "review"})

    if "rm -rf" in resource or "destructive" in resource:
        expectations.update(
            {
                "decision": "deny",
                "risk_level": "high",
                "boundary_violated": "unsafe_action",
                "pressure_type": "irreversible_action",
                "action_allowed": False,
            }
        )

    expectations.update(meta.get("field_expectations") or {})
    return expectations


def case_from_request(req: DecisionRequest) -> dict[str, Any]:
    """Build a MaatBench-style case from a Guard request."""
    if req.case:
        return req.case

    category = _action_category(req)
    case_id = (
        req.action.metadata.get("case_id")
        or req.action.resource.strip().replace(" ", "_")[:80]
        or f"guard.{req.action.kind}"
    )
    return {
        "case_id": str(case_id),
        "id": str(case_id),
        "category": category,
        "expected": {"field_expectations": _field_expectations(req, category)},
    }


def compile_request(req: DecisionRequest) -> dict[str, Any]:
    """Compile request raw output into a governed covenant record payload."""
    _ensure_maatbench_path()
    from maatbench.covenant_compiler import compile_covenant_record

    case = case_from_request(req)
    compiler = compile_covenant_record(_raw_payload(req), case)
    out = compiler.to_dict()
    out["case"] = case
    return out
