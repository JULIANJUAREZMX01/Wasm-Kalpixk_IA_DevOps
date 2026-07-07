# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-07-07 - [Ensemble Threshold Evasion]
**Vulnerability:** Simple Mean/StdDev adaptive thresholds are susceptible to "boiling the frog" adversarial drift, where an attacker slowly increases the baseline score to blind the SIEM.
**Learning:** Robust statistics (Median/MAD) combined with dampened updates and confirmed-benign buffer gating are essential to resist adversarial score inflation.
**Prevention:** Use `AdversarialDriftGuard` for all ensemble-level detection thresholds.
