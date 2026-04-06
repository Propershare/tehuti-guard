# Tehuti-Guard

**Security layer for Model Context Protocol servers**

Forked from ContextGuard with a focus on per-tool policies, stricter allowlists, and operational guardrails for MCP deployments.

---

## 🎯 Why Tehuti-Guard?

- MCP servers routinely face:
  - 🔓 Prompt injection
  - 🔑 API key leakage
  - 📁 Unauthorized file access and traversal
  - 🚨 Tool abuse (runaway loops / rate abuse)
- Tehuti-Guard adds defense-in-depth with configurable, versioned policies and auditable enforcement.

Key differences from upstream ContextGuard:
- Stricter defaults: allowlists per tool/server, explicit policy schema (planned).
- Per-tool granularity (planned), stronger rule packs, and richer observability.
- Designed to wrap common MCP deployments (mcpo, OpenWebUI, workflow engine, custom servers).

### What’s different from upstream (at a glance)
- Product name: **Tehuti-Guard** (fork of ContextGuard)
- Stricter defaults and policy schema planned (allowlists per tool/server)
- Roadmap for per-tool allow/deny and per-tool rate limits
- Rule packs with versioning/auto-update planned
- Planned HTTP/SSE proxy mode (beyond stdio)
- Planned observability: Prometheus metrics + webhook sinks
- Planned attack corpus + regression suite to manage block/FP rates

---

## 🚀 Quick Start

```bash
# install globally
npm install -g contextguard   # (base dependency; fork will publish as tehuti-guard)

# wrap an MCP server (example)
tehuti-guard --server "node /path/to/server.js" --config /path/to/config.json
```

Claude/OpenWebUI config example:
```json
{
  "mcpServers": {
    "secured-server": {
      "command": "tehuti-guard",
      "args": [
        "--server",
        "node /path/to/your-server.js",
        "--config",
        "/path/to/config.json"
      ]
    }
  }
}
```

---

## 🧪 Quick Test

Example `config.json`:
```json
{
  "maxToolCallsPerMinute": 5,
  "enablePromptInjectionDetection": true,
  "enableSensitiveDataDetection": true,
  "enablePathTraversalPrevention": true,
  "allowedFilePaths": ["/tmp/safe-directory"],
  "logPath": "/tmp/mcp_security.log",
  "logLevel": "info"
}
```

Attacks to verify:
- Dump API keys → ✅ BLOCKED
- "Ignore previous instructions" → ✅ BLOCKED
- `../../../../etc/hosts` → ✅ BLOCKED

---

## ✨ Features (current)

| Feature                        | Description                                 | Status |
| ------------------------------ | ------------------------------------------- | ------ |
| Prompt Injection Detection     | Blocks common injection patterns            | ✅     |
| Sensitive Data Scanning        | Detects keys/passwords/SSNs patterns        | ✅     |
| Path Traversal Prevention      | Blocks unauthorized file access             | ✅     |
| Rate Limiting                  | Per-server threshold                        | ✅     |
| JSON Logging                   | Structured logs with severity               | ✅     |
| Per-tool policy granularity    | Allow/deny, per-tool limits                 | 🔜     |
| Rule packs (versioned)         | Curated PI/secret/path rules, updatable     | 🔜     |
| HTTP/SSE proxy mode            | Beyond stdio                                | 🔜     |
| Metrics & webhook sinks        | Prometheus + Discord/Slack/webhook          | 🔜     |
| SQL/XSS detection              | Extended detectors                          | 🔜     |

---

## 🔍 How It Works

Tehuti-Guard sits between the MCP client and server:
```
Client (Claude/OpenWebUI) -> Tehuti-Guard -> Your MCP Server
```
It evaluates tool calls against policies (rate, prompt-injection, secrets, path rules) and logs/blocks as configured.

---

## ⚙️ Configuration

Example `config.json`:
```json
{
  "maxToolCallsPerMinute": 30,
  "enablePromptInjectionDetection": true,
  "enableSensitiveDataDetection": true,
  "enablePathTraversalPrevention": true,
  "allowedFilePaths": ["/srv/tehuti", "/srv/projects"],
  "logLevel": "info",
  "logPath": "/var/log/tehuti-guard/filesystem.log"
}
```

Roadmap additions (planned):
- Per-tool allow/deny lists
- Per-tool rate limits
- Deny-by-default mode with explicit allowlists
- Policy schema + `--validate-config`

### Example presets
- `examples/filesystem.json`: strict paths for file tools, deny execute/delete.
- `examples/postgres.json`: allow read-only queries; deny execute.
- `examples/workflow-mcp.json`: allow discovery/validation tools with rate caps.

---

## Security Events (JSON)
```json
{
  "timestamp": "2025-12-16T10:30:45.123Z",
  "eventType": "SECURITY_VIOLATION",
  "severity": "HIGH",
  "toolName": "write_file",
  "details": {
    "violations": ["Path traversal detected: ../../etc/passwd"],
    "blocked": true
  }
}
```

---

## Performance Target
| Metric           | Target |
| ---------------- | ------ |
| Latency overhead | <1–2%  |
| Memory           | ~+15MB |

---

## Roadmap (fork goals)
- Per-tool policies (allow/deny, rate, path scopes)
- Rule packs with versioning and auto-update
- HTTP/SSE proxy mode
- Prometheus metrics + webhook sinks
- Config schema + validation CLI
- Attack corpus + regression suite

---

## Defense in Depth
- Least privilege: run under non-root users
- Strict allowlists for filesystem/DB tools
- Network isolation: loopback-only where possible
- systemd hardening: NoNewPrivileges, ProtectSystem, PrivateTmp
- Logging + alerts: Discord/webhook and metrics

---

## Contributing
- Fork, branch, add tests, open PR.
- Focus areas: rule packs, per-tool policies, transports, metrics/alerts, test corpus.

## License
MIT (inherited from upstream)

## Support
- Issues: (new fork tracker)
- Docs: this README + policy docs

