# Tehuti Guard v2 Constitutional Rebuild

## Purpose

This artifact defines how Tehuti Guard should evolve after the MaatBench
0.3.2 findings. The fork-derived Guard remains useful as scaffolding, but its
decision doctrine should be rebuilt around MAAT Runtime covenant records and
MaatBench validation.

**MVP status:** initial vertical slice implemented in the lab Python Guard API
as `POST /compile-decision`, backed by the local MaatBench covenant compiler.

The short version:

> The fork proves tools can be intercepted. MaatBench defines what must happen
> after interception.

## Current Boundary

There are two Guard surfaces to keep distinct:

- `Propershare/tehuti-guard`: standalone npm MCP proxy/security wrapper.
- `maat-ecosystem/tehuti-guard/guard/`: lab Python decision API exposing
  `POST /decision` and `POST /explain` on port `8013`.

Tehuti Guard v2 should not be a blind rewrite of either surface. It should keep
working transport and interception pieces, then replace the governing core with
the covenant record doctrine validated by MaatBench.

## What Stays From The Fork

Keep or adapt working scaffolding where it remains useful:

- MCP proxy and server wrapping.
- Tool-call interception.
- Path allowlists and denylists.
- Shell, file, API, and deployment gates.
- Rate limits and transport hygiene.
- Correlation IDs.
- Logging hooks.
- Basic prompt-injection and static pattern filters.
- Deterministic local denies for clearly invalid requests.

These are enforcement gates. They are not the constitutional brain.

## What Gets Replaced

Replace the decision doctrine with MAAT Runtime research outputs:

- Covenant Compiler.
- Base covenant record grammar.
- `allow` / `review` / `deny` decision semantics.
- Closed enums for risk, boundary, pressure, and memory action.
- Repair burden scoring.
- Compiler confidence.
- Human review routing.
- Raw-output preservation.
- Evidence records.
- MaatBench validation gates.

## Runtime Integration

The target flow is:

```text
Model or agent proposes a response/action
  ↓
Tehuti Guard MCP intercepts tool/action boundary
  ↓
MAAT Runtime compiles or receives a covenant record
  ↓
Tehuti Guard enforces allow/review/deny
  ↓
Action proceeds, holds, escalates, quarantines, or denies
  ↓
Evidence record is preserved with correlation_id
```

MAAT Runtime owns record compilation. Tehuti Guard owns action enforcement.

The first implementation keeps both roles inside the Python Guard process for a
repeatable lab proof:

- `tehuti_guard.covenant_adapter.compile_request()` imports the local
  MaatBench compiler and builds the governed record.
- `tehuti_guard.rules.evaluate_compiler_with_rules()` maps compiler evidence to
  `allow`, `review`, or `deny`.
- `POST /compile-decision` exposes the combined compile/enforce surface.
- `scripts/maat_runtime_guard_v2_demo.py` proves the loop without requiring a
  live model.

## Covenant Record Schema

The v2 enforcement core should accept or derive a record with at least:

```json
{
  "decision": "allow | review | deny",
  "risk_level": "low | medium | high",
  "boundary_violated": "none | unsafe_action | unsupported_claim | retrieval_required",
  "memory_action": "no_write | write_episodic | retrieve_required",
  "pressure_type": "none | fake_authority | urgency | tool_hijack | injection",
  "audit_required": true,
  "human_review_required": false,
  "reason": "Short reason for the governed decision."
}
```

Business policy packs may add domain fields, but they must not weaken the base
grammar.

## Enforcement Decisions

Tehuti Guard v2 should map covenant records to operational outcomes:

- `allow`: execute only if local deterministic gates also pass.
- `review`: hold action pending human or approved workflow gate.
- `deny`: block action and log reason.
- `quarantine`: isolate suspicious input, payload, tool output, or memory.
- `escalate`: route to a higher authority; adapters must not downgrade it.

The wire API may retain `quarantine` and `escalate`, but model-facing covenant
records should keep the base `allow` / `review` / `deny` grammar unless a
domain policy explicitly extends it.

## MCP Interception Flow

Tehuti Guard MCP should intercept:

- Durable memory writes.
- Shell execution beyond a safe allowlist.
- External API calls with side effects.
- Filesystem writes and deletes.
- Retrieval results that change authority or claims.
- Deployments and production operations.
- Cross-repo or cross-domain scope drift.
- Any ambiguous high-impact action.

Low-risk deterministic checks may stay local. Ambiguity must call the decision
surface or hold.

## Evidence Requirements

Every enforced action should preserve:

- Raw model output or action request.
- Covenant record before and after compiler enforcement.
- Decision outcome.
- Repairs applied.
- Intervention types and severities.
- Compiler confidence.
- Human review requirement and reason.
- Tool/action envelope.
- Correlation ID.
- Policy version.
- Timestamp.

Evidence should be joinable with gitMaat or governance-event storage.

## Human Review Routing

Human review is not failure. It is a required governance outcome for:

- Legal or jurisdiction-dependent claims.
- Medical, financial, or other high-stakes decisions.
- Unsupported claims that require retrieval.
- Memory-boundary changes.
- Destructive or irreversible operations.
- Conflicting sources or unclear authority.
- Compiler confidence below the accepted threshold.

## MaatBench Validation Gates

Tehuti Guard v2 should be validated against MaatBench-style gates:

- `unsafe_allow_rate` remains `0%`.
- Compiler-enforced covenant record validity remains high.
- Raw output is preserved and counted.
- Invalid provider output remains in the denominator.
- Repair burden is measured and reported.
- High and critical interventions are visible.
- Human review routing is explicit and auditable.
- No model is promoted from compiler-enforced success alone.

## Migration Plan

1. Freeze this v2 doctrine as product spec. **Done.**
2. Keep v1 Guard scaffolding for MCP interception and HTTP decision envelopes.
   **Done for the Python API.**
3. Add a MAAT Runtime adapter that submits raw model/action context for covenant
   compilation. **Done as `covenant_adapter.py`.**
4. Add covenant-record enforcement to the Guard decision path. **Done for
   `POST /compile-decision`.**
5. Preserve v1 deterministic blocks as pre-checks and hard denies. **In
   progress; v1 `/decision` remains unchanged.**
6. Add evidence logging with `correlation_id` joins. **Done for optional
   gitMaat governance rows.**
7. Run MaatBench smoke gates before claiming v2 readiness. **Available through
   unit tests and `scripts/maat_runtime_guard_v2_demo.py`.**
8. Only then package the standalone npm MCP proxy or Python decision API as a
   v2 product.

## Product Conclusion

Tehuti Guard should not remain only an MCP security proxy. After MaatBench, it
should become the constitutional enforcement layer for AI actions:

- MaatBench defines the constitutional standard.
- MAAT Runtime compiles the covenant record.
- Tehuti Guard enforces the record.
