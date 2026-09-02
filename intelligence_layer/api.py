import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from .models import serialise
from .pipeline import IntelligencePipeline
from .persistence import JsonlRunRepository
from .event_store import JsonlEventStore
from .lifecycle import build_demo_boundaries

event_store=JsonlEventStore("data/audit_events.jsonl")
governance,execution=build_demo_boundaries(event_store)
pipeline=IntelligencePipeline(repository=JsonlRunRepository("data/intelligence_runs.jsonl"),governance=governance,event_store=event_store)
class Handler(BaseHTTPRequestHandler):
    def _respond(self, code, body):
        raw=json.dumps(serialise(body)).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_POST(self):
        try:
            data=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            if self.path == "/intelligence/run":
                if not isinstance(data.get("events"),list): raise ValueError("events must be a list")
                self._respond(200,pipeline.run(data["events"]))
            elif self.path == "/execution/execute":
                run=pipeline.get_run(data["run_id"]); action_id=data["action_id"]
                if not run: raise ValueError("unknown run")
                actions=run["action_proposals"] if isinstance(run["action_proposals"][0],dict) else run["action_proposals"]
                action=next((a for a in actions if (a["action_id"] if isinstance(a,dict) else a.action_id)==action_id),None)
                if not action or isinstance(action,dict): raise ValueError("execution only supports an in-memory run with typed action")
                self._respond(200,execution.execute(run_id=data["run_id"],action=action,submission=governance.submission_by_action[action_id],decision=governance.decisions.get(action_id)))
            else: self._respond(404,{"error":"not found"})
        except Exception as e: self._respond(400,{"error":str(e),"status":"HOLD"})
    def do_GET(self):
        prefix="/intelligence/runs/"
        if self.path.startswith(prefix):
            result=pipeline.get_run(self.path[len(prefix):])
            return self._respond(200,result) if result else self._respond(404,{"error":"run not found"})
        if self.path.startswith("/authorization/decisions/"):
            decision_id=self.path.rsplit("/",1)[-1]; decision=next((d for d in governance.decisions.values() if d.decision_id==decision_id),None)
            return self._respond(200,decision) if decision else self._respond(404,{"error":"decision not found"})
        if self.path.startswith("/runs/"):
            return self._respond(200,event_store.get_run(self.path.rsplit("/",1)[-1]))
        if self.path.startswith("/provenance/"):
            return self._respond(200,event_store.get_provenance(self.path.rsplit("/",1)[-1]))
        self._respond(404,{"error":"not found"})
if __name__ == "__main__":
    print("Intelligence API listening on http://127.0.0.1:8080")
    HTTPServer(("127.0.0.1",8080),Handler).serve_forever()
