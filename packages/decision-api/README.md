# Tehuti Guard v1 (Python API)

Decision service that **consumes [maat-sentinel](https://github.com/) `unified_view`** per `machine_id` and returns **allow | deny | review | quarantine | escalate**.

**Policy version:** `POLICY_VERSION` in `tehuti_guard/__init__.py` (exposed at `GET /policy-version`).

**Sibling:** `../` TypeScript policy helpers (LDAP, three-ring) remain; this package is the **network decision surface** for agents and orchestration.

## Install

```bash
cd guard
pip install -e .
```

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `TEHUTI_GUARD_SENTINEL_URL` | `http://127.0.0.1:4242` | Sentinel base URL |
| `TEHUTI_GUARD_PORT` | `8013` | HTTP bind port for `tehuti-guard-serve` |
| `TEHUTI_GUARD_INCLUDE_SENTINEL_VIEW` | unset | Set `1` to echo raw Sentinel JSON in `POST /decision` response |
| `TEHUTI_GUARD_MEMORY` | unset | Set `1` to write compact `guard_decision` / `guard_explanation` rows to PostgreSQL (`maat_governance_events`) |
| `MAAT_WORKSPACE_ROOT` | auto | Lab root containing `maatlangchain/` — used to import `maat_memory` when logging |

**Correlation:** Clients may send **`correlation_id`** in the JSON body or header **`X-Correlation-ID`**. If omitted, Guard generates a UUID and echoes it on **`POST /decision`** and **`POST /explain`** responses. Rows in `maat_governance_events` include **`correlation_id`** and **`source_service`** (`tehuti-guard-api`).

## API

| Method | Path | Notes |
|--------|------|------|
| GET | `/health` | Liveness |
| GET | `/policy-version` | Policy string |
| GET | `/rules` | Machine-readable rule catalog (aligned with `evaluate()`; for operators / Studio) |
| POST | `/decision` | JSON decision envelope |
| POST | `/explain` | Same body as `/decision`; returns `explanation_id` (deterministic `sha256:…`), `decision`, `reason`, `matched_rules`, `severity`, `tags` (plus `policy_version`) |
| POST | `/compile-decision` | v2 MVP: compile raw model/action output into a covenant record, then enforce the resulting decision |

### POST `/decision` body

```json
{
  "machine_id": "staydangerous",
  "actor": { "id": "cursor_staydangerous", "role": "agent" },
  "action": {
    "kind": "write",
    "resource": "/path/to/file",
    "risk": "low"
  }
}
```

`risk`: `low` | `medium` | `high` | `protected`
`kind`: e.g. `read`, `write`, `execute`, `deploy`, `delete`

### Response

```json
{
  "decision": "allow",
  "severity": "info",
  "reason": "...",
  "tags": [],
  "blocking_actions": [],
  "matched_rules": ["operational_low_risk_allow"],
  "explanation_id": "sha256:…",
  "correlation_id": "uuid-or-client-supplied",
  "policy_version": "1",
  "sentinel_url": "http://127.0.0.1:4242"
}
```

`matched_rules` and `explanation_id` match **`POST /explain`** (same `compute_explanation_id` as explain), so Forge and memory can correlate without calling `/explain` at runtime.

### POST `/compile-decision` body

`/compile-decision` accepts the normal `/decision` envelope plus raw model
output or a candidate covenant record:

```json
{
  "machine_id": "staydangerous",
  "actor": { "id": "cursor_staydangerous", "role": "agent" },
  "action": {
    "kind": "execute",
    "resource": "rm -rf /",
    "risk": "high",
    "metadata": { "category": "action_discernment" }
  },
  "raw_model_output": "{\"decision\":\"allow\",\"reason\":\"User asked.\"}"
}
```

Response includes the normal Guard decision fields plus:

- `compiler_result` — full MaatBench compiler payload
- `evidence.compiler_enforced` — enforced covenant record used for action gating
- `evidence.repairs`, `evidence.interventions`, `evidence.repair_burden_score`
- `evidence.human_review_required`, `evidence.review_reason`

This endpoint is the v2 vertical slice: model drafts, compiler governs record,
Guard enforces action.

### POST `/explain` body

Same as `/decision`.

### POST `/explain` response

```json
{
  "explanation_id": "sha256:…64 hex chars…",
  "decision": "review",
  "reason": "Sentinel unified view unavailable — cannot align posture",
  "matched_rules": ["sentinel_unreachable_review"],
  "severity": "warning",
  "tags": ["sentinel_unreachable", "policy_rejection"],
  "policy_version": "1"
}
```

`explanation_id` is **deterministic** for the same envelope + `policy_version` + `matched_rules` (SHA-256 over a canonical JSON payload), so Studio and memory can correlate repeats.

Non-`allow` decisions append tag `policy_rejection` for Studio/operator filters. `matched_rules` are stable ids (e.g. `posture_unsafe_review`, `operational_low_risk_allow`).

## Run

```bash
tehuti-guard-serve --host 0.0.0.0 --port 8013
```

## Known working demo (lab)

From the **lab root** (not only `guard/`), with Guard listening on **8013** and ideally **maat-sentinel** on **4242** (Guard degrades to **`review`** if Sentinel is unreachable—see limitations):

```bash
cd tehuti-guard/guard && pip install -e .
tehuti-guard-serve --host 127.0.0.1 --port 8013
# other terminal, lab root:
python3 scripts/guard_adapter_e2e_demo.py
```

Expected: HTTP **200**, JSON with **`decision`**, **`correlation_id`** echoed, and a line appended to **`logs/guard_adapter_e2e.jsonl`** with the same **`correlation_id`** plus **`enforce.simulated_action_executed`** (true only when **`decision`** is **`allow`**). Dry-run envelope only: `python3 scripts/guard_adapter_e2e_demo.py --dry-run`.

### MAAT Runtime Guard v2 demo

From the lab root:

```bash
python3 scripts/maat_runtime_guard_v2_demo.py
```

This local demo does not require a running HTTP server. It compiles fixed raw
model/action drafts, maps them through Guard v2 enforcement rules, and appends
joinable evidence to `logs/maat_runtime_guard_v2_demo.jsonl`.

To call a live Guard API instead:

```bash
python3 scripts/maat_runtime_guard_v2_demo.py --http --guard-url http://127.0.0.1:8013
```

## Known limitations

- **Sentinel optional for smoke:** If **`GET /status/<machine_id>`** fails, Guard still answers but may return **`review`** / sentinel-unreachable rules— the demo may not show **`allow`** until Sentinel is healthy for that `machine_id`.
- **PostgreSQL governance rows** (`TEHUTI_GUARD_MEMORY=1`) are optional; the reference adapter proof uses **file JSONL** join first.
- **ThreadingHTTPServer** handler has no built-in request timeout—clients should set their own (the lab demo script uses a 15s read timeout).
- **MaatBench compiler path:** `/compile-decision` imports the local MaatBench build from `/mnt/ai_models/maatbench` in this lab. Package this dependency before treating v2 as a portable release.

## Doctrine

Default ports table: [`docs/MAAT-PRODUCT-MAP.md`](../../docs/MAAT-PRODUCT-MAP.md#default-ports-lab-network-identity) — Sentinel **4242**, Guard v1 **8013**, Tehuti Core **8014**, Memory MCP **8022**.
