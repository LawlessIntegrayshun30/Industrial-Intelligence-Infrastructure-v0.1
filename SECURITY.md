# Security model (v0.2)

The Intelligence Layer can create only proposals and NTTX submission intents. It has no execution provider, no capability token, and no NTTX prepare/commit invocation path.

Each service has an explicit Ed25519 identity registered in a trust registry. Authorization requests are signed by the intelligence identity; governance decisions are signed by the authorization identity. A decision covers its action-proposal hash, NTTX intent hash, ProofPack hash, requester, scope, constraints, issue/expiry time, nonce, and audit reference.

The execution gateway rejects missing, denied, expired, forged, replayed, substituted, target-mismatched, parameter-out-of-bounds, and proofpack/intent-mismatched decisions. It only invokes `MockExecutionProvider`; this milestone includes no physical or system execution adapter.

Event-store roles are application-enforced: Intelligence Writer, Authorization Writer, Execution Writer, and read-only Auditor. The JSONL adapter is append-only by application contract and hash-links records for tamper evidence; it is not a replacement for database ACLs or immutable storage.
