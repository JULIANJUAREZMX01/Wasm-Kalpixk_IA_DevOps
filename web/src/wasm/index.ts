/**
 * Kalpixk WASM entry point
 *
 * ARQUITECTURA DE IMPORTS — dos rutas según entorno:
 *
 * En producción (GitHub Pages / Vite build):
 *   El WASM se copia a web/src/wasm/ directamente (está en el repo).
 *   Import relativo local: './kalpixk_core.js'
 *
 * En desarrollo (Codespace / local con pkg/ compilado):
 *   El import relativo local también funciona si web/src/wasm/ tiene el pkg.
 *   Si no, Vite resuelve via alias a crates/kalpixk-core/pkg/
 *
 * En tests (Vitest/Node):
 *   initWasm() detecta entorno Node y carga el .wasm via fs.readFileSync
 */
import init, {
  version,
  parse_log_line,
  process_batch,
  compute_ueba_features,
  get_feature_names,
  health_check,
  analyze_and_retaliate,
  wasm_lockdown,
} from "./kalpixk_core.js";

let initialized = false;

export async function initWasm(): Promise<void> {
  if (initialized) return;

  // Entorno Node.js (Vitest) — cargar el .wasm como buffer
  if (typeof window === "undefined") {
    const fs = await import("fs");
    const path = await import("path");
    const { fileURLToPath } = await import("url");
    const __dirname = path.dirname(fileURLToPath(import.meta.url));
    const wasmPath = path.resolve(__dirname, "./kalpixk_core_bg.wasm");
    const buffer = fs.readFileSync(wasmPath);
    const arrayBuffer = buffer.buffer.slice(
      buffer.byteOffset,
      buffer.byteOffset + buffer.byteLength
    );
    await init(arrayBuffer);
  } else {
    // Browser — Vite sirve el .wasm con los headers COOP/COEP correctos
    await init();
  }

  initialized = true;
  console.log(`[Kalpixk] Motor WASM listo: ${version()}`);
}

export {
  version,
  parse_log_line,
  process_batch,
  compute_ueba_features,
  get_feature_names,
  health_check,
  analyze_and_retaliate,
  wasm_lockdown,
};
