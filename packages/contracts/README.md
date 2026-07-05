# Tehuti Guard contracts

Shared wire vocabulary for the **decision API** and **MCP proxy** adapters.

## Decision vocabulary (wire)

`allow` | `deny` | `review` | `quarantine` | `escalate`

Doctrine term **conditional** maps to **`review`** or **`quarantine`** — not a sixth wire value.

## Schemas

| File | Purpose |
|------|---------|
| `decision-envelope.schema.json` | `POST /decision` and `POST /compile-decision` request body |
| `decision-response.schema.json` | Guard decision response |

## v2 compile-decision

When `raw_model_output` or `covenant_record` is present, the decision API compiles
through MaatBench before enforcement. See `packages/decision-api/README.md`.
