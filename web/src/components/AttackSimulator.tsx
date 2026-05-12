import { useState, useCallback } from "react";

type SimPhase = "idle" | "normal" | "attack";

interface SimStatus {
  running: boolean;
  phase: SimPhase;
}

const PHASE_CONFIG: Record<SimPhase, { label: string; classes: string; dot: string }> = {
  idle: {
    label: "INACTIVO",
    classes: "bg-gray-100 text-gray-600 border-gray-300",
    dot: "bg-gray-400",
  },
  normal: {
    label: "FASE NORMAL",
    classes: "bg-green-100 text-green-700 border-green-300",
    dot: "bg-green-500",
  },
  attack: {
    label: "🚨 ATAQUE DETECTADO",
    classes: "bg-red-100 text-red-700 border-red-400 animate-pulse",
    dot: "bg-red-600 animate-pulse",
  },
};

const BASE_URL = (import.meta as unknown as { env: Record<string, string> }).env?.VITE_API_URL ?? "";

export default function AttackSimulator() {
  const [status, setStatus] = useState<SimStatus>({ running: false, phase: "idle" });
  const [loading, setLoading] = useState<"start" | "stop" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollStatus = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/api/simulate/status`);
      if (res.ok) {
        const data: SimStatus = await res.json();
        setStatus(data);
        if (data.running) {
          setTimeout(pollStatus, 1500);
        }
      }
    } catch {
      // silent
    }
  }, []);

  const handleStart = async () => {
    setLoading("start");
    setError(null);
    try {
      const res = await fetch(`${BASE_URL}/api/simulate/start`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus({ running: true, phase: "normal" });
      setTimeout(pollStatus, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar");
    } finally {
      setLoading(null);
    }
  };

  const handleStop = async () => {
    setLoading("stop");
    setError(null);
    try {
      const res = await fetch(`${BASE_URL}/api/simulate/stop`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus({ running: false, phase: "idle" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al detener");
    } finally {
      setLoading(null);
    }
  };

  const cfg = PHASE_CONFIG[status.phase];

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-lg">🎯</span>
        <h3 className="font-semibold text-gray-800 dark:text-gray-100">
          Simulador de Ataque
        </h3>
      </div>

      {/* Status Badge */}
      <div
        className={`mb-4 flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium ${cfg.classes}`}
      >
        <span className={`h-2.5 w-2.5 rounded-full ${cfg.dot}`} />
        {cfg.label}
      </div>

      {/* Buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleStart}
          disabled={status.running || loading !== null}
          className="flex-1 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading === "start" ? "Iniciando..." : "🔴 Iniciar Simulación"}
        </button>

        <button
          onClick={handleStop}
          disabled={!status.running || loading !== null}
          className="flex-1 rounded-lg bg-gray-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading === "stop" ? "Deteniendo..." : "⬛ Detener"}
        </button>
      </div>

      {error && (
        <p className="mt-2 text-xs text-red-500">⚠ {error}</p>
      )}

      <p className="mt-3 text-xs text-gray-400">
        Fase normal → 30s → cifrado masivo → spike de entropía → alerta CRITICAL
      </p>
    </div>
  );
}
