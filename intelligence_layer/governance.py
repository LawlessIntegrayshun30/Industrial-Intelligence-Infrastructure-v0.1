from abc import ABC, abstractmethod
from .models import ActionProposal, GovernanceDisposition, GovernanceResult

class GovernanceGateway(ABC):
    @abstractmethod
    def evaluate(self, action: ActionProposal) -> GovernanceResult: ...

class MockGovernanceGateway(GovernanceGateway):
    def __init__(self, disposition=GovernanceDisposition.REQUIRES_AUTHORIZATION): self.disposition=GovernanceDisposition(disposition)
    def evaluate(self, action):
        if not action.requires_governance or action.status != "proposed":
            return GovernanceResult(action.action_id, GovernanceDisposition.HOLD, "Malformed or non-governed action proposal.")
        return GovernanceResult(action.action_id, self.disposition, "Mock gateway: no execution occurs in this prototype.")
