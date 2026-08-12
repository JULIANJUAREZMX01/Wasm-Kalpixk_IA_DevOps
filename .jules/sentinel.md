# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-08-12 - [Robust Adversarial Drift Guarding]
**Vulnerability:** Adversarial Drift / 'Boiling Frog' attacks designed to gradually shift the adaptive threshold of the ensemble anomaly detector by feeding slowly increasing benign scores.
**Learning:** Simple mean and standard deviation metrics are highly susceptible to outlier and drift injection. Robust statistical metrics (Median and Median Absolute Deviation) combined with dampened Exponential Moving Average updates provide exceptional resilience.
**Prevention:** Integrate `AdversarialDriftGuard` using Median & MAD calculations, with an absolute floor of 0.01 for MAD, and enforce calibration safeguards during API startup to protect telemetry and stream evaluation endpoints.
