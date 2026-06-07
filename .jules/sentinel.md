# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-06-07 - [Pagination & Resource Exhaustion]
**Vulnerability:** SQLite `LIMIT -1` bypass and `NameError` in detection API.
**Learning:** SQLite interprets `LIMIT -1` as "no limit", which can be used to bypass client-side caps if not properly validated as a positive integer. Additionally, unverified variables in anomaly-branch loops cause DoS (500 error) exactly when a real threat is detected.
**Prevention:** Always clamp pagination limits using `max(1, min(N, int(v)))` at both API and DB layers. Ensure all result-building loops are covered by integration tests that actually trigger the anomaly branch.
