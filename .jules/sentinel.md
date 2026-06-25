# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-06-24 - [v9 Adversarial Drift Poisoning]
**Vulnerability:** Adaptive thresholds using Mean/StdDev are susceptible to "boiling frog" poisoning, where an attacker gradually increases benign noise to inflate the threshold, eventually masking high-severity anomalies.
**Learning:** Robust statistics (Median and Median Absolute Deviation) are significantly more resilient to outliers and controlled drift than traditional Gaussian metrics. Update dampening (exponential smoothing) prevents rapid threshold shifts during high-velocity attacks.
**Prevention:** Use `AdversarialDriftGuard` with robust statistics (MAD * 1.4826) and alpha-smoothing (default alpha=0.1) for all dynamic thresholding logic in detection ensembles.
