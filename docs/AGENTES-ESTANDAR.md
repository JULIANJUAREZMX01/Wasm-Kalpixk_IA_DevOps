# Agentes en Kalpixk — llave de Jules y estándar

- **Fecha:** 2026-11-03 · **Estándar canónico:** `docs/ESTANDAR-REPOS.md` en `JULIANJUAREZMX01/JULIANJUAREZMX01.github.io`

## 1. Reglas que aplican aquí

| ID | Regla |
| --- | --- |
| AGT-01 | `AGENTS.md` con las ocho secciones fijas (ya cumple) |
| AGT-03 | Un máximo de un PR abierto por agente. Sin auto-merge. **Hoy no cumple: 30 PRs abiertos** |
| AGT-04 | Cada aprendizaje entra en `docs/agentes/MEMORIA.md` con medición, no en `.jules` suelto |
| AGT-05 | `.jules/` solo guarda fichas por persona: `sentinel`, `bolt`, `speedy`, `palette` |
| SEC-02 | Las llaves viven en GitHub Actions secrets, nunca en el código |

## 2. Llave de Jules en este repositorio

- **Nombre del secreto:** `JULES_API_KEY`
- **Dónde vive:** GitHub Actions secrets de este repo y gestor de secretos del agente. Aplicado el 2026-11-03 (respuesta 201 de GitHub).
- **Cómo se usa:** `${{ secrets.JULES_API_KEY }}` en el workflow y `JULES_API_KEY` en el `.env` local. Nunca en un archivo versionado.
- **Formato:** prefijo `AQ.` y 53 caracteres. Si mide 50, le falta el prefijo y la API responde 401.
- **Rotación:** nuevo valor en el gestor, propagar con `githubSetSecret`, revocar el anterior.

## 3. Tarea de migración pendiente

La ficha `.jules/TAREA-MEMORIA-KALPIXK.md` está lista para despachar a Jules en cuanto el repositorio no tenga una sesión activa. El despachador `julesDispatch` aplica el techo de 3 sesiones y una por repo (ADR-019).
