# 🛡️ Wasm-Kalpixk_IA_DevOps

> *"Kalpixki"* — Náhuatl: **Guardián/Protector** — Un SIEM portátil compilado a WebAssembly, con motor de detección de anomalías acelerado por AMD ROCm en MI300X.

[![AMD MI300X](https://img.shields.io/badge/AMD-MI300X-ed1c24?style=flat&logo=amd)](https://www.amd.com)
[![ROCm 7.0](https://img.shields.io/badge/ROCm-7.0-ff6400?style=flat)](https://rocm.docs.amd.com)
[![F1=0.999](https://img.shields.io/badge/F1--Score-0.999-32ff32?style=flat)](#benchmark)
[![Hackathon AMD](https://img.shields.io/badge/Hackathon-AMD%202026-ed1c24?style=flat)](#hackathon)
[![MIT](https://img.shields.io/badge/License-MIT-blue?style=flat)](LICENSE)

---

## 🎯 ¿Qué es Kalpixk?

**El gap que cierra:** Los SIEMs modernos detectan *después* del ataque — cuando el disco ya está cifrado. Kalpixk lo invierte con una arquitectura de 3 capas:

```
┌──────────────────────────────────────────────────────────────┐
│  EDGE (Rust → WASM) — Zero install, corre en browser        │
│  5 parsers × 32 features × Shannon entropy < 1ms/batch      │
└─────────────────────────┬────────────────────────────────────┘
                          │ MessagePack WebSocket (95% < JSON)
┌─────────────────────────▼────────────────────────────────────┐
│  AMD MI300X — 192 GB HBM3 — ROCm 7.0                        │
│  IsolationForest(0.45) + Autoencoder(0.55) — F1=0.999        │
│  4,216,327 eventos/segundo — 3.6x vs CPU                     │
└─────────────────────────┬────────────────────────────────────┘
                          │ WebSocket (alertas + MITRE ATT&CK)
┌─────────────────────────▼────────────────────────────────────┐
│  Dashboard SIEM — React + SACITY visual                      │
│  Kynikos AI Orchestrator — Llama 3.1 70B explicación LLM     │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏆 Benchmark AMD MI300X (validado en hardware real)

| Métrica                | CPU (Xeon Platinum)  | GPU (AMD MI300X)         | Speedup    |
|------------------------|---------------------|--------------------------|------------|
| Throughput inferencia  | 1,161,218 ev/s       | **4,216,327 ev/s**       | **3.6x**   |
| Latencia 500K eventos  | 430.6 ms            | **118.6 ms**             | **3.6x**   |
| F1-Score               | —                   | **0.999**                | —          |
| VRAM usada             | —                   | 0.22 GB / **192 GB**     | —          |
| PyTorch                | —                   | **2.9.0 ROCm 7.0**       | —          |

→ Ver [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) para resultados completos.

---

## 🏗️ Estructura del Repo

```
kalpixk/
├── crates/
│   └── kalpixk-core/    # Rust → WASM (5 parsers, 32 features, Shannon entropy)
│       └── src/
│           ├── lib.rs   # parse_and_extract() — punto de entrada WASM
│           ├── event.rs # KalpixkEvent struct
│           ├── features.rs # 32 feature extractor
│           └── parsers.rs  # syslog/json/windows/db2/netflow
├── python/
│   ├── api/
│   │   └── kalpixk_api.py  # FastAPI + WebSocket MessagePack
│   ├── models/
│   │   └── ensemble.py     # IsolationForest(0.45) + Autoencoder(0.55)
│   └── utils/
│       ├── device.py        # AMD ROCm device detection
│       └── metrics.py       # PerformanceMetrics tracker
├── kynikos/
│   ├── orchestrator.py  # Intent detection + enrutamiento
│   ├── telegram_bot.py  # Control remoto desde móvil
│   └── providers.py     # LLM router (AMD vLLM → Groq → Anthropic)
├── datasets/
│   └── generate_dataset.py  # 9 tipos MITRE ATT&CK, CEDIS Cancún
├── skills/
│   ├── kalpixk_status.py   # Estado GPU + modelo
│   ├── train_model.py      # Entrenar + notificar
│   ├── benchmark.py        # Benchmark AMD MI300X
│   ├── detect_now.py       # Detección inmediata
│   └── generate_dataset.py # Generar dataset
├── benchmarks/
│   └── cpu_vs_mi300x.py    # Comparativa CPU vs GPU
├── BENCHMARK_RESULTS.md
└── sesion_amd.sh           # Script de setup para droplet MI300X
```

---

## 🚀 Arranque Rápido

### Sin GPU (desarrollo local)
```bash
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps
cp .env.example .env

# Python backend
cd python && pip install -e ".[dev]"
python skills/generate_dataset.py --size 5000
python skills/train_model.py --samples 1000 --epochs 100
python skills/kalpixk_status.py

# Rust/WASM (requiere rustup + wasm-pack)
cd crates/kalpixk-core
wasm-pack build --target web --release
```

### Con AMD MI300X (producción)
```bash
# Conectar al droplet
ssh root@<DROPLET_IP>
chmod +x sesion_amd.sh && ./sesion_amd.sh

# O manualmente:
make gpu-check    # verificar MI300X
make train        # entrenar modelo
make run          # levantar API + dashboard + bot
```

### Comandos disponibles
```bash
make status          # estado GPU + modelo
make train           # entrenar (1000 muestras, 100 epochs)
make detect          # detección una vez
make detect-loop     # monitoreo continuo 30s
make benchmark       # throughput AMD MI300X
make benchmark-notify # benchmark + notificación Telegram
make test            # suite de tests
```

---

## 🛡️ MITRE ATT&CK Cubiertos

| ID     | Técnica                      | Fuente   | Score |
|--------|------------------------------|----------|-------|
| T1110  | SSH Brute Force              | syslog   | 0.82–0.96 |
| T1110  | DB2 Brute Force              | db2      | 0.80–0.90 |
| T1485  | Data Destruction (DROP TABLE)| db2      | 0.88–0.99 |
| T1005  | Data Exfiltration            | db2      | 0.75–0.90 |
| T1543  | Malicious Service            | windows  | 0.85–0.95 |
| T1136  | Unauthorized Account         | windows  | 0.72–0.87 |
| T1059  | PowerShell Evasion           | windows  | 0.80–0.95 |
| T1078  | Privilege Escalation         | syslog   | 0.78–0.92 |
| T1005  | WMS Export Abuse             | db2      | 0.76–0.89 |

---

## 📊 Dashboard

**Live (offline mode):** https://not-yet-named-user-skipped-to-sp-15105d41.base44.app/KalpixkDashboard

Tabs:
- ⚡ **Tiempo Real** — Entropía Shannon en vivo, alerts, throughput
- ⚙️ **Parsers WASM** — 5 parsers Rust/WASM + feature contract
- 🧬 **32 Features** — Vector activo + ensemble weights
- 📊 **Benchmark** — CPU vs GPU, stack técnico
- 🛡 **MITRE ATT&CK** — 9 técnicas cubiertas, historial
- 🤖 **Kynikos AI** — Orchestrator intents, checklist hackathon

Cuando el droplet esté activo: pega la IP en el campo API URL → conecta automáticamente vía WebSocket MessagePack.

---

## 🏁 Hackathon AMD — lablab.ai Mayo 9-10, 2026

**Por qué Kalpixk gana:**
1. **WASM en ciberseguridad** — <5 proyectos existentes, ninguno con GPU AMD
2. **Benchmark documentado en hardware real** — no simulado
3. **Caso de uso industrial** — CEDIS Cancún 427, ManhattanWMS + IBM DB2
4. **AMD MI300X justificado** — 192 GB necesarios para Llama 70B + Autoencoder simultáneos
5. **Open-source completo** — MIT, reproducible, 5 parsers, 32 features

---

*MIT © 2026 Julián Juárez — Kalpixk: "Porque defender sistemas no debería requerir instalar nada."*
