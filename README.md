# Kalpixk SIEM 🛡️ ![CI Status](https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps/actions/workflows/main.yml/badge.svg)

**Neural Threat Detection at Ultra-Scale (4.2M ev/s) using WASM Edge & AMD MI300X.**

Kalpixk is a high-performance Security Information and Event Management (SIEM) engine designed for the protection of critical infrastructure, specifically optimized for the **Manhattan WMS at CEDIS Cancún 427**. It leverages WebAssembly (WASM) for efficient edge parsing and AMD MI300X GPUs for massive neural inference throughput.

## 🚀 Quick Links
- **[Live Command Center](https://julianjuarezmx01.github.io/Wasm-Kalpixk_IA_DevOps/dashboard/index.html)**: Zero-install dashboard with real-time telemetry.
- **[Benchmark Results](BENCHMARK_RESULTS.md)**: Detailed metrics on AMD MI300X performance.
- **[Architecture](docs/ARQUITECTURA.md)**: Deep dive into the neural-WASM hybrid engine.

## ⚡ Key Features
- **Neural Ensemble:** Combination of Isolation Forest and Autoencoders for zero-day anomaly detection.
- **WASM-Edge Core:** Log parsing and feature extraction running at near-native speeds in any environment.
- **AMD MI300X Accelerated:** Optimized for ROCm 6.2, achieving over **4.2 Million events/sec**.
- **MITRE ATT&CK Mapping:** Automated mapping of detected vectors to the MITRE framework (T1110, T1485, T1059, etc.).
- **Zero-Install Dashboard:** Fully functional SIEM dashboard available via GitHub Pages, no server required for basic analysis.

## 📊 Performance at a Glance
| Metric | Result |
|--------|--------|
| Throughput | 4,285,120 ev/s |
| Speedup | 3.6x vs Optimized CPU |
| F1-Score | 0.999 |
| Cloud Credits | $46.46 remaining |

## 🛠️ Getting Started
```bash
# Clone the repository
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps

# Build WASM core (requires Rust + wasm-pack)
make wasm-build

# Run the Python backend
pip install -r requirements.txt
python main.py
```

## 🛡️ The Mission
Kalpixk was built to solve the "Log Tsunami" problem in industrial logistics centers. By offloading the parsing to WASM and inference to AMD GPUs, we provide a defense-in-depth solution that is both faster and more cost-effective than traditional JVM-based SIEMs.

---
*Developed by Julian Juarez for the AMD AI Hackathon 2024.*
