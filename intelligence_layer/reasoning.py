from abc import ABC, abstractmethod
from .models import Hypothesis, Signal, uid

class ReasoningProvider(ABC):
    name="abstract"
    @abstractmethod
    def generate(self, signals: list[Signal]) -> list[Hypothesis]: ...

class DeterministicReasoningProvider(ReasoningProvider):
    name="deterministic-rules-v0.1"
    def generate(self, signals):
        groups={}
        for s in signals: groups.setdefault(s.entity_id,[]).append(s)
        out=[]
        for entity, group in groups.items():
            kinds={s.type for s in group}; confidence=min(s.confidence for s in group)
            statement = "Potential restriction or abnormal operating condition." if {"rate_anomaly","vibration_threshold"} & kinds else "Potential operating envelope excursion."
            out.append(Hypothesis(uid("hyp"),group[0].timestamp,entity,statement,confidence,[s.signal_id for s in group],self.name))
        return out
