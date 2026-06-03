# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-06-03 - [v9 XOCHIMILCO Mesh & Integrity]
**Vulnerability:** Unauthenticated mesh registration and WASM binary tampering for defense neutralization.
**Learning:** Centralized defense can be blinded by node impersonation. Binary patching can disable safety hooks silently.
**Prevention:** Implement deterministic polymorphic challenges (XOCHIMILCO markers) and rolling FNV-1a binary hashes to enforce absolute mesh and code integrity.
