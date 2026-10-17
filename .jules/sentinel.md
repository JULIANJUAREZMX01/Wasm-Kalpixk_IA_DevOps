# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-05-25 - [FastAPI Non-Finite Float Validation Crash]
**Vulnerability:** Non-finite float input injection (`NaN`, `Infinity`) bypassing neural detection (`NaN > threshold` evaluates to `False`) and crashing FastAPI response serialization with 500 Internal Server Error when formatting validation error details.
**Learning:** Pydantic validation errors capture raw `input` values. When `input` contains `inf` or `nan`, FastAPI's standard `request_validation_exception_handler` fails during `json.dumps()` serialization.
**Prevention:** Validate input floats with `math.isfinite` and register a custom `RequestValidationError` handler that recursively sanitizes non-finite floats in error details to `None`.
