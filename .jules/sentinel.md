# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-06-17 - [Adversarial Drift Protection]
**Vulnerability:** "Boiling Frog" poisoning where an attacker slowly increases benign-looking scores to drift the adaptive threshold upward.
**Learning:** Purely statistical thresholds without update dampening are vulnerable to gradual poisoning that creates a "blind spot" for subsequent high-score attacks.
**Prevention:** Implement `AdversarialDriftGuard` with alpha-dampening (e.g., 0.1) to restrict the maximum rate of threshold change per recalibration cycle.
