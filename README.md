# Wasm-Kalpixk_IA_DevOps 🔬

> **del náhuatl: "el que cuenta"** — Motor de detección de anomalías en runtimes WASM acelerado por AMD MI300X

[![AMD MI300X](https://img.shields.io/badge/AMD-MI300X-ed1c24?style=flat&logo=amd)](https://www.amd.com)
[![PyTorch ROCm](https://img.shields.io/badge/PyTorch-ROCm%207.0-ee4c2c?style=flat&logo=pytorch)](https://pytorch.org)
[![F1-Score](https://img.shields.io/badge/F1--Score-0.999-32ff32?style=flat)](#resultados)
[![Hackathon AMD 2026](https://img.shields.io/badge/Hackathon-AMD%202026-ff6400?style=flat)](#)

## 🏆 Resultados Validados (AMD MI300X)

| Métrica | Valor |
|---------|-------|
| **Throughput GPU** | **4,216,327 eventos/segundo** |
| **Speedup vs CPU** | **3.6x más rápido** |
| **F1-Score** | **0.999** |
| **VRAM disponible** | 192 GB HBM3 |
| **Stack** | PyTorch ROCm 7.0 · Rust/WASM · FastAPI |

→ Ver [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) para resultados completos.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                     EDGE (Rust/WASM)                    │
│  32 features por evento · Shannon entropy · <1ms/batch  │
└─────────────────────┬───────────────────────────────────┘
                      │ MessagePack WebSocket (95% < JSON)
┌─────────────────────▼───────────────────────────────────┐
│            AMD MI300X · 192 GB HBM3 · ROCm 7.0          │
│  Autoencoder 32→16→4→16→32 · 4.2M eventos/seg           │
│  vLLM + Llama 3.1 → explicación MITRE ATT&CK            │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Arranque rápido

```bash
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps
cp .env.example .env    # configurar tokens
make setup              # instalar dependencias
make train              # entrenar modelo
make run                # levantar API + dashboard
```

## 📋 Skills disponibles

```bash
make status            # estado del sistema (GPU, RAM, modelo)
make train             # entrenar con baseline (1000 muestras, 100 epochs)
make detect            # detección única
make detect-loop       # monitoreo continuo cada 30s
make benchmark         # throughput AMD MI300X
make test              # suite de tests (15/15)
```

## 📁 Estructura

```
src/
  detector/        # AnomalyDetector v2.1 (normalización + auto-threshold)
  runtime/         # WasmRuntimeMonitor (32 features)
  channels/        # Telegram bot + WhatsApp/Twilio
  monitor/         # SystemMonitor (background thread)
  dashboard/       # Control center (React-compatible HTML)
  ui/              # Tema visual SACITY/hacker AMD
skills/            # Scripts CLI reutilizables
tests/             # Suite completa (15/15 passing)
benchmarks/        # GPU vs CPU comparativas
models/            # Pesos del modelo entrenado
```

## 🛡️ MITRE ATT&CK cubiertos

T1055 · T1496 · T1059 · T1048 · T1611 · T1620 · T1203 · T1027

## 📊 Tests

```bash
pytest tests/ -v
# 15 passed in ~9s (CPU mode)
```

---
*by [JULIANJUAREZMX01](https://github.com/JULIANJUAREZMX01) — AMD Developer Program — Hackathon 2026*
