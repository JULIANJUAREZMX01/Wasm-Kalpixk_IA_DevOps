import React from "react"
import ReactDOM from "react-dom/client"
import { Dashboard } from "./pages/Dashboard"
import { initKalpixkWasm } from "./wasm/kalpixk-wasm"

async function bootstrap() {
  try {
    // [ATLATL-ORDNANCE] Bootstrap Sequence
    await initKalpixkWasm()
  } catch (e) {
    console.warn("[Kalpixk] Running in degraded mode (WASM engine failed to load).", e)
  }

  const rootElement = document.getElementById("app");
  if (!rootElement) throw new Error("Failed to find the root element");

  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <Dashboard />
    </React.StrictMode>
  )
}

bootstrap()
