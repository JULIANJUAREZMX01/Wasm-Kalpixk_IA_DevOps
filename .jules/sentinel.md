# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-06-01 - [Adversarial Baseline Drift & Threshold Misconfiguration]
**Vulnerability:** Baseline poisoning ("boiling frog") attack on sliding-window mean/std thresholds and runtime NameError/AttributeError in API detection results.
**Learning:** Linear mean/std sliding windows gradually absorb adversarial noise, raising the anomaly threshold and blinding detection. Initializing drift guard without direct baseline calibration causes high false positive rates or invalid state.
**Prevention:** Use `AdversarialDriftGuard` with Median and MAD statistics (scaled by 1.4826) with EMA smoothing, filtering unconfirmed anomalous scores from buffer ingestion, and calibrating directly on baseline traffic upon system initialization.
