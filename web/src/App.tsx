/**
 * App.tsx — Entry point
 * Monta el engine real (WASM + WebSocket + HTTP fallback) al iniciar.
 */
import Dashboard from "./pages/Dashboard";
import { useKalpixkEngine } from "./hooks/useKalpixkEngine";

export default function App() {
  // Motor real: WASM init + WebSocket backend + HTTP fallback
  // Se ejecuta una sola vez al montar la app.
  useKalpixkEngine();

  return <Dashboard />;
}
