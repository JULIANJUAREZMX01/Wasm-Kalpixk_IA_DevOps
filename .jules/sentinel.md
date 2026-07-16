# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-05-24 - [Adversarial Drift Protection]
**Vulnerability:** Adaptive thresholds using simple Mean/StdDev are vulnerable to adversarial "boiling frog" attacks, where an attacker slowly shifts the baseline to hide anomalies.
**Learning:** Robust statistics like Median and MAD (Median Absolute Deviation) are significantly harder to poison. Using dampened updates (EMA) on these statistics adds another layer of defense against rapid shifts.
**Prevention:** Always use robust statistical guards (like AdversarialDriftGuard) for ensemble-level thresholds instead of component-level simple thresholds.
