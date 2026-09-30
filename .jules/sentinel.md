# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-05-24 - [Subprocess URL & Script Input Validation]
**Vulnerability:** Unvalidated environment variables and script existence in background process initialization (`/api/simulate/start`).
**Learning:** Subprocess execution helper endpoints that consume backend URLs from environment without scheme validation or control character checks can lead to SSRF or argument injection.
**Prevention:** Always validate URL schemes (`http://` / `https://`), sanitize against control characters/whitespace, and verify target script existence before calling `subprocess.Popen`.
