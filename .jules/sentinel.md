# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-08-21 - [Adversarial Baseline Drift Evasion]
**Vulnerability:** Naive mean/std adaptive thresholding allowed adversaries to slowly shift the baseline ("boiling frog" attack) and evade SIEM detection.
**Learning:** Standard parametric statistics (mean/std) are easily skewed by gradual poison traffic, allowing attackers to raise detection thresholds undetected.
**Prevention:** Use robust non-parametric statistics (Median and MAD) with EMA dampening (`alpha=0.1`) and a MAD floor (`0.01`) in `AdversarialDriftGuard` to resist threshold manipulation.
