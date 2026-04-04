# Arquitectura Wasm-Kalpixk

## Diagrama de flujo

```
[Módulo WASM]
     │
     ▼
[WasmRuntimeMonitor]
  - cpu_usage
  - memory_mb  
  - exec_time_ms
  - instructions
  - memory_pages
  - function_calls
  - traps
  - imports / exports
  - heap_usage
     │
     ▼
[AnomalyDetector — KalpixkAutoencoder]
  Encoder: 10 → 16 → 8 → 3
  Decoder: 3 → 8 → 16 → 10
  Pérdida: MSELoss (reconstrucción)
  Threshold: 0.5 (ajustable)
     │
     ▼
[FastAPI REST]
  GET  /health      ← estado del detector
  GET  /metrics     ← métricas actuales + detección
  POST /detect      ← detectar en métricas externas
  GET  /simulate/X  ← simular anomalía para testing
     │
     ▼
[Notificaciones]
  Telegram → @SuperAsistenteSacBot
  Slack    → #kalpixk-alerts
```

## Decisiones técnicas

### ¿Por qué autoencoder?
- Aprendizaje no supervisado: no necesita ejemplos etiquetados de anomalías
- Entrena solo con tráfico normal → detecta desviaciones automáticamente
- Eficiente en GPU: batch inference en miles de módulos simultáneos

### ¿Por qué AMD MI300X?
- 205.8 GB VRAM unificada: puede cargar modelos LLM + detector simultáneamente
- ROCm 7.0: compatibilidad nativa con PyTorch sin capas de abstracción
- Costo 0 durante el hackathon (créditos AMD Developer Cloud)

### Integración WASM (próxima fase)
- wasmtime con `--profile` para métricas de instrucciones reales
- Hooks en el runtime para captura de function_calls y traps
- Instrumentación automática vía WASM component model
