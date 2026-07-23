# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-07-23 - [SQLite Pagination Limit Bypass]
**Vulnerability:** SQLite interprets negative LIMIT parameters (like LIMIT -1) as "no limit", allowing attackers to retrieve all table records and cause API denial of service or information exposure.
**Learning:** Simply checking `limit > 500` is insufficient since negative values bypass the upper boundary check and are passed unvalidated to the database engine.
**Prevention:** Clamp pagination limits strictly on both ends using `limit = max(1, min(limit, max_allowed))` before executing database queries.
