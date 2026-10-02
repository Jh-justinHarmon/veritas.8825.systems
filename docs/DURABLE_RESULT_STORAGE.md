# Durable Result Storage

Packet `wpk_fa189292ad894c1e`, node `durable_result_storage`.

## What changed

Synthesis history moved from a per-machine ephemeral JSON file
(`history/synthesis_history.json`) to a SQLite database
(`SqliteHistoryStore`, `backend/history/sqlite_store.py`) hosted on a
Fly volume mounted at `/data` (`veritas_data`, configured in
`fly.toml`).

Results now survive process restarts, machine replacement, and
redeploys. `history.db` is the durable artifact; WAL journaling gives
atomic writes and crash safety.

## Store semantics

- Exact-ID access only. `get_history_by_id` performs an exact key
  lookup — unknown, foreign, or malformed identifiers return `None`
  indistinguishably. No enumeration surface is added.
- Each row persists: `id` (upstream session/result id), `created_at`,
  `question`, `answer_json`, `trace_json` (includes the corpus binding),
  `owner_subject` (nullable; caller-identity binding remains
  gateway-side), `receipt_ref` (nullable), `retention_state`.
- Storage outage fails closed: `HistoryStoreError` → sanitized
  `HISTORY_UNAVAILABLE` (503) at every history touchpoint and at
  synthesize persistence. No silent ephemeral fallback when a durable
  backend was requested.
- Backend selection: `VERITAS_HISTORY_BACKEND=auto|sqlite|json`.
  `auto` uses SQLite when `/data` exists or `VERITAS_HISTORY_DB` is set,
  otherwise the legacy JSON file (local dev only). `sqlite` forces
  durable mode and fails closed if it cannot initialize.
- Retention: `VERITAS_HISTORY_RETENTION_DAYS` (default `0` = retain
  forever). Expired entries are excluded from reads; `DELETE
  /api/history/<id>` always removes permanently.

## Deploy requirement

Provisioning the volume is a deploy-time action (gated by
`publish_and_deploy_hardening`):

```
fly volumes create veritas_data --region dfw --size 1 -a veritas-8825-systems
```

Single-volume model pins the app to one machine in `dfw`. Multi-region
scale-out of the store is out of scope.

## Failure and backup model

- Failure: volume loss destroys result history (ownership receipts in
  the gateway artifact store are unaffected). Degradation is confined
  to result readback; synthesis still requires a working store.
- Backup: `fly volumes snapshots list` / `fly volumes snapshot` —
  periodic snapshot of `veritas_data`. DB is also plain SQLite: a
  consistent dump is `sqlite3 /data/history.db .dump`.

## Migration

On first boot with an empty DB, `SqliteHistoryStore` imports the legacy
`history/synthesis_history.json` (one-time, `INSERT OR IGNORE`).
Production data migration beyond this bootstrap requires a separate
human gate per packet constraints.

## Rollback

1. Redeploy the previous image (history resumes from the last JSON
   state — data written to SQLite meanwhile is not back-propagated;
   reconcile by exporting `history.db` and replaying into JSON if
   needed).
2. Or set `VERITAS_HISTORY_BACKEND=json` to force the legacy backend
   without redeploying storage code (data since cutover remains in
   SQLite until migrated back).
