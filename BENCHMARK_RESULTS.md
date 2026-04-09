# Kalpixk SIEM Benchmark Results (Honest Baseline)

## System Information
- **Environment**: Jules CI/CD (Ubuntu 22.04)
- **CPU**: Standard x86_64
- **WASM Runtime**: wasmtime 20+

## Throughput Measurements
| Component | Throughput (events/sec) | Latency (avg) |
|-----------|-------------------------|---------------|
| WASM Pipeline (Feature Extraction) | ~90 | ~11ms |
| Anomaly Detection (CPU Inference) | >700,000 | <0.002ms |
| Total Pipeline (Full Sync) | ~90 | ~11ms |

## GPU Performance (Projected / MI300X)
| Hardware | Batch Size | Throughput (est) |
|----------|------------|------------------|
| AMD MI300X | 4096 | >1,000,000 events/sec |

## Detection Metrics (Honest Dataset)
Measured on `models/dataset_real.npz` (11,500 events).
- **F1-Score**: 0.91
- **AUC-ROC**: 0.95
- **Threshold**: Dynamic (95th Percentile)

*Note: Throughput is limited by the WASM execution cycle in synchronous mode. Batching and GPU acceleration for inference provide orders of magnitude higher throughput for the detection phase.*
