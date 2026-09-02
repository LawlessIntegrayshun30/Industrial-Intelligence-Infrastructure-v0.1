# Intelligence Layer Prototype v0.1

A local, deterministic prototype that turns industrial observations into a governed `Decision`. It deliberately **does not execute actions**. Action proposals always cross the `GovernanceGateway` boundary and return a disposition.

## Architecture assessment

This repository was empty at implementation time: no API contracts, Nanocode interface, schemas, persistence layer, or tests were present. The prototype therefore uses the Python standard library and defines a narrow `GovernanceGateway` adapter intended to be replaced by Nanocode/Cham-Code integration.

## Run

```powershell
python -m intelligence_layer.demo
python -m unittest discover -s tests -v
python -m intelligence_layer.api
```

The API listens on `http://127.0.0.1:8080`.

```powershell
Invoke-RestMethod http://127.0.0.1:8080/intelligence/run -Method Post -ContentType application/json -InFile fixtures/demo_events.json
```

Retrieve a run with `GET /intelligence/runs/{run_id}`. The run response is a complete example output: events, current state, signals, hypotheses, predictions, recommendations, action proposals, governance disposition, provenance, and audit records.

## Confidence limitations

Confidence is a deterministic evidence-quality heuristic, not a probability or guarantee. It combines source reliability and rule coverage; downstream objects cannot exceed their supporting signal confidence. A production version should calibrate it against recorded outcomes.

## NTTX authorization integration

The untouched source remains at `Z:\Brant Development\Nanocode\NTTX`. The working integration clone is `Z:\Brant Development\Nanocode\NTTX-Intelligence-Layer-Integration-v0.1`.

`NTTXGovernanceGateway` seals a canonical typed ActionProposal and creates an NTTX `AUTHORIZE_ACTION` intent. It never prepares or commits the transfer, cannot obtain release material, and always reports `REQUIRES_AUTHORIZATION` after successful submission. Use it by constructing the pipeline with `governance=NTTXGovernanceGateway()`.

The API now writes append-only JSONL run records to `data/intelligence_runs.jsonl` and can retrieve them after a process restart.

## v0.2 authenticated governance

Run `python -m unittest discover -s tests -v` for the complete deterministic lifecycle, including approval, mock-only execution, action/ProofPack modification, invalid signatures, expiration, replay, unknown identity, and append-only audit checks. Read [SECURITY.md](SECURITY.md) and [AUDIT.md](AUDIT.md) for boundaries and persistence migration details.

## Known limitations and next milestone

State and audit history are in-memory; rule thresholds are static; the governance gateway is a mock. Next, integrate the gateway adapter with the actual Nanocode authorization contract and use durable append-only event storage with outcome feedback/calibration.
