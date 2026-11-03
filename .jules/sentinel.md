# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-11-04 - [Attack Simulator Subprocess & SSRF Injection]
**Vulnerability:** In `POST /api/simulate/start`, `KALPIXK_BACKEND_URL` was read directly from environment variables and interpolated into a background CLI subprocess execution without validation.
**Learning:** Background simulator utilities can be hijacked if backend URL arguments contain malformed schemes or unvalidated characters, enabling unexpected process behavior or SSRF attacks.
**Prevention:** Strictly validate backend URL schemes (`http`, `https`), verify hostname presence and legal characters via regex, and ensure the script target file exists on disk prior to spawning subprocesses.
