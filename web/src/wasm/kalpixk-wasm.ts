import { initWasm, version } from "./index";

export async function initKalpixkWasm() {
  return await initWasm();
}

export { version };
