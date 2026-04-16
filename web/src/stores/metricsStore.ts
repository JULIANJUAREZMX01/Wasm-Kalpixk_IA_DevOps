// stores/wasmStore.ts
import { create } from "zustand";

interface WasmStore {
  isLoaded: boolean;
  isDemoMode: boolean;
  version: string;
  eventsPerSecond: number;
  totalParsed: number;
  setLoaded: (loaded: boolean, version: string) => void;
  incrementParsed: (n: number) => void;
  setEps: (eps: number) => void;
}

export const useWasmStore = create<WasmStore>((set) => ({
  isLoaded: false,
  isDemoMode: true,
  version: "—",
  eventsPerSecond: 0,
  totalParsed: 0,
  setLoaded: (loaded, version) =>
    set({ isLoaded: loaded, isDemoMode: !loaded, version }),
  incrementParsed: (n) =>
    set((s) => ({ totalParsed: s.totalParsed + n })),
  setEps: (eps) => set({ eventsPerSecond: eps }),
}));

// stores/metricsStore.ts
import { create as createMetrics } from "zustand";

interface MetricsStore {
  gpuLatencyMs: number;
  gpuThroughput: number;
  cpuThroughput: number;
  speedupRatio: number;
  f1Score: number;
  fpRate: number;
  wasmSizeKb: number;
  vramUsedGb: number;
  vramTotalGb: number;
  gpuLoadPct: number;
  updateMetrics: (m: Partial<Omit<MetricsStore, "updateMetrics">>) => void;
}

export const useMetricsStore = createMetrics<MetricsStore>((set) => ({
  gpuLatencyMs: 34,
  gpuThroughput: 4_216_327,
  cpuThroughput: 1_161_218,
  speedupRatio: 3.6,
  f1Score: 0.999,
  fpRate: 2.3,
  wasmSizeKb: 487,
  vramUsedGb: 14.2,
  vramTotalGb: 192,
  gpuLoadPct: 38,
  updateMetrics: (m) => set(m),
}));
