import { defineConfig } from "vitest/config";
import wasm from "vite-plugin-wasm";
import topLevelAwait from "vite-plugin-top-level-await";

/**
 * vitest.config.ts
 *
 * Configuración de tests para el motor WASM de Kalpixk.
 *
 * ENTORNO: Node.js (jsdom no soporta WebAssembly bien)
 * Los tests usan 'node' environment y el polyfill en index.ts
 * carga el .wasm via fs.readFileSync para evitar dependencia del browser.
 *
 * Por qué NO usamos jsdom:
 *   jsdom no implementa WebAssembly.instantiateStreaming()
 *   El polyfill en index.ts lo resuelve en entorno node.
 */
export default defineConfig({
  plugins: [wasm(), topLevelAwait()],
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
    globals: true,
    // Timeout generoso para la inicialización del WASM (~2-3 segundos)
    testTimeout: 15000,
    hookTimeout: 15000,
  },
});
