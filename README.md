# 🛡️ Wasm-Kalpixk_IA_DevOps

> *"Kalpixki"* — Náhuatl: **Guardian of the house/structure**  
> Our AI is the guardian of the WASM runtime.  
> Prehispanic philosophy meets cutting-edge security technology.

---

## 🎯 What is Wasm-Kalpixk?

**Wasm-Kalpixk** is a **portable Blue Team SIEM compiled to WebAssembly**, powered by an **AMD ROCm-accelerated ML anomaly detection engine** running on the MI300X GPU.

The gap it closes: **75% of WASM modules in the wild are malicious** (CrowdStrike, 2024), yet no native Blue Team tool exists that uses WASM itself to detect WASM threats. Kalpixk is the first.

---

## 🔥 Why This Wins

| Differentiator | Details |
|---|---|
| **Gap de mercado real** | 75% WASM modules malicious, zero Blue Team native tools |
| **AMD ROCm native** | Autoencoder + LSTM running on MI300X — 205.8GB VRAM |
| **Benchmark documentado** | CPU Python vs MI300X speedup — judges need proof of ROCm use |
| **Caso de uso real** | SAC/Manhattan WMS production logs as anomaly feed |
| **Narrativa única** | Kalpixki — náhuatl guardian — story no other team has |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   WASM RUNTIME LAYER                     │
│  Rust → wasm32-wasip1                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ WASM Parser  │  │ Feature      │  │ Bytecode      │ │
│  │ (bytecode)   │→ │ Extractor    │→ │ Signature DB  │ │
│  │              │  │ (10 vectors) │  │               │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │ feature vector [f1..f10]
┌─────────────────────────▼───────────────────────────────┐
│              ML DETECTION ENGINE (AMD ROCm)              │
│  PyTorch 2.9 + ROCm 7.0 — AMD MI300X — 205.8GB VRAM   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ Autoencoder  │  │ Isolation    │  │ LSTM Temporal │ │
│  │ (anomaly     │  │ Forest       │  │ (sequence     │ │
│  │  score)      │  │ (baseline)   │  │  detection)   │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │ anomaly_score + classification
┌─────────────────────────▼───────────────────────────────┐
│                    API + DASHBOARD                       │
│  FastAPI /analyze endpoint                              │
│  Streamlit real-time detection dashboard                │
│  SAC/Manhattan WMS log integration (real prod data)     │
└─────────────────────────────────────────────────────────┘
```

---

## 🧠 WASM Defense Protocols (RFM-inspired)

Kalpixk implements **Zero Trust WASM execution** principles derived from algorithmic defense architecture:

### Severity Levels
| Level | Score Range | Action |
|---|---|---|
| `CLEAN` | 0 – 10 | Pass — normal execution |
| `SUSPICIOUS` | 10 – 50 | Flag + log — monitor |
| `ANOMALY` | 50 – 100 | Quarantine + alert |
| `CRITICAL` | 100+ | **LOCKDOWN** — block + full report |

### Defense Nodes
- **Node Alpha** — Bytecode signature validation (static analysis)
- **Node Beta** — Runtime feature extraction (dynamic analysis)
- **Node Gamma** — ML anomaly scoring (AMD ROCm accelerated)
- **Node Delta** — Response orchestration (API + alerting)

```
WASM binary → [Alpha] → [Beta] → [Gamma: score=102.3] → [Delta: CRITICAL 🔴]
```

### Proof of Concept (AMD MI300X — confirmed)
```
Anomaly score: 102.3110   ← CRITICAL threshold
Device: cuda:0            ← AMD MI300X confirmed
VRAM: 205.8 GB            ← HBM3 unified memory
PyTorch: 2.9.0+rocm7.0   ← ROCm native
```

---

## 📁 Repository Structure

```
Wasm-Kalpixk_IA_DevOps/
├── src/
│   ├── wasm_parser/        # Rust bytecode parser → wasm32-wasip1
│   ├── feature_extractor/  # 10-vector feature extraction
│   └── api/                # FastAPI /analyze endpoint
├── models/
│   ├── autoencoder.py      # PyTorch ROCm autoencoder
│   ├── isolation_forest.py # Baseline model
│   └── lstm_temporal.py    # Sequence anomaly detection
├── benchmarks/
│   ├── cpu_baseline.py     # Python CPU benchmark
│   └── mi300x_rocm.py      # AMD MI300X benchmark
├── data/
│   ├── wasm_corpus/        # Public WASM samples
│   └── wms_logs/           # SAC/Manhattan WMS (anonymized)
├── dashboard/
│   └── streamlit_app.py    # Real-time detection UI
├── docs/
│   ├── ARCHITECTURE.md
│   ├── BENCHMARK_RESULTS.md
│   └── WASM_DEFENSE_PROTOCOLS.md
└── test_motor.py           # ✅ Confirmed working on MI300X
```

---

## ⚡ Hackathon: AMD Developer Hackathon

**Event:** lablab.ai AMD Developer Hackathon  
**Deadline:** May 10, 2026 — 5:30 AM IST (May 9, ~7PM Cancún)  
**Prize:** $10,000 + AMD Radeon AI PRO R9700 GPU  
**Infrastructure:** AMD Developer Cloud — MI300X (kalpixk-dev-01)

---

## 🚀 Quick Start

```bash
# Connect to AMD MI300X droplet
ssh -i ~/.ssh/kalpixk_amd root@129.212.190.56

# Start PyTorch ROCm container
docker start rocm && docker exec -it rocm /bin/bash

# Run anomaly detection proof-of-concept
python3 /workspace/kalpixk/test_motor.py

# Expected output:
# Anomaly score: 102.3110
# Device: cuda:0
# Kalpixk motor OK en MI300X
```

---

## 🌐 Related Projects

| Project | Purpose | Status |
|---|---|---|
| [SAC](https://github.com/JULIANJUAREZMX01/SAC) | Manhattan WMS monitoring — real log source | ✅ Production |
| [KynicOS](https://github.com/JULIANJUAREZMX01/KynicOS) | AMD-first LLM router (Lemonade/Code for Hardware) | ✅ Deployed |
| [python-orchestrator-node](https://github.com/JULIANJUAREZMX01/python-orchestrator-node) | WASM migration analysis orchestrator | ✅ Active |

---

## 🏆 Why AMD ROCm?

The benchmark is the argument. We don't just claim GPU acceleration — we document it:

- **CPU baseline:** Python pure — ~X seconds per batch
- **AMD MI300X:** ROCm 7.0 — ~Xs per batch (**Xx faster**)
- **VRAM utilization:** 205.8 GB HBM3 — unified memory architecture
- **Anomaly score precision:** 4 decimal places — `102.3110` on first run

*Benchmark results will be updated as training progresses — Week 1 target.*

---

## 📜 Philosophy

> "Kalpixki no custodia con fuerza. Custodia con inteligencia.  
> El runtime de WASM es la casa. Kalpixk es su guardián."

Wasm-Kalpixk fuses Nahuatl philosophy with AMD GPU-accelerated security engineering.  
Built in Cancún 🇲🇽 — powered by AMD MI300X — competing globally.

---

*Built for AMD Developer Hackathon 2026 | JULIANJUAREZMX01*
