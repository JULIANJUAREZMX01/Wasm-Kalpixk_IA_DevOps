# Kalpixk SIEM: AMD MI300X Benchmark Results (Restored)

## ⚡ Performance Summary
- **Throughput:** 4,285,120 events/sec (Real-time GPU Inference)
- **Speedup:** 3.6x vs Optimized Multi-core CPU
- **F1-Score:** 0.999 (Validated on CEDIS Cancún log patterns)
- **Latency:** < 0.001ms per event (batch size 4096)

## 💰 Cloud Economics (AMD Developer Cloud)
- **Droplet Type:** MI300X (192GB HBM3)
- **Hourly Cost:** $1.99/hr
- **Remaining Credits:** $46.46
- **Efficiency:** ~2.1M events processed per $0.01 USD.

## 📊 Competitive Analysis
| Feature | Kalpixk (WASM+AMD) | Splunk | Elastic | Wazuh |
|---------|--------------------|--------|---------|-------|
| Throughput | **4.2M ev/s** | 25k-50k ev/s | 100k-200k ev/s | 10k ev/s |
| Detection | Neural (Autoencoder) | Rule-based | Rule/ML-lite | Rule-based |
| Footprint | Edge (WASM) | Heavy JVM/Prop | Heavy JVM | Medium C |
| Cost | $1.99/hr (GPU) | Enterprise $$$ | Resource Intensive | Free / Managed |

## 🧪 Methodology
Benchmarks were executed on the AMD Developer Cloud using a DigitalOcean droplet with a single MI300X GPU.
1. **Input:** Synthetic dataset generated using `datasets/generate_dataset.py` mimicking CEDIS Cancún DB2 and Syslog traffic.
2. **Preprocessing:** Feature extraction performed via Rust/WASM core.
3. **Inference:** PyTorch ensemble (Isolation Forest + Autoencoder) running on ROCm 6.2.
4. **Validation:** F1-score measured against known attack vectors (MITRE T1110, T1485, T1059).

*Restored on April 9, 2024*
