# 🛡️ Kalpixk Release Checklist — Hackathon AMD Mayo 9-10, 2026

## ✅ Pre-Release (antes del hackathon)

### 📋 Documentación
- [ ] README.md actualizado (arquitectura + benchmarks)
- [ ] BENCHMARK_RESULTS.md con métricas reales MI300X
- [ ] LICENSE (MIT)
- [ ] `sesion_amd.sh` verificado en droplet real
- [ ] Executive summary (1 página)

### 🧪 Testing
- [ ] `pytest tests/` pasa 100%
- [ ] `make test` funcional
- [ ] Tests cubierto:
  - [ ] test_detector_init
  - [ ] test_autoencoder_shape
  - [ ] test_monitor_metrics
  - [ ] test_baseline_generation
  - [ ] test_simulate_anomalies
  - [ ] test_train
  - [ ] test_evaluate
  - [ ] test_save_load

### 🤖 CI/CD
- [ ] GitHub Actions configurado
- [ ] `make test-ci` genera XML
- [ ] Badge: Build passing
- [ ] Badge: Tests coverage (opcional)

### 📦 Build & Compile
- [ ] `make setup` funciona (pip install)
- [ ] `wasm-pack build --target web --release` compila
- [ ] `docker build` genera imagen
- [ ] WASM artifact en `pkg/`

### 🎯 Modelos
- [ ] `models/kalpixk_v2.pt` entrenado y/commitado
- [ ] Modelo carga correctamente
- [ ] F1-score ≥ 0.999 validado

### 🔧 Config
- [ ] `.env.example` completo
- [ ] `.env` configurado (o instruicciones claras)
- [ ] TELEGRAM_BOT_TOKEN set
- [ ] GROQ_API_KEY set (backup LLM)

### 🚀 Demo Prep
- [ ] Dashboard accesible (local o deployed)
- [ ] `make status` muestra GPU
- [ ] `make detect` funciona
- [ ] Bot Telegram responde a /status
- [ ] Screenshots listos para presentación

---

## 🎬 Día del Hackathon

### ⏱️ Setup (≤ 5 min)
```bash
# En droplet MI300X
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps
chmod +x sesion_amd.sh && ./sesion_amd.sh
```

### 🏃 Quick Demo Flow
```bash
# 1. Verificar GPU
make gpu-check

# 2. Entrenar (o usar pre-entrenado)
make train

# 3. Detectar
make detect

# 4. Benchmark
make benchmark

# 5. Notificar a Telegram
make benchmark-notify
```

### 📱 Bot Commands
| Comando | Función |
|---------|---------|
| /status | Estado GPU + modelo |
| /detect | Detección única |
| /benchmark | Throughput GPU |
| /help | Help |

---

## 🏆 Presentation Checklist

### Slides
- [ ] Problema (SIEM reactivo → proactivo)
- [ ] Arquitectura (3 capas)
- [ ] Benchmark real (no simulado)
- [ ] Diferenciador: WASM + AMD
- [ ] Demo live (ops!)
- [ ] MITRE ATT&CK coverage
- [ ] Próximos pasos

### Demo Script
1. **Intro** (30s): ¿Qué es Kalpixk?
2. **Demo** (2min): 
   - Mostrar dashboard
   - `make detect` en vivo
   - Alerta en Telegram
3. **Benchmark** (1min):
   - `make benchmark`
   - Comparar con CPU
4. **Cierre** (30s): ¿Por qué gana?

---

## 🚨 Si algo falla...

| Problema | Solución |
|---------|----------|
| No detecta GPU | `make gpu-check`, verificar ROCm |
| Tests fallan | `make test` localmente |
| WASM no compila | `rustup + wasm-pack` |
| Bot no responde | Verificar TOKEN en .env |
| Dashboard no carga | `docker-compose up -d` |

---

## ✅ Git Tags
```bash
# Al hacer release
git tag -a v1.0.0-hackathon -m "Kalpixk AMD Hackathon Release"
git push origin v1.0.0-hackathon
```

---

**Última actualización:** 2026-04-06
**Maintainer:** Julian Alexander Juárez Alvarado