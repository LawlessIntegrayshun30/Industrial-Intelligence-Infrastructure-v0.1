# Audit and persistence

`EventStore` is the application-facing contract. `JsonlEventStore` is the verified local adapter and stores append-only records with a payload hash and previous-event hash. Hash chaining provides ordered tamper evidence; it is not blockchain consensus.

The PostgreSQL adapter is intentionally a deployment seam until a provisioned database and driver are supplied. It must use append-only tables and database roles mirroring the application roles before being enabled. JSONL remains useful for local development, deterministic tests, and recovery export.

Query a lifecycle by `run_id` (`get_run`) or an object identifier (`get_provenance`). A run links intelligence-stage records, NTTX authorization submission, signed governance decision, execution result, and outcome-equivalent mock execution status.
