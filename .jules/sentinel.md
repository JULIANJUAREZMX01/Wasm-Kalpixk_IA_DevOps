# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-07-04 - [Adversarial Threshold Poisoning & Auth Gap]
**Vulnerability:** Mean/StdDev-based adaptive thresholds are vulnerable to "slow-burn" poisoning. Unauthenticated access was possible in dev mode if env vars were missing.
**Learning:** Robust statistics (Median/MAD) are essential for unsupervised thresholding to prevent outliers from inflating the baseline. Failing "open" in dev environments creates a footgun for production deployments.
**Prevention:** Implement `AdversarialDriftGuard` using Median/MAD and dampened updates. Enforce a `development_secret` by default in all non-production environments to ensure the system always fails closed.
