# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-06-19 - [v9 Adversarial Poisoning]
**Vulnerability:** 'Boiling Frog' poisoning of adaptive detection thresholds.
**Learning:** Attackers can slowly raise detection thresholds by injecting near-boundary benign-looking samples, eventually blinding the system to sharp anomalies.
**Prevention:** Implement `AdversarialDriftGuard` with update dampening (alpha-factor) and Z-score windowing to reject outlier-driven threshold shifts.
