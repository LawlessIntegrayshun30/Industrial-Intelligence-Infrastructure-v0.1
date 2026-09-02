import json
from pathlib import Path
from .models import serialise
from .pipeline import IntelligencePipeline

if __name__ == "__main__":
    events=json.loads((Path(__file__).parent.parent / "fixtures" / "demo_events.json").read_text()) ["events"]
    print(json.dumps(serialise(IntelligencePipeline().run(events)), indent=2))
