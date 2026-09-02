# Architecture

```
Inputs -> Intelligence -> NTTX AUTHORIZE_ACTION -> Authorization Service -> Signed GovernanceDecision -> ExecutionGateway -> Mock Provider
   |                                                                                  |                       |                    |
   +---------------------------------------------- append-only hash-linked EventStore <---------------------+--------------------+
```

The Intelligence Layer owns normalization, state reconstruction, deterministic signals, hypotheses, predictions, recommendations, and `ActionProposal` creation. It has no execution interface.

`GovernanceGateway.evaluate()` is the sole handoff point. It returns `ALLOW`, `DENY`, `HOLD`, or `REQUIRES_AUTHORIZATION`; none of those results invokes a device or external system. A future Nanocode/Cham-Code adapter belongs behind this interface, not in the intelligence pipeline.

The current NTTX adapter uses only NTTX sealing and intent creation. NTTX `prepare_transfer` and `commit_transfer` are explicitly excluded from the intelligence process; they remain for a separately authenticated authorization/execution runtime.

v0.2 uses three distinct Ed25519 identities: `intelligence-layer`, `authorization-service`, and `execution-service`. The authorization service verifies the intelligence request signature, applies deterministic policy, and signs a decision bound to canonical hashes of the exact ActionProposal, NTTX intent, and ProofPack. The execution gateway independently verifies this signature, expiration, hash bindings, policy constraints, and one-time nonce before calling the mock provider.

Every stage records an `AuditRecord` with correlation/run ID, inputs, outputs, provider, status, latency, and confidence. `Decision.provenance` references the event, signal, hypothesis, prediction, recommendation, action, state snapshot, governance, and audit records used to create it.
