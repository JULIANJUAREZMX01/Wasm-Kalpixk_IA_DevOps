import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { useWasmStore } from "./stores/wasmStore";

async function bootstrap() {
  // Attempt to load WASM engine
  // If it fails (no .wasm file yet), the app still runs in demo mode
  try {
    const { initKalpixkWasm } = await import("./wasm/kalpixk-wasm");
    await initKalpixkWasm();
    useWasmStore.getState().setLoaded(true, "0.1.0");
    console.info("[Kalpixk] WASM engine v0.1.0 loaded ✓");
  } catch (e) {
    console.warn("[Kalpixk] WASM unavailable — running in demo mode:", e);
    useWasmStore.getState().setLoaded(false, "demo");
  }

  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

bootstrap();
