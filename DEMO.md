# DEMO.md — Kalpixk Live Demo
## AMD Hackathon May 2026 · WASM-native Blue Team SIEM

---

## 🌐 Live Deployments

| Environment | URL | Notes |
|-------------|-----|-------|
| **GitHub Pages** | https://julianjuarezmx01.github.io/Wasm-Kalpixk_IA_DevOps/ | Primary demo |
| **Netlify CDN** | https://kalpixk.netlify.app | WASM headers enabled |
| **Base44 (prototype)** | https://not-yet-named-user-skipped-to-sp-15105d41.base44.app/KalpixkDashboard | Visual reference |

---

## 🎥 Demo Video (3 minutes)

> **[🎬 Watch on YouTube](https://youtu.be/TODO)**

### What the demo shows:

**0:00 – 0:30 — Zero-install setup**
- Open the dashboard URL in a browser — no npm, no Python, no Docker
- F12 → Console → `[Kalpixk] WASM v0.1.0 loaded ✓`
- The Rust/WASM engine running inside the browser

**0:30 – 1:00 — WASM Parser in action**
- Go to "WASM Parsers" tab
- Paste a DB2 audit log: `AUTHID=ROOT SQL=DROP TABLE WMS_USER`
- Click PARSE LOG → instant JSON output with `local_severity: 0.95`
- Switch source type: syslog, windows, netflow — all parse in <5ms

**1:00 – 1:45 — Real-time threat detection**
- Return to Real-Time tab
- Alerts stream in from the WASM engine
- A brute force attempt fires: score 0.91, CRITICAL
- LLM explains in Spanish: _"Se detectó un ataque de fuerza bruta SSH..."_

**1:45 – 2:20 — AMD MI300X Benchmark**
- Switch to Benchmark tab
- CPU: 1,161,218 events/sec
- MI300X GPU: 4,216,327 events/sec → **3.6x faster** (15-23x with 100K events)
- Detection latency: 34ms for 100 events (<50ms target ✅)

**2:20 – 3:00 — MITRE ATT&CK coverage**
- MITRE tab shows techniques detected in session
- T1110 Brute Force × 14, T1048 Exfiltration × 3, T1021 Lateral Movement × 4
- All mapped from the 32-dimensional feature vector

---

## 🔑 Key Technical Differentiators

1. **Zero-install for analysts** — WASM runs in the browser, no dependencies
2. **Real industrial data** — CEDIS Cancún, Manhattan WMS, IBM DB2 (22 monitored queries)
3. **Coherent stack** — Rust/WASM + AMD ROCm + Llama 70B local = one narrative
4. **No API costs** — LLM runs on the same MI300X that runs the models ($0/query)
5. **Privacy by design** — logs never leave the analyst's browser or the on-prem GPU

---

## 🚀 Quick Start (local dev)

```bash
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps

# Backend (no GPU needed)
cd python
KALPIXK_FORCE_CPU=true uv run uvicorn api.main:app --reload
# → http://localhost:8000

# Frontend
cd ../web
npm install
npm run dev
# → http://localhost:5173/Wasm-Kalpixk_IA_DevOps/
```

---

*KynicOS NODE_SENTINEL · operator: jaja.dev · WASM · WASP · WAST*
