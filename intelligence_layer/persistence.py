"""Small append-only JSONL repository for prototype event/audit durability."""
from __future__ import annotations
import json
from pathlib import Path
from threading import Lock
from .models import serialise

class JsonlRunRepository:
    def __init__(self, path: str | Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True); self._lock=Lock()
    def append(self, result: dict) -> None:
        entry=json.dumps(serialise(result), sort_keys=True, separators=(",", ":"))
        with self._lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(entry + "\n"); stream.flush()
    def get(self, run_id: str) -> dict | None:
        if not self.path.exists(): return None
        with self._lock, self.path.open(encoding="utf-8") as stream:
            for line in reversed(stream.readlines()):
                entry=json.loads(line)
                if entry["run_id"] == run_id: return entry
        return None
