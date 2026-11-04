# Memoria compartida de agentes — Wasm-Kalpixk_IA_DevOps

> Una sola bitácora para todos los agentes y herramientas. Léela antes de trabajar; agrega UNA entrada al terminar.
> Formato: fecha · área · problema · técnica · resultado. No dupliques. Esta memoria sobrevive aunque cambie la herramienta.

| Fecha | Área | Problema | Técnica aplicada | Resultado |
|---|---|---|---|---|
| 2026-04-09 | React | Estados derivados (`events.reduce/filter`) recalculados en cada render del dashboard. | Envolver en `useMemo` con `[events]` como dependencia. | Menos CPU con alta frecuencia de logs. |
| 2026-04-13 | React | Listas con índice como `key` remontan todas las filas con cada evento. | Claves estables (timestamp + log) y `React.memo` en la fila. | Sin remontaje O(N). |
| 2025-04-15 | Python/ML | Listas por comprensión en bucles de predicción. | Vectorizar con NumPy (`np.clip`, `np.abs`). | Mayor throughput en MI300X. |
| 2024-05-18 | Seguridad | Ruido adversarial (FGSM/PGD) puede cegar autoencoders. | Auditar rugosidad del tensor (`v7_audit_tensor`) antes de inferir. | Detectable a nivel de bit. |
| 2024-05-22 | Seguridad | JIT spraying y evasión por deduplicación de buffers. | Entropía caótica no lineal y relleno polimórfico (JIT Shield). | Alineación de shellcode interrumpida. |
| 2026-11-04 | Seguridad/API | Subproceso de simulador vulnerable a argumentos maliciosos de backend URL y SSRF. | Validación estricta de esquema (`http`/`https`), regex de caracteres seguros y verificación de ruta de archivo. | Lanzamiento de simulador seguro y sin riesgo de SSRF/inyección. |
