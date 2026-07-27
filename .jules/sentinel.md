# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-07-27 - [SQLite Pagination Limit Bypass]
**Vulnerability:** SQLite treats negative LIMIT values (e.g., -1) as "no limit," which allows bypassing query boundaries when only upper bound checks are present.
**Learning:** Simple checks like `if limit > 500: limit = 500` fail to secure database queries from pagination bypass and denial of service (DoS) when negative values are provided.
**Prevention:** Always clamp pagination parameters on both sides using `limit = max(1, min(limit, max_allowed))` to enforce proper lower and upper bounds.
