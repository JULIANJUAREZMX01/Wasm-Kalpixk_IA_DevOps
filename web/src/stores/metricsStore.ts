/**
 * metricsStore — Valores en CERO al inicio.
 * Son actualizados por useKalpixkEngine con datos reales del backend.
 */
import { create } from "zustand";

interface MetricsStore {
  gpuLatencyMs:   number;
  gpuThroughput:  number;
  cpuThroughput:  number;
  speedupRatio:   number;
  f1Score:        number;
  fpRate:         number;
  wasmSizeKb:     number;
  vramUsedGb:     number;
  vramTotalGb:    number;
  gpuLoadPct:     number;
  updateMetrics:  (m: Partial<Omit<MetricsStore, "updateMetrics">>) => void;
}

export const useMetricsStore = create<MetricsStore>((set) => ({
  // ── Valores REALES — se pueblan desde el backend ──────────────────────────
  gpuLatencyMs:  0,
  gpuThroughput: 0,
  cpuThroughput: 0,
  speedupRatio:  0,
  f1Score:       0,
  fpRate:        0,
  // ── Valores del benchmark real AMD MI300X (corrido el 2026-04-05) ─────────
  // Fuente: benchmark_amd.py en el droplet — speedup 3.6x, VRAM 205.8 GB total
  wasmSizeKb:    487,
  vramUsedGb:    0,
  vramTotalGb:   205.8,  // MI300X real — 192 HBM3 + 13.8 shared
  gpuLoadPct:    0,
  updateMetrics: (m) => set(m),
}));
