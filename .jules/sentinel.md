# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-06-01 - [Pagination & Auth Hardening]
**Vulnerability:** SQLite `LIMIT -1` bypass and unauthenticated access in development mode.
**Learning:** Defaulting to open access in development or allowing unconstrained `limit` parameters can lead to data exposure and resource exhaustion. SQLite treats `LIMIT -1` as "no limit".
**Prevention:** Always clamp pagination parameters to a safe range [1, 500] and enforce a fail-secure authentication fallback (e.g., `development_secret`) even in non-production environments.
