# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-05-24 - [Adversarial Drift Poisoning]
**Vulnerability:** Adaptive thresholds using simple mean/std are susceptible to "frog boiling" attacks where an attacker slowly shifts the baseline to hide malicious activity.
**Learning:** Using robust statistics (Median/MAD) combined with alpha-dampening renders the detection threshold resilient to gradual poisoning attempts.
**Prevention:** Standardize on `AdversarialDriftGuard` for all adaptive thresholding in the ensemble core.
