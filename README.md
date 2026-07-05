# Tehuti Guard — standalone monorepo

**One product. Two packages. One constitutional doctrine.**

Tehuti Guard is the enforcement runtime for governed AI actions. MaatBench defines
the covenant record law; the **decision API** compiles and enforces it; the **MCP
proxy** intercepts tool calls and optionally delegates to the API.

```
Model / agent proposes action
        ↓
MCP proxy intercepts (packages/mcp-proxy)     [optional HTTP]
        ↓
Decision API compile + enforce (packages/decision-api)
        ↓
allow | review | deny → evidence preserved
```

## Packages

| Package | Path | Role |
|---------|------|------|
| **mcp-proxy** | `packages/mcp-proxy/` | npm MCP security wrapper; optional `guardApiUrl` → `/compile-decision` |
| **decision-api** | `packages/decision-api/` | Python HTTP API on `:8013` — v1 `/decision` + v2 `/compile-decision` |
| **contracts** | `packages/contracts/` | Shared JSON schemas and wire vocabulary |

## Quick start

### Decision API (Python)

```bash
cd packages/decision-api
pip install -e .
export MAATBENCH_PATH=/mnt/ai_models/maatbench   # required for /compile-decision
tehuti-guard-serve --host 127.0.0.1 --port 8013
```

### MCP proxy (Node)

```bash
pnpm install
pnpm build
tehuti-guard --server "node your-mcp-server.js" --config examples/guard-v2-config.json
```

### v2 demo (no HTTP server required)

```bash
export MAATBENCH_PATH=/mnt/ai_models/maatbench
python3 scripts/maat_runtime_guard_v2_demo.py
python3 scripts/maat_runtime_guard_v2_demo.py --http --guard-url http://127.0.0.1:8013
```

## Environment

| Variable | Package | Meaning |
|----------|---------|---------|
| `MAATBENCH_PATH` | decision-api | Directory containing `maatbench/covenant_compiler.py` |
| `TEHUTI_GUARD_PORT` | decision-api | HTTP bind port (default `8013`) |
| `TEHUTI_GUARD_SENTINEL_URL` | decision-api | maat-sentinel base (default `http://127.0.0.1:4242`) |
| `guardApiUrl` in MCP config | mcp-proxy | Base URL for `POST /compile-decision` |

## Wire vocabulary

`allow` | `deny` | `review` | `quarantine` | `escalate`

See `packages/contracts/README.md`.

## Lab integration

The Tehuti Lab `maat-ecosystem` monorepo **consumes** this repo — it no longer owns
the Guard source of truth. Clone alongside the lab or set:

```bash
export TEHUTI_GUARD_ROOT=/path/to/tehuti-guard
```

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/TEHUTI_GUARD_V2_CONSTITUTIONAL_REBUILD.md`](docs/TEHUTI_GUARD_V2_CONSTITUTIONAL_REBUILD.md)
- [`packages/decision-api/README.md`](packages/decision-api/README.md)

## License

MIT — see [LICENSE](LICENSE).
