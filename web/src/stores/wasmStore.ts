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
