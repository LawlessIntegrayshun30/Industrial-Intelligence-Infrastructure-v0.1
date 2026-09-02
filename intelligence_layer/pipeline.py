from __future__ import annotations
from time import perf_counter
from .governance import GovernanceGateway, MockGovernanceGateway
from .ingestion import EventNormalizer
from .models import *
from .reasoning import DeterministicReasoningProvider, ReasoningProvider
from .signals import DeterministicSignalDetector
from .state import StateStore
from .persistence import JsonlRunRepository
from .event_store import EventStore, ROLES

class IntelligencePipeline:
    def __init__(self, store=None, reasoning: ReasoningProvider|None=None, governance: GovernanceGateway|None=None, repository: JsonlRunRepository|None=None, event_store: EventStore|None=None):
        self.store=store or StateStore(); self.normalizer=EventNormalizer(); self.reasoning=reasoning or DeterministicReasoningProvider(); self.governance=governance or MockGovernanceGateway(); self.runs={}; self.repository=repository; self.event_store=event_store
    def run(self, raw_events: list[dict]) -> dict:
        run_id=uid("run"); audit=[]
        if hasattr(self.governance, "set_run_id"): self.governance.set_run_id(run_id)
        def stage(name, inputs, operation, provider="deterministic"):
            began=perf_counter()
            try:
                value=operation(); status="success"; err=None
            except Exception as exc:
                value=[]; status="failed"; err=str(exc)
            outputs=value if isinstance(value,list) else [value]
            record=AuditRecord(uid("audit"),run_id,now(),name,inputs,[getattr(x,"event_id",getattr(x,"state_id",getattr(x,"signal_id",getattr(x,"hypothesis_id",getattr(x,"prediction_id",getattr(x,"recommendation_id",getattr(x,"action_id","unknown"))))))) for x in outputs],provider,round((perf_counter()-began)*1000,2),status,None,err)
            audit.append(record)
            if self.event_store: self.event_store.append(actor_identity="intelligence-layer",actor_role=ROLES["intelligence"],event_type="INTELLIGENCE_STAGE",run_id=run_id,source="intelligence-pipeline",object_id=record.audit_id,object_type="AuditRecord",payload=serialise(record),metadata={"stage":name})
            if status == "failed": raise RuntimeError(f"{name} failed closed: {err}")
            return value
        normalized=stage("normalize", [e.get("event_id","unknown") for e in raw_events], lambda:[self.normalizer.normalize(e) for e in raw_events])
        events=[x[0] for x in normalized]; observations=[o for _,os in normalized for o in os]
        states=stage("update_state", [e.event_id for e in events], lambda:self.store.apply(events))
        signals=stage("detect_signals", [s.state_id for s in states], lambda:DeterministicSignalDetector().detect(states, events))
        hypotheses=stage("generate_hypotheses", [s.signal_id for s in signals], lambda:self.reasoning.generate(signals), self.reasoning.name)
        predictions=stage("generate_predictions", [h.hypothesis_id for h in hypotheses], lambda:[Prediction(uid("pred"),h.timestamp,h.entity_id,"If the trend continues, temperature may exceed the configured operating envelope within approximately 10 minutes.",10,round(h.confidence*.95,2),[h.hypothesis_id]) for h in hypotheses])
        recommendations=stage("generate_recommendations", [p.prediction_id for p in predictions], lambda:[Recommendation(uid("rec"),p.timestamp,p.entity_id,"Reduce operating load and initiate diagnostic inspection.",round(p.confidence*.95,2),[p.prediction_id]) for p in predictions])
        actions=stage("generate_action_proposals", [r.recommendation_id for r in recommendations], lambda:[ActionProposal(uid("act"),r.timestamp,"adjust_operating_parameter",r.entity_id,{"load_delta_percent":-10},"Reduce projected operating risk.",round(r.confidence*.95,2)) for r in recommendations])
        governance=stage("governance_handoff", [a.action_id for a in actions], lambda:[self.governance.evaluate(a) for a in actions], "governance-gateway")
        provenance={"events":[e.event_id for e in events],"observations":[o.observation_id for o in observations],"states":[s.state_id for s in states],"signals":[s.signal_id for s in signals],"hypotheses":[h.hypothesis_id for h in hypotheses],"predictions":[p.prediction_id for p in predictions],"recommendations":[r.recommendation_id for r in recommendations],"actions":[a.action_id for a in actions],"audit":[a.audit_id for a in audit]}
        confidence=min((a.confidence for a in actions), default=min((s.confidence for s in states),default=0))
        decision=Decision(uid("decision"),run_id,now(),[s.entity_id for s in states],[s.state_id for s in states],provenance["signals"],provenance["hypotheses"],provenance["predictions"],provenance["recommendations"],provenance["actions"],confidence,provenance)
        result={"run_id":run_id,"decision":decision,"events":events,"observations":observations,"states":states,"signals":signals,"hypotheses":hypotheses,"predictions":predictions,"recommendations":recommendations,"action_proposals":actions,"governance":governance,"audit":audit}
        self.runs[run_id]=result
        if self.repository: self.repository.append(result)
        return result
    def get_run(self, run_id: str):
        return self.runs.get(run_id) or (self.repository.get(run_id) if self.repository else None)
