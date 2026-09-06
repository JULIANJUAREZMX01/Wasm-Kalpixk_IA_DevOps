# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-04-08 - [Non-Finite Float Injection & Serializer Crash]
**Vulnerability:** Non-finite floats (NaN/Infinity) in request feature arrays polluted the adaptive drift guard buffer and caused FastAPI default error handlers to crash with 500 Internal Server Errors when trying to serialize `exc.errors()`.
**Learning:** Pydantic permits NaN/Inf float types, and Python's standard `json.dumps()` raises ValueError when serializing raw non-finite numbers present in validation error inputs.
**Prevention:** Enforce `math.isfinite()` on all incoming array inputs at the Pydantic validator boundary and filter non-finite scores in model threshold guards; sanitize `exc.errors()` via `jsonable_encoder()` in custom `RequestValidationError` handlers.
