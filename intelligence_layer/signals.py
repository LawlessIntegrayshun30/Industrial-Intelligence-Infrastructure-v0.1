from .models import Event, Signal, State, uid

class DeterministicSignalDetector:
    def detect(self, states: list[State], events: list[Event]) -> list[Signal]:
        result=[]
        by_entity={s.entity_id:s for s in states}
        for entity, state in by_entity.items():
            evidence=state.event_ids
            temp=state.values.get("temperature_c"); vib=state.values.get("vibration_mm_s")
            rate=max((float(e.payload.get("rate_of_change",0)) for e in events if e.entity_id==entity), default=0)
            if temp is not None and rate > 2:
                result.append(Signal(uid("sig"),state.timestamp,entity,"rate_anomaly","high",min(.95, round(state.confidence*.98,2)),evidence,f"Temperature increased at {rate} C/min, exceeding the configured 2.0 C/min threshold."))
            if vib is not None and vib > 2.0:
                result.append(Signal(uid("sig"),state.timestamp,entity,"vibration_threshold","high",round(state.confidence*.95,2),evidence,f"Vibration is {vib} mm/s, exceeding the configured 2.0 mm/s threshold."))
            if temp is not None and temp > 80:
                result.append(Signal(uid("sig"),state.timestamp,entity,"temperature_threshold","high",round(state.confidence*.95,2),evidence,f"Temperature is {temp} C, exceeding the configured 80 C threshold."))
        return result
