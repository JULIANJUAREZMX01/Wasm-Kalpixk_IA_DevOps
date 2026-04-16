// stores/alertStore.ts
import { create } from "zustand";

export interface KalpixkAlert {
  id: number;
  ts: Date;
  ip: string;
  geo: string;
  msg: string;
  score: number;
  src: string;
  eventType: string;
}

interface AlertStore {
  alerts: KalpixkAlert[];
  criticalCount: number;
  isConnected: boolean;
  totalDetected: number;
  addAlert: (a: KalpixkAlert) => void;
  setConnected: (v: boolean) => void;
  clearAlerts: () => void;
}

export const useAlertStore = create<AlertStore>((set) => ({
  alerts: [],
  criticalCount: 0,
  isConnected: false,
  totalDetected: 0,
  addAlert: (a) =>
    set((s) => ({
      alerts: [a, ...s.alerts].slice(0, 50),
      criticalCount: s.criticalCount + (a.score >= 0.85 ? 1 : 0),
      totalDetected: s.totalDetected + 1,
    })),
  setConnected: (v) => set({ isConnected: v }),
  clearAlerts: () => set({ alerts: [], criticalCount: 0 }),
}));
