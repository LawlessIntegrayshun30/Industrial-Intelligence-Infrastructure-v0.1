from .models import Event, Observation, Source

class ValidationError(ValueError): pass

class EventNormalizer:
    REQUIRED = {"event_id", "source", "timestamp", "entity_id", "event_type", "payload"}
    def normalize(self, raw: dict) -> tuple[Event, list[Observation]]:
        missing = self.REQUIRED - raw.keys()
        if missing: raise ValidationError(f"missing required fields: {sorted(missing)}")
        if not isinstance(raw["payload"], dict): raise ValidationError("payload must be an object")
        source_name = raw["source"] if isinstance(raw["source"], str) else raw["source"].get("name")
        if not source_name: raise ValidationError("source must identify a name")
        source = Source(source_id=f"src_{source_name}", name=source_name, reliability=float(raw.get("source_reliability", .9)))
        observations = []
        for metric, value in raw["payload"].items():
            if isinstance(value, (int, float)) and metric not in {"rate_of_change"}:
                observations.append(Observation(f"obs_{raw['event_id']}_{metric}", raw["timestamp"], source.source_id, raw["entity_id"], metric, float(value), self._unit(metric), source.reliability))
        if not observations: raise ValidationError("payload must contain at least one numeric observation")
        event = Event(raw["event_id"], raw["timestamp"], source, raw["entity_id"], raw["event_type"], raw["payload"], [o.observation_id for o in observations])
        return event, observations
    @staticmethod
    def _unit(metric: str) -> str:
        return {"temperature_c": "C", "pressure_bar": "bar", "vibration_mm_s": "mm/s"}.get(metric, "unit")
