import { create } from 'zustand'

export interface ParsedEvent {
  event_type: string;
  local_severity: number;
  source: string;
  user: string | null;
  source_type: string;
  timestamp_ms: number;
  raw: string;
}

interface AlertState {
  events: ParsedEvent[];
  wasmReady: boolean;
  wasmVersion: string;
  addEvent: (event: ParsedEvent) => void;
  setWasmReady: (ready: boolean, version?: string) => void;
  clearEvents: () => void;
}

export const useAlertStore = create<AlertState>((set) => ({
  events: [],
  wasmReady: false,
  wasmVersion: 'desconocida',
  addEvent: (event) => set((state) => ({
    events: [event, ...state.events].slice(0, 100)
  })),
  setWasmReady: (ready, version) => set({
    wasmReady: ready,
    wasmVersion: version || 'desconocida'
  }),
  clearEvents: () => set({ events: [] }),
}))
