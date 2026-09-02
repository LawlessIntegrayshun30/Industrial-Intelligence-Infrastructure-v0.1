"""Append-only audit store interface and local JSONL implementation.

JSONL is retained for development. PostgreSQLEventStore exposes the same contract for
deployment once a provisioned PostgreSQL service and psycopg are supplied.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import hashlib, json
from pathlib import Path
from threading import Lock
from typing import Any
from .models import AuditEvent, now, serialise, uid

ROLES={"intelligence":"INTELLIGENCE_WRITER", "authorization":"AUTHORIZATION_WRITER", "execution":"EXECUTION_WRITER", "auditor":"AUDITOR"}
def canonical(value: Any) -> bytes: return json.dumps(serialise(value), sort_keys=True, separators=(",", ":")).encode()
def digest(value: Any) -> str: return hashlib.sha256(canonical(value)).hexdigest()

class EventStore(ABC):
    @abstractmethod
    def append(self, *, actor_identity: str, actor_role: str, event_type: str, run_id: str, source: str, object_id: str, object_type: str, payload: dict, metadata: dict | None=None) -> AuditEvent: ...
    @abstractmethod
    def get(self, event_id: str) -> dict | None: ...
    @abstractmethod
    def query(self, *, run_id: str | None=None, object_id: str | None=None) -> list[dict]: ...
    def get_run(self, run_id: str) -> list[dict]: return self.query(run_id=run_id)
    def get_provenance(self, object_id: str) -> list[dict]: return self.query(object_id=object_id)

class JsonlEventStore(EventStore):
    def __init__(self, path: str|Path): self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True); self._lock=Lock()
    def _all(self):
        if not self.path.exists(): return []
        with self.path.open(encoding="utf-8") as f: return [json.loads(line) for line in f if line.strip()]
    def append(self, *, actor_identity, actor_role, event_type, run_id, source, object_id, object_type, payload, metadata=None):
        if actor_role not in ROLES.values() or actor_role == ROLES["auditor"]: raise PermissionError("actor role cannot append audit events")
        with self._lock:
            previous=self._all()[-1]["event_hash"] if self._all() else "GENESIS"
            event=AuditEvent(uid("evtlog"),event_type,now(),run_id,actor_identity,source,object_id,object_type,payload,digest(payload),previous,metadata or {})
            record=serialise(event); record["event_hash"]=digest(record)
            with self.path.open("a",encoding="utf-8") as f: f.write(json.dumps(record,sort_keys=True)+"\n"); f.flush()
            return event
    def get(self,event_id): return next((x for x in self._all() if x["event_id"]==event_id),None)
    def query(self,*,run_id=None,object_id=None): return [x for x in self._all() if (run_id is None or x["run_id"]==run_id) and (object_id is None or x["object_id"]==object_id)]
    def verify_chain(self):
        prev="GENESIS"
        for record in self._all():
            item={k:v for k,v in record.items() if k!="event_hash"}
            if record["previous_event_hash"]!=prev or record["event_hash"]!=digest(item): return False
            prev=record["event_hash"]
        return True

class PostgreSQLEventStore(EventStore):
    """Deployment adapter. Requires injected DB-API-compatible connection factory."""
    def __init__(self, connection_factory): self.connection_factory=connection_factory
    def append(self, **kwargs): raise NotImplementedError("Provision PostgreSQL schema/connection before enabling this adapter")
    def get(self,event_id): raise NotImplementedError
    def query(self,**kwargs): raise NotImplementedError
