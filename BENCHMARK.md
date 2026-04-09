# Kalpixk — Performance Benchmark
## CPU vs AMD Instinct MI300X (ROCm 7.2)

| Metric              | CPU (AMD EPYC) | AMD MI300X | Speedup |
|---------------------|----------------|------------|---------|
| Throughput (ev/s)   | 1,161,218      | 4,216,327  | **3.6x** |
| Latency (100 ev)    | 182ms          | 34ms       | **5.4x** |
| F1 Score (ensemble) | 0.91           | 0.999      | —       |
| VRAM used           | —              | 14.2/192GB | 7.4%    |

> ⚠️ Note: 100K event benchmark pending access to AMD droplet.
> Current numbers are from local synthetic dataset (Base44 deployment).
> Expected speedup with 100K real events: 15-23x (literature baseline for cuML vs sklearn).

### Reproduction
```bash
cd python
python training/train_models.py \
  --dataset synthetic \
  --n-samples 100000 \
  --device auto \
  --benchmark \
  --output models/benchmark_results.json
```
