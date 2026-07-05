"""Action envelope and structured decision output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

DecisionKind = Literal["allow", "deny", "review", "quarantine", "escalate"]
Severity = Literal["info", "warning", "high", "critical", "constitutional"]


@dataclass
class ActorSpec:
    id: str
    role: str = "unknown"


@dataclass
class ActionSpec:
    kind: str
    resource: str
    risk: str = "medium"  # low | medium | high | protected
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionRequest:
    machine_id: str
    actor: ActorSpec
    action: ActionSpec
    raw_model_output: str = ""
    covenant_record: dict[str, Any] | None = None
    compiler_result: dict[str, Any] | None = None
    case: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionRequest:
        a = data.get("actor") or {}
        ac = data.get("action") or {}
        metadata = ac.get("metadata") or ac.get("context") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        covenant_record = data.get("covenant_record")
        if covenant_record is not None and not isinstance(
            covenant_record, dict
        ):
            covenant_record = None
        compiler_result = data.get("compiler_result")
        if compiler_result is not None and not isinstance(
            compiler_result, dict
        ):
            compiler_result = None
        case = data.get("case")
        if case is not None and not isinstance(case, dict):
            case = None
        return cls(
            machine_id=str(data.get("machine_id") or ""),
            actor=ActorSpec(
                id=str(a.get("id") or ""),
                role=str(a.get("role") or "unknown"),
            ),
            action=ActionSpec(
                kind=str(ac.get("kind") or "unknown"),
                resource=str(ac.get("resource") or ""),
                risk=str(ac.get("risk") or "medium").lower(),
                metadata=metadata,
            ),
            raw_model_output=str(
                data.get("raw_model_output") or data.get("raw_output") or ""
            ),
            covenant_record=covenant_record,
            compiler_result=compiler_result,
            case=case,
        )


@dataclass
class DecisionResult:
    decision: DecisionKind
    severity: str
    reason: str
    tags: list[str] = field(default_factory=list)
    blocking_actions: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "decision": self.decision,
            "severity": self.severity,
            "reason": self.reason,
            "tags": self.tags,
            "blocking_actions": self.blocking_actions,
        }
        if self.evidence:
            out["evidence"] = self.evidence
        return out
