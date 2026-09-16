# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-05-25 - [FastAPI RequestValidationError Non-Finite Float Serialization DoS]
**Vulnerability:** Non-finite float inputs (`NaN`, `Infinity`) in request payloads causing 500 Unhandled Exception crashes during JSON error response rendering.
**Learning:** When FastAPI handles `RequestValidationError`, `exc.errors()` includes raw user inputs in `input`. Python's `json.dumps` fails on `NaN`/`Inf`, turning 422 Unprocessable Entity into a 500 Server Error crash.
**Prevention:** Implement a custom `RequestValidationError` handler in FastAPI using recursive sanitization (`_sanitize_non_finite`) to replace `inf`/`nan` in error details with `None` before `jsonable_encoder` serialization.
