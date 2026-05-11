/**
 * App.tsx — Entry point
 * Monta el engine real (WASM + WebSocket + HTTP fallback) al iniciar.
 */
import Dashboard from "./pages/Dashboard";
import { useKalpixkEngine } from "./hooks/useKalpixkEngine";
import { useAlertHistory } from "./hooks/useAlertHistory";

export default function App() {
  // Motor real: WASM init + WebSocket backend + HTTP fallback
  useKalpixkEngine();
  // Carga histórico de alertas desde /api/alerts (no-op si endpoint no existe aún)
  useAlertHistory();

  return <Dashboard />;
}
