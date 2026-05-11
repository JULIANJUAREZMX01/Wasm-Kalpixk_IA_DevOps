/**
 * useAlertHistory.ts
 * Carga el histórico de alertas desde GET /api/alerts cuando el backend esté disponible.
 * Se integra con el alertStore existente — no rompe nada si el endpoint no existe aún.
 */
import { useEffect, useRef } from "react";
import { useAlertStore, KalpixkAlert } from "../stores/alertStore";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

interface ApiAlert {
  id: number;
  ts: string;
  ip?: string;
  anomaly_score: number;
  event_type?: string;
  severity?: string;
  technique?: string;
  source?: string;
}

function mapApiAlert(a: ApiAlert, idx: number): KalpixkAlert {
  const score = a.anomaly_score ?? 0;
  const severity = a.severity ?? (score >= 0.85 ? "CRITICAL" : score >= 0.5 ? "HIGH" : "LOW");
  return {
    id: a.id ?? idx,
    ts: new Date(a.ts),
    ip: a.ip ?? "127.0.0.1",
    geo: "LOCAL",
    msg: `[${severity}] ${a.technique ?? a.event_type ?? "Anomaly detected"} — score ${score.toFixed(3)}`,
    score,
    src: a.source ?? "agent",
    eventType: a.event_type ?? "ANOMALY",
  };
}

export function useAlertHistory() {
  const addAlert = useAlertStore((s) => s.addAlert);
  const loaded = useRef(false);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;

    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API_URL}/api/alerts?limit=50`, {
          headers: { "x-api-key": API_KEY },
        });
        if (!res.ok) return; // backend no tiene el endpoint aún — silencioso
        const data = await res.json();
        const alerts: ApiAlert[] = data.alerts ?? [];
        // Cargar en orden cronológico inverso (más reciente primero)
        alerts
          .sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime())
          .slice(0, 50)
          .forEach((a, i) => addAlert(mapApiAlert(a, i)));
      } catch {
        // Backend offline — no hace nada, el engine maneja el demo mode
      }
    };

    fetchHistory();
  }, [addAlert]);
}
