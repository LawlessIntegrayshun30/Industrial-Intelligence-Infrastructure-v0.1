"""Wires the v0.2 demo boundaries without granting intelligence execution access."""
from __future__ import annotations
from dataclasses import replace
from .authorization import AuthorizationService
from .event_store import EventStore
from .execution import ExecutionGateway, MockExecutionProvider
from .identity import ServiceIdentity, TrustRegistry
from .models import GovernanceDisposition, GovernanceResult
from .nttx_gateway import NTTXGovernanceGateway

DEFAULT_POLICY={"scope":"industrial-intelligence","action_types":["adjust_operating_parameter"],"decision_ttl_minutes":5,"constraints":{"target":"engine_07","allowed_parameters":{"load_delta_percent":{"min":-10,"max":0}},"max_execution_count":1}}
class AuthenticatedNTTXGovernanceGateway:
    """Intelligence submits; authorization signs; this gateway never executes."""
    def __init__(self, authorization: AuthorizationService, requester: ServiceIdentity, submissions: NTTXGovernanceGateway): self.authorization,self.requester,self.submissions=authorization,requester,submissions; self.decisions={}; self.submission_by_action={}; self.run_id="unbound"
    def set_run_id(self, run_id): self.run_id=run_id
    def evaluate(self, action):
        try:
            submission=self.submissions.submit(action)
            request=self.authorization.make_request(submission=submission,run_id=self.run_id,requester=self.requester,nonce=f"nonce_{action.action_id}")
            decision=self.authorization.submit_for_authorization(request,action)
            self.decisions[action.action_id]=decision; self.submission_by_action[action.action_id]=submission
            return GovernanceResult(action.action_id,decision.decision,"authorization service evaluated sealed NTTX action intent",decision_id=decision.decision_id,action_intent_id=submission.intent_id)
        except Exception as exc: return GovernanceResult(action.action_id,GovernanceDisposition.HOLD,f"governance service unavailable or rejected request: {exc}")

def build_demo_boundaries(store: EventStore):
    trust=TrustRegistry(); intelligence=ServiceIdentity.generate("intelligence-layer","intelligence"); authorization=ServiceIdentity.generate("authorization-service","authorization"); execution=ServiceIdentity.generate("execution-service","execution")
    for identity in (intelligence,authorization,execution): trust.register(identity)
    service=AuthorizationService(authorization,trust,store,DEFAULT_POLICY); governed=AuthenticatedNTTXGovernanceGateway(service,intelligence,NTTXGovernanceGateway()); executor=ExecutionGateway(execution,trust,store,MockExecutionProvider())
    return governed,executor
