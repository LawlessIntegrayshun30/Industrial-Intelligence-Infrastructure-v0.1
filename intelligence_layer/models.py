from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "0.2"

def now() -> str: return datetime.now(timezone.utc).isoformat()
def uid(prefix: str) -> str: return f"{prefix}_{uuid4().hex[:12]}"

class GovernanceDisposition(str, Enum):
    ALLOW = "ALLOW"; DENY = "DENY"; HOLD = "HOLD"; REQUIRES_AUTHORIZATION = "REQUIRES_AUTHORIZATION"; APPROVED = "APPROVED"; DENIED = "DENIED"; INVALID = "INVALID"; EXPIRED = "EXPIRED"

@dataclass(frozen=True)
class Source:
    source_id: str; name: str; reliability: float = 0.9; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Observation:
    observation_id: str; timestamp: str; source_id: str; entity_id: str; metric: str; value: float; unit: str; confidence: float; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Event:
    event_id: str; timestamp: str; source: Source; entity_id: str; event_type: str; payload: dict[str, Any]; observation_ids: list[str] = field(default_factory=list); schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Entity:
    entity_id: str; entity_type: str = "industrial_asset"; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class State:
    state_id: str; entity_id: str; timestamp: str; values: dict[str, float]; event_ids: list[str]; confidence: float; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Signal:
    signal_id: str; timestamp: str; entity_id: str; type: str; severity: str; confidence: float; evidence: list[str]; explanation: str; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str; timestamp: str; entity_id: str; statement: str; confidence: float; signal_ids: list[str]; provider: str; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Prediction:
    prediction_id: str; timestamp: str; entity_id: str; statement: str; horizon_minutes: int; confidence: float; hypothesis_ids: list[str]; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str; timestamp: str; entity_id: str; statement: str; confidence: float; prediction_ids: list[str]; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class ActionProposal:
    action_id: str; timestamp: str; action_type: str; target: str; parameters: dict[str, Any]; reason: str; confidence: float; requires_governance: bool = True; status: str = "proposed"; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Outcome:
    outcome_id: str; timestamp: str; action_id: str; status: str; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class GovernanceResult:
    action_id: str; disposition: GovernanceDisposition; reason: str; timestamp: str = field(default_factory=now); decision_id: str | None = None; action_intent_id: str | None = None

@dataclass(frozen=True)
class GovernanceDecision:
    decision_id: str; action_intent_id: str; action_proposal_hash: str; proofpack_hash: str; intent_hash: str; requester_identity: str; authorization_identity: str; decision: GovernanceDisposition; scope: str; constraints: dict[str, Any]; issued_at: str; expires_at: str; nonce: str; signature: str; audit_reference: str; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str; action_id: str; decision_id: str | None; status: str; reason: str; timestamp: str = field(default_factory=now); outcome_id: str | None = None

@dataclass(frozen=True)
class AuditEvent:
    event_id: str; event_type: str; timestamp: str; run_id: str; actor_identity: str; source: str; object_id: str; object_type: str; payload: dict[str, Any]; payload_hash: str; previous_event_hash: str; metadata: dict[str, Any]; schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class AuditRecord:
    audit_id: str; run_id: str; timestamp: str; stage: str; input_ids: list[str]; output_ids: list[str]; provider: str; latency_ms: float; status: str; confidence: float | None = None; error: str | None = None

@dataclass(frozen=True)
class Decision:
    decision_id: str; run_id: str; timestamp: str; entity_ids: list[str]; state_ids: list[str]; signal_ids: list[str]; hypothesis_ids: list[str]; prediction_ids: list[str]; recommendation_ids: list[str]; action_ids: list[str]; confidence: float; provenance: dict[str, list[str]]; schema_version: str = SCHEMA_VERSION

def serialise(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if is_dataclass(value): return {k: serialise(v) for k, v in asdict(value).items()}
    if isinstance(value, list): return [serialise(v) for v in value]
    if isinstance(value, dict): return {k: serialise(v) for k, v in value.items()}
    return value
