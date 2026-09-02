import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from intelligence_layer.authorization import AuthorizationService
from intelligence_layer.event_store import JsonlEventStore, ROLES
from intelligence_layer.execution import ExecutionGateway, MockExecutionProvider
from intelligence_layer.identity import ServiceIdentity, TrustRegistry
from intelligence_layer.lifecycle import DEFAULT_POLICY, build_demo_boundaries
from intelligence_layer.models import ActionProposal, GovernanceDisposition
from intelligence_layer.pipeline import IntelligencePipeline

EVENTS=json.loads((Path(__file__).parent.parent/"fixtures"/"demo_events.json").read_text())["events"]

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(); self.store=JsonlEventStore(Path(self.temp.name)/"events.jsonl")
        self.governance,self.executor=build_demo_boundaries(self.store)
        self.result=IntelligencePipeline(governance=self.governance,event_store=self.store).run(EVENTS)
        self.action=self.result["action_proposals"][0]; self.decision=self.governance.decisions[self.action.action_id]; self.submission=self.governance.submission_by_action[self.action.action_id]
    def tearDown(self): self.temp.cleanup()
    _DEFAULT=object()
    def execute(self, action=None, submission=None, decision=_DEFAULT): return self.executor.execute(run_id=self.result["run_id"],action=action or self.action,submission=submission or self.submission,decision=self.decision if decision is self._DEFAULT else decision)
    def test_complete_lifecycle_executes_mock_only(self):
        r=self.execute(); self.assertEqual(self.decision.decision,GovernanceDisposition.APPROVED); self.assertEqual(r.status,"EXECUTION_COMPLETED"); self.assertEqual(self.executor.provider.accepted,[self.action.action_id]); self.assertTrue(self.store.verify_chain()); self.assertGreaterEqual(len(self.store.get_run(self.result["run_id"])),11)
    def test_modified_action_is_blocked(self): self.assertEqual(self.execute(action=replace(self.action,parameters={"load_delta_percent":-5})).status,"EXECUTION_DENIED")
    def test_modified_proofpack_is_blocked(self): self.assertEqual(self.execute(submission=replace(self.submission,proofpack_hash="tampered")).status,"EXECUTION_DENIED")
    def test_expired_decision_is_blocked(self): self.assertEqual(self.execute(decision=replace(self.decision,expires_at=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat())).status,"EXECUTION_DENIED")
    def test_invalid_signature_is_blocked(self): self.assertEqual(self.execute(decision=replace(self.decision,signature="forged")).status,"EXECUTION_DENIED")
    def test_replay_is_blocked(self): self.assertEqual(self.execute().status,"EXECUTION_COMPLETED"); self.assertEqual(self.execute().status,"EXECUTION_DENIED")
    def test_scope_and_target_constraints_are_blocked(self):
        self.assertEqual(self.execute(action=replace(self.action,target="engine_08")).status,"EXECUTION_DENIED")
    def test_no_decision_never_executes(self): self.assertEqual(self.execute(decision=None).status,"EXECUTION_DENIED")
    def test_denied_decision_never_executes(self): self.assertEqual(self.execute(decision=replace(self.decision,decision=GovernanceDisposition.DENIED)).status,"EXECUTION_DENIED")
    def test_unknown_identity_request_is_invalid(self):
        outsider=ServiceIdentity.generate("unknown","intelligence")
        request=self.governance.authorization.make_request(submission=self.submission,run_id=self.result["run_id"],requester=outsider,nonce="unique-outsider")
        decision=self.governance.authorization.submit_for_authorization(request,self.action)
        self.assertEqual(decision.decision,GovernanceDisposition.INVALID)
    def test_auditor_cannot_modify_history(self):
        with self.assertRaises(PermissionError): self.store.append(actor_identity="auditor",actor_role=ROLES["auditor"],event_type="TAMPER",run_id="x",source="test",object_id="x",object_type="x",payload={})

if __name__=="__main__": unittest.main()
