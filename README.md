# KALPIXK — WASM-Native Blue Team SIEM
## [ATLATL-ORDNANCE] Security Information and Event Management

Kalpixk is a production-grade SIEM designed for industrial infrastructure (Chedraui CEDIS Cancún), featuring a zero-install WebAssembly log analysis engine and GPU-accelerated anomaly detection on AMD MI300X.

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          KALPIXK ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LOG SOURCES           BROWSER LAYER              GPU SERVER            │
│  ─────────────         ─────────────────          ──────────────────    │
│                                                                          │
│  /var/log/auth.log ──► [WASM ENGINE]              [AMD MI300X]          │
│  IBM DB2 Audit     ──► Rust → .wasm               192 GB VRAM          │
│  Windows EventLog  ──►   parse_log_line()                               │
│  NetFlow v9        ──►   process_batch()     ──► POST /api/detect       │
│  Manhattan WMS     ──►   features[N,32]           IsolationForest GPU   │
│                          heuristics()             Autoencoder PyTorch    │
│                          ueba_session()           Ensemble (0.45+0.55)  │
│                               │                        │                │
│                               │              score > 0.65?              │
│                               │                   YES ▼                 │
│                               │              POST /api/explain          │
│                               │              Llama 3.1 70B (local)      │
│                               │                        │                │
│                               ◄────────────────────────┘                │
│                          WebSocket alert                                 │
│                          + explanation                                   │
│                               │                                         │
│                    [WASP DASHBOARD]                                      │
│                    React + Zustand                                       │
│                    AlertFeed / ThreatMap                                 │
│                    ATLATL-ORDNANCE UI                                    │
│                                                                          │
│  EDGE NODES (KynicOS)                                                   │
│  RPi 4B × 2 + ESP32-S3 × 1                                             │
│  → Passive network sensors                                              │
│  → Report to NODE_SENTINEL                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 🛡️ The WASM · WASP · WAST Triad

- **WASM**: Rust-based engine compiled to WebAssembly. Handles high-speed parsing and feature extraction directly in the browser.
- **WASP**: React/Vite dashboard. SOC command center with real-time telemetry and zero-install requirement.
- **WAST**: Comprehensive test suite ensuring binary integrity and parser accuracy.

### 🚀 Key Features
- **AMD MI300X Acceleration**: Ensemble detection (Isolation Forest + Autoencoder) optimized for ROCm.
- **Manhattan WMS / IBM DB2 Integration**: Native support for industrial warehouse management system audit logs.
- **Security Guards**: Input validation and memory protection at the WASM binary level.
- **Llama 70B Integration**: Local LLM-powered alert explanation (Zero cloud costs).

### 🛠️ KynicOS Ecosystem
Kalpixk operates as `NODE_SENTINEL` within the KynicOS ecosystem, managing security and audit for industrial operations.

**CLI Usage:**
```bash
sac sentinel audit --scope=full
sac sentinel watch --interface=eth0
```

### 📄 Documentation
- [BENCHMARK.md](./BENCHMARK.md): Performance comparison CPU vs AMD MI300X.
- [DEMO.md](./DEMO.md): Instructions for the live demo and hackathon requirements.

---
*Developed by Julián Juárez (jaja.dev) for AMD Hackathon 2026.*
