"""Post-governance mock execution boundary. No real system calls exist here."""
from __future__ import annotations
from datetime import datetime, timezone
from .authorization import decision_bytes
from .event_store import EventStore, ROLES, digest
from .identity import TrustRegistry
from .models import ExecutionResult, GovernanceDecision, GovernanceDisposition, uid

class MockExecutionProvider:
    def __init__(self): self.accepted=[]
    def execute(self, action): self.accepted.append(action.action_id); return "EXECUTION_COMPLETED"

class ExecutionGateway:
    def __init__(self, identity, trust: TrustRegistry, store: EventStore, provider: MockExecutionProvider):
        if identity.role != "execution": raise ValueError("execution identity required")
        self.identity,self.trust,self.store,self.provider=identity,trust,store,provider; self._consumed_nonces=set()
    def execute(self, *, run_id: str, action, submission, decision: GovernanceDecision | None) -> ExecutionResult:
        error=self._verify(action,submission,decision)
        if error:
            result=ExecutionResult(uid("exec"),action.action_id,decision.decision_id if decision else None,"EXECUTION_DENIED",error)
        else:
            self._consumed_nonces.add(decision.nonce); result=ExecutionResult(uid("exec"),action.action_id,decision.decision_id,"EXECUTION_COMPLETED","mock provider accepted governed action")
            self.provider.execute(action)
        self.store.append(actor_identity=self.identity.identity_id,actor_role=ROLES["execution"],event_type=result.status,run_id=run_id,source="execution-gateway",object_id=result.execution_id,object_type="ExecutionResult",payload=result.__dict__,metadata={"action_id":action.action_id})
        return result
    def _verify(self, action, submission, decision):
        if not decision: return "no governance decision"
        if decision.decision != GovernanceDisposition.APPROVED: return "governance decision is not approved"
        if not self.trust.verify(decision.authorization_identity,decision_bytes(decision),decision.signature,"authorization"): return "invalid authorization signature or identity"
        if datetime.fromisoformat(decision.expires_at) <= datetime.now(timezone.utc): return "governance decision expired"
        if decision.nonce in self._consumed_nonces: return "authorization nonce already consumed"
        if digest(action) != decision.action_proposal_hash or digest(action) != submission.payload_hash: return "modified or substituted action"
        if submission.proofpack_hash != decision.proofpack_hash or submission.intent_hash != decision.intent_hash or submission.intent_id != decision.action_intent_id: return "proofpack or intent binding mismatch"
        c=decision.constraints
        if action.target != c.get("target"): return "target outside authorization scope"
        for key,bounds in c.get("allowed_parameters",{}).items():
            v=action.parameters.get(key)
            if not isinstance(v,(int,float)) or not bounds["min"] <= v <= bounds["max"]: return "parameters outside authorization constraints"
        return None
