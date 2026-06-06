# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-05-25 - [SQLite Pagination Bypass]
**Vulnerability:** Resource exhaustion (DoS) via `LIMIT -1` in SQLite queries.
**Learning:** SQLite treats negative LIMIT values as "no limit". Unsanitized user input allowed attackers to fetch the entire alerts database, leading to memory exhaustion and API timeouts.
**Prevention:** Always strictly clamp numeric limits using `max(1, min(MAX_VAL, int(val)))` at both the API and Database abstraction layers (defense-in-depth).
