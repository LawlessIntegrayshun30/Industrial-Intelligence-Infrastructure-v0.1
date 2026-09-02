"""Governed, non-executing intelligence prototype."""

from .pipeline import IntelligencePipeline
from .governance import MockGovernanceGateway

__all__ = ["IntelligencePipeline", "MockGovernanceGateway"]
