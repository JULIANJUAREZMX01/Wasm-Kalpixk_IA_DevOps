# Kalpixk SIEM 🛡️ ![CI Status](https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps/actions/workflows/main.yml/badge.svg)

**Neural Threat Detection at Ultra-Scale (4.2M ev/s) using WASM Edge & AMD MI300X.**

Kalpixk is a high-performance Security Information and Event Management (SIEM) engine designed for the protection of critical infrastructure, specifically optimized for the **Manhattan WMS at CEDIS Cancún 427**. It leverages WebAssembly (WASM) for efficient edge parsing and AMD MI300X GPUs for massive neural inference throughput.

> **Status 2026-11-03 · AMBER.** Code stable and actively developed. Deployment is in transition: Render and Vercel services are suspended for billing, and every public surface is moving to GitHub Pages under the AEI standard (ADR-006). **30 pull requests are open**, above this repository's one-PR-per-agent rule. Read `AGENTS.md` before opening anything.

## ⚡ Quick Links
- **Live Command Center**: https://julianjuarezmx01.github.io/Wasm-Kalpixk_IA_DevOps/dashboard/index.html
- **Benchmark Results**: `BENCHMARK_RESULTS.md`
- **Architecture**: `docs/ARQUITECTURA.md`
- **Agent rules (source of truth)**: `AGENTS.md`
- **Decision records (ADR)**: https://github.com/JULIANJUAREZMX01/JULIANJUAREZMX01.github.io/tree/main/docs/adr
- **Shared agent memory**: https://github.com/JULIANJUAREZMX01/JULIANJUAREZMX01.github.io/blob/main/docs/agentes/MEMORIA.md

## ⚡ Key Features
- **Neural Ensemble:** Isolation Forest plus Autoencoders for zero-day anomaly detection.
- **WASM-Edge Core:** Log parsing and feature extraction at near-native speed in any environment.
- **AMD MI300X Accelerated:** Optimized for ROCm, measured above **4.2 Million events/sec**.
- **MITRE ATT&CK Mapping:** Automatic mapping of detected vectors to the framework (T1110, T1485, T1059, and others).
- **Zero-Install Dashboard:** Static SIEM dashboard served from GitHub Pages, no server required for basic analysis.

## 📊 Performance at a Glance
| Metric | Result |
|--------|--------|
| Throughput | 4,285,120 ev/s |
| Speedup | 3.6x vs optimized CPU |
| F1-Score | 0.999 |
| Load profile | 15/15 scenario tests passing |

> Cloud credit balances are no longer tracked in this file. They change weekly; the 6-hour monitor reports them.

## 🛠️ Getting Started
```bash
# Clone the repository
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps

# Build the WASM core (requires Rust + wasm-pack)
make wasm-build

# Run the Python backend
pip install -r requirements.txt
python main.py
```

## 🧭 Operating Model (2026)
- **Static first.** Public front ends ship to GitHub Pages with `output: static`, a `pages.yml` workflow and a 200 smoke gate (ADR-006).
- **No secrets in the repo.** Nothing in `PUBLIC_*`, `public/` or git history; real values live in provider variables only.
- **Base44 is legacy** until parity is reached, component by component.
- **Agents follow `AGENTS.md`**, not their own console: one open PR per agent, no automatic merge.
- **Jules winds down.** Google's Jules becomes read-only on 2026-11-11 and shuts down 2026-12-31; its operating knowledge moves to `AGENTS.md` and the shared `MEMORIA.md`.
- **Monitoring.** The DACC and RC Caribe monitors snapshot repos, CI, projects and credential-related email every 6 hours.

## 🛡️ The Mission
Kalpixk was built to solve the "Log Tsunami" problem in industrial logistics centers. By offloading parsing to WASM and inference to AMD GPUs, it delivers a defense-in-depth solution that is both faster and more cost-effective than traditional JVM-based SIEMs.

---
*Developed by Julian Juarez. Originally built for the AMD AI Hackathon; maintained as the reference repository where agent workflows are tested first.*
