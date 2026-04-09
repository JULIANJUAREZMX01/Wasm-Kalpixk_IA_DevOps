import React from "react"
import ReactDOM from "react-dom/client"
import { Dashboard } from "./pages/Dashboard"
import { initKalpixkWasm } from "./wasm/kalpixk-wasm"

async function bootstrap() {
  try {
    await initKalpixkWasm()
    console.info("[Kalpixk] WASM engine loaded")
  } catch (e) {
    console.warn("[Kalpixk] WASM unavailable — running in demo mode:", e)
  }
  ReactDOM.createRoot(document.getElementById("app")!).render(
    <React.StrictMode>
      <Dashboard />
    </React.StrictMode>
  )
}

bootstrap()
