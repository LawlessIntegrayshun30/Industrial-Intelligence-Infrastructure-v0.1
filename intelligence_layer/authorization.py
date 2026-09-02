"""Separately-authenticated, deterministic authorization boundary."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Any
from .event_store import EventStore, canonical, digest, ROLES
from .identity import ServiceIdentity, TrustRegistry
from .models import GovernanceDecision, GovernanceDisposition, now, uid

@dataclass(frozen=True)
class AuthorizationRequest:
    request_id: str; run_id: str; action_intent_id: str; action_proposal_hash: str; proofpack_hash: str; intent_hash: str; scope: str; nonce: str; requester_identity: str; requester_signature: str; submitted_at: str

def request_bytes(request: AuthorizationRequest) -> bytes:
    d={k:v for k,v in request.__dict__.items() if k!="requester_signature"}; return canonical(d)
def decision_bytes(decision: GovernanceDecision) -> bytes:
    d={k:v for k,v in decision.__dict__.items() if k!="signature"}; return canonical(d)

class AuthorizationService:
    """Policy authority; it has no execution provider and only signs decisions."""
    def __init__(self, identity: ServiceIdentity, trust: TrustRegistry, store: EventStore, policy: dict[str, Any]):
        if identity.role != "authorization": raise ValueError("authorization identity required")
        self.identity,self.trust,self.store,self.policy=identity,trust,store,policy; self._seen_requests=set()
    def make_request(self, *, submission, run_id: str, requester: ServiceIdentity, nonce: str) -> AuthorizationRequest:
        draft=AuthorizationRequest(uid("authreq"),run_id,submission.intent_id,submission.payload_hash,submission.proofpack_hash,submission.intent_hash,submission.scope,nonce,requester.identity_id,"",now())
        return AuthorizationRequest(**{**draft.__dict__,"requester_signature":requester.sign(request_bytes(draft))})
    def submit_for_authorization(self, request: AuthorizationRequest, action: Any) -> GovernanceDecision:
        reason="approved"; decision=GovernanceDisposition.APPROVED
        if request.request_id in self._seen_requests or not self.trust.verify(request.requester_identity,request_bytes(request),request.requester_signature,"intelligence"):
            decision=GovernanceDisposition.INVALID; reason="unknown requester, invalid requester signature, or replayed request"
        elif digest(action) != request.action_proposal_hash:
            decision=GovernanceDisposition.INVALID; reason="action proposal hash does not bind to request"
        elif not self._policy_allows(action, request.scope):
            decision=GovernanceDisposition.DENIED; reason="action is outside deterministic policy constraints"
        self._seen_requests.add(request.request_id)
        request_audit=self.store.append(actor_identity=self.identity.identity_id,actor_role=ROLES["authorization"],event_type="AUTHORIZATION_REQUEST",run_id=request.run_id,source="authorization-service",object_id=request.request_id,object_type="AuthorizationRequest",payload=request.__dict__,metadata={"requester":request.requester_identity})
        issued=datetime.now(timezone.utc); expires=issued+timedelta(minutes=int(self.policy.get("decision_ttl_minutes",5)))
        unsigned=GovernanceDecision(uid("gov"),request.action_intent_id,request.action_proposal_hash,request.proofpack_hash,request.intent_hash,request.requester_identity,self.identity.identity_id,decision,request.scope,self.policy["constraints"],issued.isoformat(),expires.isoformat(),request.nonce,"",request_audit.event_id,schema_version="0.2")
        signed=GovernanceDecision(**{**unsigned.__dict__,"signature":self.identity.sign(decision_bytes(unsigned))})
        self.store.append(actor_identity=self.identity.identity_id,actor_role=ROLES["authorization"],event_type="GOVERNANCE_DECISION",run_id=request.run_id,source="authorization-service",object_id=signed.decision_id,object_type="GovernanceDecision",payload={"request":request.__dict__,"decision":signed.__dict__},metadata={"reason":reason})
        return signed
    def _policy_allows(self, action, scope):
        c=self.policy["constraints"]
        if scope != self.policy["scope"] or action.action_type not in self.policy["action_types"] or action.target != c.get("target"): return False
        for name,bounds in c.get("allowed_parameters",{}).items():
            value=action.parameters.get(name)
            if not isinstance(value,(int,float)) or value < bounds["min"] or value > bounds["max"]: return False
        return True
