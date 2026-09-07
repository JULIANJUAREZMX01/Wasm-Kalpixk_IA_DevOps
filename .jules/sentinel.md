# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-09-07 - [Non-Finite Float Threshold Poisoning]
**Vulnerability:** Unsanitized non-finite float inputs (`NaN`, `Infinity`) in feature payloads.
**Learning:** Ingesting non-finite floats into machine learning pipelines corrupts statistical state estimators (e.g., `AdversarialDriftGuard` threshold becomes `NaN`, permanently disabling anomaly detection). Additionally, default FastAPI error handlers crash with 500 when attempting to serialize non-finite floats inside `RequestValidationError` detail structures.
**Prevention:** Enforce `math.isfinite` validation on all numeric input fields via Pydantic validators and sanitize validation error details before JSON serialization.
