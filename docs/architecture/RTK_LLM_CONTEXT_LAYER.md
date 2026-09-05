# RTK LLM Context Layer — Architecture Decision

## Decision

Evaluate **rtk-ai/rtk** as an optional context-efficiency layer at the tool-output boundary.

RTK is not an LLM, model router, memory engine, or inference accelerator. It is a Rust CLI proxy that filters and compresses command output before that output enters an agent's context. The upstream project documents a single Rust binary, 100+ command integrations, sub-10ms overhead, hook-based command rewriting, and output reductions of up to 90% for supported commands.

## Proposed Kalpixk topology

```text
LLM / Agent Orchestrator
        |
        v
Tool / Shell Request
        |
        v
+---------------------------+
| Context Efficiency Layer  |
|                           |
| RTK adapter (optional)    |
| deterministic redaction   |
| evidence preservation     |
+-------------+-------------+
              |
              v
        Tool execution
              |
              v
   compact agent-facing output
              |
              +----> raw evidence store / audit log
```

## Why this fits Kalpixk

Kalpixk already has Rust/WASM and Python layers. RTK is also Rust, but its responsibility is orthogonal: it reduces command-output noise. The correct integration is therefore an **adapter/process boundary**, not embedding RTK into the detection engine or linking it into the WASM inference path.

### Expected benefits

- Lower context pressure for command-heavy agents.
- More deterministic evidence summaries for repetitive CLI output.
- Less redundant shell output entering LLM context.
- Reusable support for Codex/Claude/Gemini/Cursor-style command workflows through RTK's existing hook/plugin model.
- No coupling between context optimization and anomaly-model correctness.

## Non-goals

- Do not replace the LLM.
- Do not modify model inference, ROCm, ONNX/PyTorch, or WASM scoring.
- Do not compress security evidence before deterministic parsing.
- Do not discard raw command output needed for forensic/audit records.
- Do not vendor RTK into this repository at this stage.

## Safety and correctness gates

1. **Fail-open:** if `rtk` is unavailable or exits unsuccessfully, return the original command output.
2. **Raw evidence first:** preserve the original stdout/stderr and exit status before optimization.
3. **Structured-output bypass:** JSON, SARIF, machine-readable CI artifacts, and security evidence should bypass lossy compression unless a schema-aware adapter is explicitly enabled.
4. **Command allowlist:** only known-safe command families should be rewritten automatically.
5. **Version pinning:** record the tested RTK version in the integration manifest.
6. **Golden tests:** compare raw output against optimized output for representative Git, test, filesystem, and diagnostic commands.
7. **No trust escalation:** RTK output is presentation/context material, not authoritative security evidence.

## Compatibility finding

The upstream RTK `develop` branch currently declares Rust 1.91 and edition 2021. Kalpixk should therefore avoid directly adding RTK as a Cargo workspace member until the workspace toolchain is verified against that requirement. A subprocess/adapter integration has a smaller compatibility surface.

## Proposed implementation phases

### Phase A — Adapter

Add a small Python/Rust adapter that:

- detects `rtk` with PATH lookup;
- executes the requested command through RTK only for approved command classes;
- captures raw output before optimization;
- exposes both `raw` and `context` representations;
- records RTK version and elapsed time.

### Phase B — Agent orchestration

Connect the adapter to the Kalpixk agent/tool orchestration layer. The LLM receives `context`; the audit pipeline receives `raw`.

### Phase C — Verification

Benchmark token-estimation reduction, wall-clock overhead, failure behavior, and semantic preservation. Do not use RTK's estimated bytes/4 metric as an exact billing metric.

## Current verdict

**LOGICALLY VALID, but as an optional boundary layer.**

The architecture should be:

`agent -> tool request -> RTK adapter -> command -> raw evidence + compact context -> agent`

not:

`LLM -> RTK -> model inference -> WASM`.

The second topology incorrectly assigns RTK responsibility for model execution and would create unnecessary coupling.
