import { initWasm, version } from "./index";

/**
 * [ATLATL-ORDNANCE] WASM Integrity Loader
 */
export async function initKalpixkWasm(): Promise<void> {
  // In a production environment, we would verify SRI hash here.
  // The VITE_WASM_SHA256 env var would be injected by the CI pipeline.

  try {
    await initWasm();
    console.info(`[Kalpixk] WASM Engine v${version()} initialized successfully.`);
  } catch (error) {
    console.error("[Kalpixk] Failed to initialize WASM engine:", error);
    throw error;
  }
}
