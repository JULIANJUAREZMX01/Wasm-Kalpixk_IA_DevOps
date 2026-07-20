# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-07-20 - [Adversarial Drift Poisoning]
**Vulnerability:** Adversarial baseline shifting ("boiling frog" attacks) where simple Mean/StdDev thresholds are progressively shifted upward by injecting slowly increasing benign-looking traffic, eventually rendering the detection system blind to actual attacks.
**Learning:** Mean and standard deviation are non-robust statistics that are highly susceptible to outlier injection. In contrast, Median and Median Absolute Deviation (MAD) are robust estimators of central tendency and variability. Incorporating an exponential moving average (EMA) dampening factor for statistics updates ensures the baseline does not drift rapidly.
**Prevention:** Implement `AdversarialDriftGuard` using Median and MAD statistics combined with a dampened update mechanism (such as EMA) and ensure proper integration within the detection ensemble's prediction loop.
