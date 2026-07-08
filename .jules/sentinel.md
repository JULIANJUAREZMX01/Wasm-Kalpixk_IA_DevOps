# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-05-25 - [Robust Adversarial Drift Guard]
**Vulnerability:** Adaptive thresholds based on simple mean/std are susceptible to "boiling frog" attacks (gradual drift) and outlier poisoning.
**Learning:** Using Median and Median Absolute Deviation (MAD) provides a much higher breakdown point against malicious samples. Integration requires consistent propagation of the adaptive threshold across the Ensemble and API layers to prevent detection bypass.
**Prevention:** Implement `AdversarialDriftGuard` with dampened (alpha=0.1) Median/MAD updates and strictly use the ensemble-level adaptive threshold for alerting.
