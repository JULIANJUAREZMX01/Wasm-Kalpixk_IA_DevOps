# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-06-01 - [Ensemble Adaptive Threshold Bypass]
**Vulnerability:** Adaptive threshold security bypass via incorrect variable assignment in ensemble logic.
**Learning:** Even if a robust AdversarialDriftGuard module is implemented and updated with batch scores, returning the legacy or individual model threshold (like Isolation Forest's simple Mean/StdDev threshold) in the prediction endpoint bypasses the robust statistical guard entirely. This leaves the system completely vulnerable to baseline shifting ("boiling frog") attacks and leads to extreme false-positive/negative rates under varying traffic.
**Prevention:** Ensure the combined ensemble prediction returns the robust `current_threshold` calculated directly from the active `drift_guard` update, and rigorously test the anomaly rate on baseline/normal traffic fixtures.
