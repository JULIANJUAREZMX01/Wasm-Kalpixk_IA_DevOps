/**
 * Kalpixk WASM entry point
 * ATLATL-ORDNANCE: Bridge ofensivo para el dashboard.
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
} from "../../../crates/kalpixk-core/pkg/kalpixk_core.js";

let initialized = false;

/** Inicializa el motor WASM. Debe llamarse antes de cualquier función. */
export async function initWasm(): Promise<void> {
  if (initialized) return;
  await init();
  initialized = true;
  console.log(`[Kalpixk] Motor WASM listo (MODO OFENSIVO): ${version()}`);
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
