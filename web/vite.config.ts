// =============================================================================
// web/vite.config.ts
// =============================================================================
import { defineConfig } from "vite";
import wasm from "vite-plugin-wasm";
import topLevelAwait from "vite-plugin-top-level-await";
import path from "path";

export default defineConfig({
  plugins: [wasm(), topLevelAwait()],

  // Base URL para GitHub Pages:
  // https://julianjuarezmx01.github.io/Wasm-Kalpixk_IA_DevOps/
  // En desarrollo local usa '/' automáticamente via env
  base: process.env.VITE_BASE_URL || "/",

  optimizeDeps: {
    exclude: ["kalpixk-core"],
  },

  build: {
    target: "esnext",
    // No incluir source maps en producción (reduce tamaño)
    sourcemap: false,
  },

  server: {
    port: 3000,
    headers: {
      // Requeridos para WebAssembly con SharedArrayBuffer
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
    fs: {
      // Permitir acceso al pkg/ fuera de web/
      allow: [
        path.resolve(__dirname, ".."),
      ],
    },
  },

  preview: {
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
  },
});
