"""Explicit service identities backed by Ed25519 signing keys."""
from __future__ import annotations
import base64
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

@dataclass
class ServiceIdentity:
    identity_id: str
    role: str
    _private: Ed25519PrivateKey
    @classmethod
    def generate(cls, identity_id: str, role: str): return cls(identity_id, role, Ed25519PrivateKey.generate())
    @property
    def public_key(self) -> str: return base64.b64encode(self._private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()
    def sign(self, message: bytes) -> str: return base64.b64encode(self._private.sign(message)).decode()

class TrustRegistry:
    def __init__(self): self._identities: dict[str, tuple[str, str]] = {}
    def register(self, identity: ServiceIdentity) -> None: self._identities[identity.identity_id]=(identity.role, identity.public_key)
    def verify(self, identity_id: str, message: bytes, signature: str, expected_role: str | None = None) -> bool:
        record=self._identities.get(identity_id)
        if not record or (expected_role and record[0] != expected_role): return False
        try:
            Ed25519PublicKey.from_public_bytes(base64.b64decode(record[1])).verify(base64.b64decode(signature), message); return True
        except Exception: return False
