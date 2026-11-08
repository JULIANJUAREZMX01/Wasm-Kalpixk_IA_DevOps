# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-11-08 - [Alert Pagination Limit Bypass & Database DoS]
**Vulnerability:** Unconstrained query parameters in `/api/alerts` allowed negative (`limit <= 0`) or unbounded limit inputs to reach backend handlers without schema validation. In SQLite, `LIMIT -1` bypasses pagination limits and dumps all table rows.
**Learning:** Validating and clamping numeric boundaries inside database utility functions alone leaves the API route open to schema tampering and denial-of-service payloads. Route query parameters must declare strict boundaries (`ge=1, le=500`).
**Prevention:** Always declare FastAPI `Query(..., ge=1, le=500)` constraints at the route definition and keep defensive clamping (`max(1, min(limit, 500))`) before database invocation.
