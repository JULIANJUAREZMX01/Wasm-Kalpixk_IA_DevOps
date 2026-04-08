# Kalpixk — Guía Completa del Ecosistema
## Documento de referencia para el desarrollador

> Esta guía documenta el estado real del proyecto, qué hace cada componente,
> por qué existe, y cómo usarlo. Escrita el 8 de Abril de 2026.

---

## Índice

1. [Qué es Kalpixk](#qué-es-kalpixk)
2. [Arquitectura real](#arquitectura-real)
3. [Componentes](#componentes)
4. [Cómo correr el proyecto](#cómo-correr)
5. [Estado actual y pendientes](#estado-actual)
6. [El ecosistema de agentes](#ecosistema)
7. [Roadmap al hackathon](#roadmap)
8. [Glosario técnico](#glosario)

---

## Qué es Kalpixk

Kalpixk (del náhuatl: "guardián/protector") es un SIEM portátil para Blue Team.

**El problema que resuelve:** los SIEMs comerciales (Splunk, Elastic, Wazuh) requieren
instalar 4-20GB de software antes de poder detectar nada. Kalpixk invierte esto:
el motor de parseo y extracción de features corre directamente en el browser del
analista, compilado a WebAssembly, sin instalar nada.

**La diferencia técnica real:**
```
SIEM tradicional:    Logs → Servidor pesado → Dashboard
Kalpixk:            Logs → Browser (WASM) → GPU AMD → Dashboard
                           ↑ Zero install         ↑ 3.6x más rápido
```

**Caso de uso validado:** logs del sistema Manhattan WMS + IBM DB2 del
CEDIS Chedraui Cancún 427 (el proyecto SAC de Julián).

---

## Arquitectura real

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1: EDGE — Rust compilado a WebAssembly                │
│                                                              │
│  Corre EN EL BROWSER del analista.                          │
│  Archivo: crates/kalpixk-core/src/                          │
│                                                              │
│  Lo que hace realmente:                                      │
│  • Parsea logs línea por línea (5 formatos)                 │
│  • Extrae 32 features numéricas por evento                  │
│  • Calcula entropía de Shannon de los strings               │
│  • Detecta patrones heurísticos básicos                     │
│  • Retorna JSON con evento + vector de features             │
│                                                              │
│  Lo que NO hace (limitación honesta):                       │
│  • No mide ciclos de CPU del WASM (requiere wasmtime)       │
│  • 3 de 32 features son siempre 0 (exec_time, instructions) │
└──────────────────────────────────┬──────────────────────────┘
                                   │ HTTP POST /api/detect
                                   │ (vector [N, 32] de features)
┌──────────────────────────────────▼──────────────────────────┐
│  CAPA 2: GPU — Python + AMD ROCm                            │
│                                                              │
│  Corre en el droplet AMD MI300X (192 GB HBM3).              │
│  Archivo: python/ (antes: src/)                              │
│                                                              │
│  Lo que hace realmente:                                      │
│  • IsolationForest (peso 0.45) — detecta outliers           │
│  • Autoencoder 32→16→4→16→32 (peso 0.55) — detección       │
│  • FastAPI con WebSocket para alertas en tiempo real        │
│  • 4.2M eventos/seg de throughput en inferencia GPU         │
│                                                              │
│  Limitación honesta:                                        │
│  • Entrenado con datos sintéticos (no logs CEDIS reales)    │
│  • F1=0.999 es en test set sintético, no producción         │
│  • Requiere el droplet activo ($1.99/hr)                    │
└──────────────────────────────────┬──────────────────────────┘
                                   │ WebSocket (alertas JSON)
┌──────────────────────────────────▼──────────────────────────┐
│  CAPA 3: PRESENTACIÓN — Dashboard + Bots                    │
│                                                              │
│  dashboard/index.html    → Dashboard completo (sin React)   │
│  web/                    → Frontend Vite/TypeScript         │
│  src/channels/           → Bot Telegram + WhatsApp/Twilio   │
│  Base44                  → Dashboard alternativo live       │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes

### crates/kalpixk-core/ — El motor WASM (Rust)

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `lib.rs` | Entry point — exporta funciones a JavaScript | ✅ Funcional |
| `parsers.rs` | 5 parsers: syslog, JSON, Windows Event, DB2, NetFlow | ✅ Funcional |
| `features.rs` | Extracción de 32 features numéricas | ✅ 29/32 reales |
| `event.rs` | Tipos de datos: KalpixkEvent, EventType | ✅ Funcional |
| `heuristics.rs` | Scoring local y correlación de eventos | ✅ Funcional |
| `wasm.rs` | Validación de input del browser | ✅ Funcional |
| `wast.rs` | Framework de tests en WASM | ✅ Funcional |
| `defense_nodes.rs` | 4 nodos MITRE ATT&CK | ✅ Nuevo |
| `motor.zig` | Motor alternativo en Zig | ⚠️ Sin usar |
| `retaliation.rs` | Contramedidas activas | ⚠️ Sin usar / revisar |
| `severity.rs` | Cálculo de severidad separado | ⚠️ Sin usar |

**Nota sobre motor.zig y retaliation.rs:** Si estos archivos están en el workspace
de Cargo (`Cargo.toml` los incluye), deben compilar limpio o CI fallará. Si no
están en el workspace, son archivos sueltos que Rust ignora.

### python/ (antes src/) — Backend AMD ROCm

| Módulo | Propósito |
|--------|-----------|
| `api/main.py` | FastAPI: /api/detect, /api/explain, /ws/events |
| `detection/ensemble.py` | IsolationForest + Autoencoder combinados |
| `detection/autoencoder.py` | Red neuronal 32→16→4→16→32 |
| `utils/device.py` | Detecta AMD ROCm vs NVIDIA vs CPU automáticamente |
| `utils/metrics.py` | Tracker de métricas de rendimiento |
| `training/train_models.py` | Script para entrenar los modelos |

### web/ — Frontend Vite

| Archivo | Propósito |
|---------|-----------|
| `src/main.ts` | Entry point — carga WASM y verifica funcionamiento |
| `src/wasm/index.ts` | Bindings TypeScript para kalpixk-core |
| `src/wasm/kalpixk_core_bg.wasm` | El binario WASM (~245KB) |
| `vite.config.ts` | Configuración con headers COOP/COEP requeridos por WASM |
| `index.html` | Entry HTML del frontend |
| `dist/` | Build de producción (generado por `npm run build`) |

### src/channels/ — Bots de notificación

| Archivo | Canal | Estado |
|---------|-------|--------|
| `telegram_bot.py` | Telegram | Código listo, falta TOKEN |
| `whatsapp_twilio.py` | WhatsApp via Twilio | Código listo, faltan credenciales |

---

## Cómo correr

### Opción A: Solo WASM en browser (sin GPU, sin instalación)

```bash
# Clonar el repo
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps

# Instalar Node.js 20+ si no está instalado
# (Ver: https://nodejs.org/)

# Instalar dependencias del frontend
cd web
npm install

# Iniciar servidor de desarrollo
npm run dev

# Abrir: http://localhost:3000
# El dashboard mostrará:
#   ✅ Motor WASM: kalpixk-core/0.1.0 (contract 1.0.0)
#   ✅ SSH Brute Force → LoginFailure, severity=45%
#   ✅ DROP TABLE DB2  → DbAnomalousQuery, severity=85%
```

### Opción B: Compilar WASM desde Rust (si no hay pkg/ en el repo)

```bash
# Instalar Rust si no está instalado
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Agregar el target WASM
rustup target add wasm32-unknown-unknown

# Instalar wasm-pack
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

# Compilar
cd crates/kalpixk-core
wasm-pack build --target web --release

# Copiar a web/src/wasm/
cp pkg/* ../../web/src/wasm/
```

### Opción C: Backend GPU en AMD MI300X (requiere droplet)

```bash
# 1. Crear droplet en AMD Developer Cloud
# https://amd.digitalocean.com/projects/
# → Create GPU Droplet → MI300X → Quick Start ROCm

# 2. Conectar por SSH
ssh root@<IP_DEL_DROPLET>

# 3. Clonar y configurar
git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps
cd Wasm-Kalpixk_IA_DevOps
cp .env.example .env
# Editar .env con nano o vi

# 4. Correr el script de setup (hace todo automáticamente)
chmod +x sesion_amd.sh
./sesion_amd.sh

# 5. Verificar que la API está activa
curl http://localhost:8000/api/health
# Respuesta esperada: {"status":"healthy","device":"cuda:0"}

# ⚠️ IMPORTANTE: Destruir el droplet cuando termines
# AMD cobra $1.99/hr aunque esté apagado
```

### Opción D: Monitor automático sin GPU

```bash
# En cualquier máquina (PC, servidor, Codespace)
cp .env.example .env
# Editar .env: agregar TELEGRAM_TOKEN y TELEGRAM_CHAT_ID

python kalpixk_monitor.py
# Enviará alertas a Telegram cuando detecte eventos anómalos
```

---

## Estado actual

### Qué funciona hoy (verificado)

- ✅ Motor WASM detectando amenazas en browser (GitHub Codespaces)
- ✅ 3 tipos de amenaza detectados: SSH Brute Force, DROP TABLE DB2, Batch
- ✅ 32 features extraídas por evento (29 con valores reales)
- ✅ Backend Python con modelo entrenado en AMD MI300X
- ✅ Benchmark real: 4.2M eventos/seg, 3.6x speedup
- ✅ Dashboard Base44 en vivo (offline mode + online mode)
- ✅ Bot Telegram KiloKlawKynos activo con 17 skills

### Qué está pendiente

- ❌ web/ y WASM compilado no están en main branch de GitHub (solo en Codespaces)
- ❌ CI de GitHub Actions falla (cargo fmt + hatchling)
- ❌ GitHub Pages no está activado (no hay URL permanente)
- ❌ TELEGRAM_TOKEN del bot de Kalpixk no está configurado
- ❌ Video demo de 3 minutos para el hackathon
- ❌ Registro en lablab.ai para el hackathon Mayo 9

### Deuda técnica conocida

- 3 features de instrumentación WASM son siempre 0 (exec_time_ms, instructions, function_calls)
- F1=0.999 es con datos sintéticos — con logs reales el F1 esperado es 0.85-0.92
- motor.zig y retaliation.rs no se usan — pueden causar confusión
- nanobot-cloud en Render está bloqueado por pago fallido

---

## Ecosistema de agentes

Este es el inventario honesto de todos los agentes activos:

| Agente | Canal | Propósito real | Estado |
|--------|-------|---------------|--------|
| KiloKlawKynos | Telegram | 17 skills: GitHub, Gmail, Drive, exec commands | ✅ Activo |
| SuperAsistenteSacBot (Leo) | Telegram | Concierge KynicOS + MueveCancún | ✅ Activo |
| Asistente_KynicOS_v44 | Telegram | Bot general KynicOS | ✅ Activo (Sprint 2 bloqueado) |
| Base44 Agent | API REST | Dashboard Kalpixk + databases | ✅ Activo |
| Jules (Google) | GitHub | Agente de código autónomo — hace PRs | ✅ Disponible |
| Claude (este chat) | claude.ai | Análisis, generación de código, auditorías | ✅ Activo |

### Cómo usar KiloKlawKynos para tareas automáticas

KiloKlawKynos tiene acceso a tu shell, GitHub, y Gmail. Puedes pedirle:
```
# Ejecutar cargo fmt desde el móvil:
"ejecuta en el Codespace: cargo fmt --all && git push"

# Ver estado del CI:
"revisa las últimas GitHub Actions en Wasm-Kalpixk_IA_DevOps"

# Hacer commit de algo específico:
"en el repositorio Wasm-Kalpixk_IA_DevOps, agrega kalpixk_monitor.py al main"
```

---

## Roadmap al hackathon

### Mayo 9-10, 2026 — AMD Developer Hackathon (lablab.ai)
**Premio: $10,000 + AMD Radeon AI PRO R9700**
**Créditos AMD restantes: ~$46 (vencen Mayo 3)**

```
Semana del 8-12 Abril (sin GPU, $0)
├── cargo fmt --all → git push          [30 min]
├── pyproject.toml corregido → push     [10 min]
├── git push de web/ con WASM           [15 min]
├── Activar GitHub Pages                 [5 min]
├── Registrarse en lablab.ai            [5 min]
└── TELEGRAM_TOKEN en .env              [10 min]

Semana del 13-19 Abril (sin GPU, $0)
├── kalpixk_real_features.py → push    [ya generado]
├── BENCHMARK_RESULTS.md honesto       [ya generado]
├── kalpixk_monitor.py → push          [ya generado]
└── Resolver motor.zig/retaliation.rs  [30 min]

Semana del 20-30 Abril (1 sesión GPU ~$4)
├── Recrear droplet AMD
├── Benchmark end-to-end con logs reales
└── Grabar video demo 3 minutos

Mayo 1-8 (submission)
├── README final con screenshots
├── Video subido a YouTube (unlisted)
└── Submission en lablab.ai
    ├── URL del repo
    ├── URL de GitHub Pages
    └── Link al video demo
```

---

## Glosario técnico

**WASM (WebAssembly):** Formato binario que corre en browsers modernos.
El código Rust se compila a .wasm con `wasm-pack`. El resultado corre
en el browser sin instalar nada. Es la tecnología central de Kalpixk.

**wasm-pack:** Herramienta oficial de Rust que compila código Rust a WASM
y genera automáticamente los bindings de JavaScript/TypeScript.

**Vite:** Build tool de JavaScript que sabe cómo servir archivos .wasm
con los headers de seguridad correctos (COOP/COEP) que los browsers exigen.

**cargo fmt:** Formateador automático de código Rust. Hace que todo el
código tenga el mismo estilo. El CI lo ejecuta con --check para verificar.

**hatchling:** Build backend de Python (reemplaza setuptools). Necesita
saber qué directorios contienen el código del paquete.

**ROCm:** Plataforma de cómputo GPU de AMD (equivalente a CUDA de NVIDIA).
PyTorch tiene soporte ROCm desde la versión 2.0.

**AMD MI300X:** GPU de AMD con 192 GB de VRAM HBM3. La usamos en el
AMD Developer Cloud ($1.99/hr). Confirmamos 4.2M eventos/seg de throughput.

**GitHub Pages:** Hosting gratuito de sitios estáticos en GitHub.
La URL es github.io/nombre-repo. Se activa en Settings → Pages.

**IsolationForest:** Algoritmo de detección de anomalías no supervisado.
No necesita datos etiquetados — aprende qué es "normal" y detecta lo diferente.

**Autoencoder:** Red neuronal que aprende a comprimir y reconstruir datos normales.
Si no puede reconstruir bien un evento → ese evento es anómalo.

**MITRE ATT&CK:** Framework de ciberseguridad que cataloga técnicas de ataque.
Kalpixk mapea sus detecciones a los IDs de MITRE (T1110, T1485, T1059, etc.)

**SIEM (Security Information and Event Management):** Sistema que centraliza
y analiza logs de seguridad. Kalpixk es un SIEM portátil y ligero.

**Blue Team:** Equipo de defensa en ciberseguridad (vs Red Team que ataca).
Kalpixk es una herramienta para Blue Teams.

**Manhattan WMS:** Sistema de gestión de almacén (Warehouse Management System)
usado en CEDIS Chedraui Cancún 427. Genera logs de DB2 que Kalpixk parsea.
