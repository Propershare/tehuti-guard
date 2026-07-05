# Tehuti Guard architecture

## Product split

Tehuti Guard is **one product** shipped as **two packages** in this monorepo:

1. **`packages/decision-api`** — constitutional brain (Python)
2. **`packages/mcp-proxy`** — transport/interception shell (Node)

MaatBench (external) supplies the covenant compiler. Guard does not embed training
logic — it imports MaatBench at runtime via `MAATBENCH_PATH`.

## v1 vs v2

| Surface | v1 | v2 |
|---------|----|----|
| `/decision` | Sentinel posture + rule catalog | unchanged |
| `/compile-decision` | — | raw model output → MaatBench compiler → enforce |
| MCP proxy | static patterns, rate limits, path gates | optional `guardApiUrl` hook |

## Flow (v2)

```text
POST /compile-decision
  body: DecisionRequest + raw_model_output
    → covenant_adapter.compile_request()
    → maatbench.covenant_compiler.compile_covenant_record()
    → rules.evaluate_compiler_with_rules()
    → DecisionResult + evidence
    → memory_sink (optional gitMaat)
```

## Fail posture

- MCP + Guard API unreachable when `guardApiUrl` set: **fail closed** (block tool call)
- Sentinel unreachable for v1 `/decision`: **review** (existing behavior)
- MaatBench missing for `/compile-decision`: **500** with explicit error

## Canonical repo

This repository (`Propershare/tehuti-guard`) is the **single source of truth**.

The lab `maat-ecosystem/tehuti-guard/` path is a **consumer stub** — not a second
product home.
