# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-10-31 - [Honeypot Client Host Null Dereference DoS]
**Vulnerability:** Unchecked access to `request.client.host` in FastAPI honeypot routes causing `AttributeError` runtime crash when `request.client` is `None`.
**Learning:** Reverse proxies, test harnesses, or ASGI protocol edge cases can omit client network attributes. Direct property access without a fallback crashes request handling with HTTP 500.
**Prevention:** Guard all client address resolution with `request.client.host if request.client else "unknown"` across telemetry, SIEM logging, and deception endpoints.
