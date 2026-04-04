# 🔬 Wasm-Kalpixk_IA_DevOps

> Motor de detección de anomalías en runtimes WASM acelerado por AMD MI300X

[![AMD MI300X](https://img.shields.io/badge/GPU-AMD%20MI300X-ED1C24)](https://developer.amd.com)
[![ROCm](https://img.shields.io/badge/ROCm-7.0-FF6600)](https://rocm.docs.amd.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.9--ROCm-EE4C2C)](https://pytorch.org)
[![Hackathon AMD](https://img.shields.io/badge/AMD%20Hackathon-Mayo%202026-blue)](https://developer.amd.com)

## ¿Qué hace?

Kalpixk (del náhuatl: *"el que cuida"*) monitorea el comportamiento de módulos WebAssembly en tiempo real y detecta anomalías usando un autoencoder entrenado en PyTorch sobre GPU AMD.

## Arquitectura

```
[WASM Runtime] → [WasmMonitor] → [AnomalyDetector] → [API REST]
                  (métricas)      (autoencoder GPU)    (alertas)
```

**10 features monitoreadas por módulo WASM:**
- CPU usage, Memory MB, Execution time
- Instructions, Memory pages, Function calls
- Traps, Imports, Exports, Heap usage

## Setup rápido

```bash
# 1. Clonar
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps

# 2. Configurar entorno
cp .env.example .env
pip install -r requirements.txt

# 3. Verificar GPU
make gpu-check

# 4. Correr tests
make test

# 5. Benchmark MI300X
make benchmark

# 6. Levantar API
make api
```

## En el droplet AMD (cuando esté encendido)

```bash
# Arrancar contenedor PyTorch/ROCm
docker start rocm
docker exec -it rocm /bin/bash

# Dentro del contenedor
cd /workspace/kalpixk
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps .
make gpu-check
make test
make benchmark
```

## Estructura

```
src/
  detector/      ← AnomalyDetector (autoencoder PyTorch)
  runtime/       ← WasmRuntimeMonitor (captura métricas)
  api/           ← FastAPI REST server
config/
  llm_config.yaml  ← AMD-first LLM router
benchmarks/
  benchmark_gpu.py ← throughput en MI300X
tests/
  test_detector.py ← test suite
models/          ← modelos entrenados (.pt)
docs/            ← documentación técnica
```

## Hardware objetivo

| Spec | Valor |
|------|-------|
| GPU | AMD MI300X |
| VRAM | 205.8 GB |
| ROCm | 7.0.0 |
| PyTorch | 2.9.0+rocm7.0 |

## Integración con KynicOS

Kalpixk es un módulo de KynicOS. Cuando el motor detecta una anomalía,
notifica via Telegram (bot Leo) y registra en el sistema de memoria de KynicOS.

---

*Proyecto para el AMD Developer Hackathon — Mayo 2026*  
*by Julián Juárez (JULIANJUAREZMX01)*
