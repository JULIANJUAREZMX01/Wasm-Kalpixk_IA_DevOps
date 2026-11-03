# AGENTS.md — Wasm-Kalpixk_IA_DevOps

> Reglas para cualquier agente de IA que trabaje en este repositorio (Jules, Claude, Copilot, Gemini, Codex, Antigravity).
> Fuente única: este archivo. Los demás (`CLAUDE.md`, `GEMINI.md`, `.cursorrules`) solo apuntan aquí.
> Dueño: Julián Juárez (@JAJA.DEV) · Marca de servicios: UNT Tecnologías Computacionales Cancún.

## 1. Qué es este repo
- **Perfil:** SIEM Blue Team nativo en WebAssembly, API en Python, frontend React, optimizado para un WMS de CEDIS.
- **Stack:** Rust/Zig→WASM, Python (numpy), React/Vite, Docker
- **Comandos verificados:**
  - `cargo fmt --check`
  - `cargo test`
  - `pip install -r requirements.txt`
  - `pytest -q`
  - `npm ci && npm run build`

## 2. Misión de los agentes aquí
Mantener las 32 features de detección y el rendimiento declarado (4.2M ev/s) **solo si se reproduce con benchmark**. Seguridad defensiva únicamente: nada ofensivo. Lee `.jules/sentinel.md` y `.jules/bolt.md` (aprendizajes ya migrados a la memoria compartida).

## 3. Reglas inquebrantables (Ley Kynikos)
1. **Un cambio, una intención.** Un PR hace una sola cosa y se explica en una frase.
2. **Nada de PRs duplicados.** Antes de abrir uno, lista los PRs abiertos (`gh pr list`) y busca el tema. Si ya existe, comenta ahí en vez de abrir otro.
3. **Máximo 1 PR abierto por agente a la vez.** Si hay uno sin revisar, no abras otro.
4. **Sin secretos en código ni en logs.** Variables de entorno solo desde `.env.example` documentado; nunca valores reales.
5. **No toques** `package.json`, `tsconfig.json`, lockfiles ni CI sin instrucción explícita.
6. **Medir antes de optimizar.** Una optimización sin medición previa se rechaza.
7. **Pruebas verdes o no hay PR.** Si una prueba falla, revierte y explica.
8. **Humano decide.** Los agentes proponen; Julián aprueba. Nunca hagas merge a `main` por tu cuenta.
9. **Sin dependencias nuevas** sin pedir permiso en el PR.
10. **Honestidad:** separa hecho verificado de suposición. Si no sabes, dilo.

## 4. Memoria compartida (obligatoria)
Antes de empezar lee `docs/agentes/MEMORIA.md`. Al terminar, agrega UNA entrada con: fecha, qué aprendiste, qué evitar. No dupliques entradas existentes. Esto reemplaza la memoria propia de cada herramienta, que puede desaparecer.

## 5. Documentación
- Toda decisión no trivial va como ADR en `docs/adr/` (Contexto / Decisión / Consecuencias).
- Los cambios de rutina se registran en `docs/CALENDARIO.md` si existe.

## 6. Tono
Español claro y directo en PRs, commits y comentarios. Commits atómicos con prefijo (`fix:`, `feat:`, `docs:`, `perf:`, `sec:`). Sin relleno, sin exageración.

## 7. Personas (turnos)
- **Sentinel** (semanal): endurecimiento defensivo.
- **Bolt** (semanal): rendimiento con benchmark previo y posterior.
