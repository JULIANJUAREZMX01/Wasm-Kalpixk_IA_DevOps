// WASM Loader for Browser (Vite compatible)
// @ts-ignore
import * as wasm from "./kalpixk_core.js";

let initialized = false;

export async function initWasm() {
  if (initialized) return wasm;
  // @ts-ignore
  await wasm.default();
  initialized = true;
  return wasm;
}

export function parse_log_line(line: string, log_type: string) {
  if (!initialized) throw new Error("WASM not initialized");
  return wasm.parse_log_line(line, log_type);
}

export function version() {
  return "0.1.0-neural-wasm";
}
