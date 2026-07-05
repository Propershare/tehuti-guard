# flake8: noqa: E501
"""Optional writes to maat-memory (PostgreSQL) — off unless TEHUTI_GUARD_MEMORY=1."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def _memory_enabled() -> bool:
    v = os.environ.get("TEHUTI_GUARD_MEMORY", "").strip().lower()
    return v in ("1", "true", "yes")


def _ensure_workspace_path() -> None:
    root = os.environ.get("MAAT_WORKSPACE_ROOT", "").strip()
    candidates: list[Path] = []
    if root:
        candidates.append(Path(root))
    here = Path(__file__).resolve()
    for i in range(0, min(12, len(here.parents))):
        candidates.append(here.parents[i])
    for base in candidates:
        ml = base / "maatlangchain"
        if (ml / "maat_memory").is_dir():
            mp = str(ml)
            if mp not in sys.path:
                sys.path.insert(0, mp)
            return
    return


def _try_maat_postgres() -> Any:
    _ensure_workspace_path()
    from maat_memory.memory_postgres import MaatMemoryPostgres  # type: ignore

    return MaatMemoryPostgres()


def log_guard_decision_row(
    raw_envelope: dict[str, Any],
    response: dict[str, Any],
    *,
    agent: str = "tehuti-guard-api",
) -> None:
    if not _memory_enabled():
        return
    try:
        mem = _try_maat_postgres()
        forge = raw_envelope.get("forge_meta") or {}
        payload: dict[str, Any] = {
            "record_type": "guard_decision",
            "source_service": "tehuti-guard-api",
            "machine_id": raw_envelope.get("machine_id"),
            "agent_id": (raw_envelope.get("actor") or {}).get("id"),
            "session_id": forge.get("session_id"),
            "task_id": forge.get("task_id"),
            "correlation_id": raw_envelope.get("correlation_id") or response.get("correlation_id"),
            "decision": response.get("decision"),
            "severity": response.get("severity"),
            "reason": response.get("reason"),
            "matched_rules": response.get("matched_rules") or [],
            "tags": response.get("tags") or [],
            "policy_version": str(response.get("policy_version", "")),
            "explanation_id": response.get("explanation_id"),
        }
        mem.log_governance_event(
            payload,
            agent=agent,
            machine_id=str(payload.get("machine_id") or "") or None,
            explanation_id=payload.get("explanation_id"),
            task_id=str(payload.get("task_id") or "") or None,
            session_id=str(payload.get("session_id") or "") or None,
            correlation_id=str(payload.get("correlation_id") or "") or None,
            source_service="tehuti-guard-api",
        )
    except Exception as e:
        log.debug("TEHUTI_GUARD_MEMORY: skip or failed: %s", e)


def log_guard_explanation_row(
    raw_envelope: dict[str, Any],
    response: dict[str, Any],
    *,
    agent: str = "tehuti-guard-api",
) -> None:
    if not _memory_enabled():
        return
    try:
        mem = _try_maat_postgres()
        payload: dict[str, Any] = {
            "record_type": "guard_explanation",
            "source_service": "tehuti-guard-api",
            "machine_id": raw_envelope.get("machine_id"),
            "correlation_id": raw_envelope.get("correlation_id") or response.get("correlation_id"),
            "explanation_id": response.get("explanation_id"),
            "decision": response.get("decision"),
            "matched_rules": response.get("matched_rules") or [],
            "policy_version": str(response.get("policy_version", "")),
            "severity": response.get("severity"),
            "tags": response.get("tags") or [],
        }
        mem.log_governance_event(
            payload,
            agent=agent,
            machine_id=str(payload.get("machine_id") or "") or None,
            explanation_id=payload.get("explanation_id"),
            correlation_id=str(payload.get("correlation_id") or "") or None,
            source_service="tehuti-guard-api",
        )
    except Exception as e:
        log.debug("TEHUTI_GUARD_MEMORY: explain skip or failed: %s", e)


def log_compile_decision_row(
    raw_envelope: dict[str, Any],
    response: dict[str, Any],
    *,
    agent: str = "tehuti-guard-api",
) -> None:
    if not _memory_enabled():
        return
    try:
        mem = _try_maat_postgres()
        forge = raw_envelope.get("forge_meta") or {}
        compiler = response.get("compiler_result") or {}
        evidence = response.get("evidence") or {}
        payload: dict[str, Any] = {
            "record_type": "guard_compile_decision",
            "source_service": "tehuti-guard-api",
            "machine_id": raw_envelope.get("machine_id"),
            "agent_id": (raw_envelope.get("actor") or {}).get("id"),
            "session_id": forge.get("session_id"),
            "task_id": forge.get("task_id"),
            "correlation_id": raw_envelope.get("correlation_id")
            or response.get("correlation_id"),
            "decision": response.get("decision"),
            "severity": response.get("severity"),
            "reason": response.get("reason"),
            "matched_rules": response.get("matched_rules") or [],
            "tags": response.get("tags") or [],
            "policy_version": str(response.get("policy_version", "")),
            "explanation_id": response.get("explanation_id"),
            "raw_model_output": raw_envelope.get("raw_model_output")
            or raw_envelope.get("raw_output"),
            "compiler_enforced": compiler.get("compiler_enforced"),
            "repairs": compiler.get("repairs") or [],
            "interventions": compiler.get("interventions") or [],
            "repair_burden_score": compiler.get("repair_burden_score"),
            "compiler_confidence": compiler.get("compiler_confidence"),
            "human_review_required": compiler.get("human_review_required"),
            "review_reason": compiler.get("review_reason"),
            "evidence": evidence,
        }
        mem.log_governance_event(
            payload,
            agent=agent,
            machine_id=str(payload.get("machine_id") or "") or None,
            explanation_id=payload.get("explanation_id"),
            task_id=str(payload.get("task_id") or "") or None,
            session_id=str(payload.get("session_id") or "") or None,
            correlation_id=str(payload.get("correlation_id") or "") or None,
            source_service="tehuti-guard-api",
        )
    except Exception as e:
        log.debug("TEHUTI_GUARD_MEMORY: compile decision skip or failed: %s", e)
