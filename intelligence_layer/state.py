from collections import defaultdict
from .models import Entity, Event, State, uid

class StateStore:
    def __init__(self): self.events: list[Event] = []; self.states: dict[str, State] = {}
    def apply(self, events: list[Event]) -> list[State]:
        self.events.extend(events)
        return self.reconstruct()
    def reconstruct(self) -> list[State]:
        grouped = defaultdict(list)
        for event in sorted(self.events, key=lambda e: e.timestamp): grouped[event.entity_id].append(event)
        states=[]
        for entity_id, history in grouped.items():
            values={}; confidence=[]
            for event in history:
                values.update({k: float(v) for k,v in event.payload.items() if isinstance(v,(int,float)) and k != "rate_of_change"})
                confidence.append(event.source.reliability)
            state=State(uid("state"), entity_id, history[-1].timestamp, values, [e.event_id for e in history], round(sum(confidence)/len(confidence), 2))
            self.states[entity_id]=state; states.append(state)
        return states
    def entities(self) -> list[Entity]: return [Entity(e) for e in self.states]
