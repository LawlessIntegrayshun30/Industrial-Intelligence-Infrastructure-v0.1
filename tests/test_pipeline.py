import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory
from intelligence_layer.governance import MockGovernanceGateway
from intelligence_layer.ingestion import EventNormalizer, ValidationError
from intelligence_layer.models import GovernanceDisposition
from intelligence_layer.pipeline import IntelligencePipeline
from intelligence_layer.reasoning import ReasoningProvider
from intelligence_layer.state import StateStore
from intelligence_layer.persistence import JsonlRunRepository
from intelligence_layer.nttx_gateway import NTTXGovernanceGateway

EVENTS=json.loads((Path(__file__).parent.parent/"fixtures"/"demo_events.json").read_text())["events"]

class FailingProvider(ReasoningProvider):
    name="failing"
    def generate(self, signals): raise RuntimeError("provider unavailable")

class PipelineTests(unittest.TestCase):
    def test_malformed_event_rejected(self):
        with self.assertRaises(ValidationError): EventNormalizer().normalize({"event_id":"bad"})
    def test_state_reconstruction_is_auditable(self):
        n=EventNormalizer(); events=[n.normalize(e)[0] for e in EVENTS]
        store=StateStore(); store.apply(events[:2]); first=store.reconstruct()[0]; store.apply(events[2:]); final=store.reconstruct()[0]
        self.assertEqual(final.values["temperature_c"],84.8); self.assertEqual(final.event_ids, ["evt_001","evt_002","evt_003"]); self.assertEqual(first.event_ids[:2],["evt_001","evt_002"])
    def test_end_to_end_is_governed_and_audited(self):
        result=IntelligencePipeline().run(EVENTS)
        self.assertTrue(result["signals"]); self.assertTrue(result["hypotheses"]); self.assertTrue(result["predictions"]); self.assertTrue(result["recommendations"]); self.assertTrue(result["action_proposals"])
        self.assertEqual(result["governance"][0].disposition,GovernanceDisposition.REQUIRES_AUTHORIZATION)
        self.assertTrue(all(a.requires_governance and a.status=="proposed" for a in result["action_proposals"]))
        self.assertEqual(len(result["audit"]),8); self.assertIn("evt_003",result["decision"].provenance["events"])
    def test_confidence_propagates_downstream(self):
        r=IntelligencePipeline().run(EVENTS)
        self.assertLessEqual(r["action_proposals"][0].confidence,r["recommendations"][0].confidence)
    def test_governance_dispositions(self):
        for disposition in (GovernanceDisposition.DENY,GovernanceDisposition.HOLD,GovernanceDisposition.REQUIRES_AUTHORIZATION):
            r=IntelligencePipeline(governance=MockGovernanceGateway(disposition)).run(EVENTS)
            self.assertEqual(r["governance"][0].disposition,disposition)
    def test_provider_failure_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"failed closed"):
            IntelligencePipeline(reasoning=FailingProvider()).run(EVENTS)
    def test_deterministic_signal_result(self):
        a=IntelligencePipeline().run(EVENTS); b=IntelligencePipeline().run(EVENTS)
        self.assertEqual([s.type for s in a["signals"]],[s.type for s in b["signals"]])
    def test_run_is_durably_retrievable(self):
        with TemporaryDirectory() as directory:
            repo=JsonlRunRepository(Path(directory)/"runs.jsonl"); result=IntelligencePipeline(repository=repo).run(EVENTS)
            restored=IntelligencePipeline(repository=repo).get_run(result["run_id"])
            self.assertEqual(restored["run_id"],result["run_id"]); self.assertEqual(restored["decision"]["decision_id"],result["decision"].decision_id)
    def test_nttx_gateway_submits_without_execution(self):
        result=IntelligencePipeline(governance=NTTXGovernanceGateway()).run(EVENTS)
        self.assertEqual(result["governance"][0].disposition,GovernanceDisposition.REQUIRES_AUTHORIZATION)
        self.assertIn("no commit or execution",result["governance"][0].reason)

if __name__ == "__main__": unittest.main()
