# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-07-01 - [Adversarial Threshold Poisoning]
**Vulnerability:** Adaptive thresholds based on Mean/StdDev are susceptible to "boiling frog" attacks where an attacker slowly drifts the baseline.
**Learning:** Robust statistics (Median/MAD) are significantly more resilient to outliers and gradual poisoning than standard mean-based methods.
**Prevention:** Implement `AdversarialDriftGuard` with Median/MAD and update dampening (alpha-smoothing) to enforce stability.

## 2026-07-01 - [Insecure Dev Default Auth]
**Vulnerability:** API key verification allowed unauthenticated access if the environment variable was missing in dev mode.
**Learning:** Security defaults must be fail-closed or fail-to-known-secret even in development environments to prevent accidental exposure.
**Prevention:** Strictly default to a non-empty `development_secret` if `KALPIXK_API_KEY` is unset.
