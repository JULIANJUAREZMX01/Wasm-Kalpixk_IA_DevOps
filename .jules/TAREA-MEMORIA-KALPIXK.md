# Encargo a Jules — consolidación y memoria de Kalpixk

- **Rol:** sentinel · **Fecha:** 2026-11-03 · **Entrega:** un solo PR
- **Ventana:** Jules pasa a solo lectura el 2026-11-11 y se apaga el 2026-12-31

## Lectura obligatoria antes de tocar nada

1. `AGENTS.md` de este repositorio.
2. `docs/agentes/MEMORIA.md` en `JULIANJUAREZMX01/JULIANJUAREZMX01.github.io`.
3. ADR-019 (operación Jules: techo de 3 sesiones, una por repo, `AUTO_CREATE_PR`, sin auto-merge).
4. ADR-006 (estándar AEI: nada de secretos en `PUBLIC_*`, `public/` ni historial de git).

## Objetivo único

Producir `.jules/MEMORIA-EXPORT.md`: la destilación de esta carpeta en filas listas para pegar en `docs/agentes/MEMORIA.md`, con formato `fecha | área | problema | técnica | resultado`.

## Reglas duras

- Solo backend. Prohibido frontend, estilos, componentes visuales, copy y diseño.
- Un solo PR pequeño. Sin dependencias nuevas. Sin cambios de contrato de API. Sin refactors grandes.
- Cada fila necesita evidencia: ruta de archivo, commit o medición antes/después.
- Si una ficha no trae medición, la fila va marcada `sin_medicion`. No se inventan cifras.
- Prohibido tocar `src/lib/app-params.js` y `.github/workflows/`: ahí ya hubo colisiones con 102 sesiones previas.

## Pasos

1. **Inventario.** `sentinel.md`, `bolt.md`, `ordnance_ops.md`, `WASM_COMPILE_TASK.md`, `speedy.md`, `palette.md` (las dos últimas creadas el 3-nov-2026).
2. **Deduplicar.** `bolt.md` repite seis veces la misma lección de `useMemo` y `React.memo` con fechas distintas (2024-04-13, 2024-04-14, 2024-04-16, 2026-04-09, 2026-05-20, 2026-08-14). Se colapsan en una sola fila con la fecha más antigua y la técnica vigente.
3. **Clasificar** por área: seguridad, rendimiento, datos, gobernanza, despliegue.
4. **Redactar** `MEMORIA-EXPORT.md`, máximo 20 filas. Las de `ordnance_ops.md` (v5 a v9) hoy describen vectores y defensas sin cifras: van con `sin_medicion`.
5. **Verificar** cada fila contra el código. Si la técnica ya no existe en el repo, se marca `historico`.
6. **Abrir el PR** con el archivo y una lista de las filas descartadas con su motivo.

## Criterio de aceptación

- `MEMORIA-EXPORT.md` existe, tiene 20 filas o menos, sin duplicados y cada una es verificable.
- No se modificó ningún archivo fuera de `.jules/`.
- El PR explica qué se descartó y por qué.

## Fuera de alcance

Compilar el core WASM (ya está cubierto por `WASM_COMPILE_TASK.md`), montar el dashboard, tocar datos reales de CEDIS, y cualquier tarea de frontend.
