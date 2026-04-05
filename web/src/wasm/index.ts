/**
 * Kalpixk WASM entry point
 * Importa el módulo compilado por wasm-pack desde crates/kalpixk-core/pkg/
 */
import init, {
  version,
  parse_log_line,
  process_batch,
  compute_ueba_features,
  get_feature_names,
  health_check,
} from "../../../crates/kalpixk-core/pkg/kalpixk_core.js";

let initialized = false;

/** Inicializa el motor WASM. Debe llamarse antes de cualquier función. */
export async function initWasm(): Promise<void> {
  if (initialized) return;
  await init();
  initialized = true;
  console.log(`[Kalpixk] Motor WASM listo: ${version()}`);
}

export { version, parse_log_line, process_batch, compute_ueba_features, get_feature_names, health_check };
