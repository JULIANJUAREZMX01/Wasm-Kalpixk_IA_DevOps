import init, { parse_log_line, process_batch, version, health_check } from '../../../crates/kalpixk-core/pkg/kalpixk_core.js'

let initialized = false

export async function initWasm(): Promise<void> {
  if (initialized) return

  if (typeof window === 'undefined' || (typeof process !== 'undefined' && process.env.NODE_ENV === 'test')) {
    const fs = await import('fs');
    const path = await import('path');
    const wasmPath = path.resolve(__dirname, '../../../crates/kalpixk-core/pkg/kalpixk_core_bg.wasm');
    const buffer = fs.readFileSync(wasmPath);
    const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
    await init(arrayBuffer);
  } else {
    await init();
  }

  initialized = true
  console.log(`[Kalpixk] WASM motor v${version()} listo`)
}

export { parse_log_line, process_batch, version, health_check }
