"""Adapter from an ActionProposal to the NTTX clone's authorization submission contract."""
from __future__ import annotations
import sys
from pathlib import Path
from .governance import GovernanceGateway
from .models import ActionProposal, GovernanceDisposition, GovernanceResult

DEFAULT_NTTX_CLONE = Path(r"Z:\Brant Development\Nanocode\NTTX-Intelligence-Layer-Integration-v0.1")

class NTTXGovernanceGateway(GovernanceGateway):
    def __init__(self, nttx_root: str | Path = DEFAULT_NTTX_CLONE):
        root=Path(nttx_root)
        if not (root / "integration" / "action_intent.py").exists(): raise RuntimeError("NTTX integration clone is unavailable")
        if str(root) not in sys.path: sys.path.insert(0, str(root))
        from integration.action_intent import NTTXActionSubmissionGateway
        self._gateway=NTTXActionSubmissionGateway()
    def evaluate(self, action: ActionProposal) -> GovernanceResult:
        try:
            submitted=self.submit(action)
            return GovernanceResult(action.action_id, GovernanceDisposition.REQUIRES_AUTHORIZATION, f"Submitted to NTTX intent {submitted.intent_id}; sealed request {submitted.sealed_object_id}; no commit or execution occurred.")
        except Exception as exc:
            return GovernanceResult(action.action_id, GovernanceDisposition.HOLD, f"NTTX submission failed closed: {exc}")
    def submit(self, action: ActionProposal):
        """Submission only; this method cannot prepare, commit, or execute."""
        return self._gateway.submit(action)
