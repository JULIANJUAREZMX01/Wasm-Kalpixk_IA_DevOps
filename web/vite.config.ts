import { defineConfig } from "vite";
import wasm from "vite-plugin-wasm";
import topLevelAwait from "vite-plugin-top-level-await";
import path from "path";

// Base URL: /Wasm-Kalpixk_IA_DevOps/ para GitHub Pages
// En local dev usa '/' si no se define la env var
const base = process.env.VITE_BASE_URL ?? "/";

export default defineConfig({
  plugins: [wasm(), topLevelAwait()],
  base,
  build: {
    target: "esnext",
    sourcemap: false,
    assetsDir: "assets",
    rollupOptions: {
      output: {
        // Nombres predecibles para debug
        entryFileNames: "assets/main.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
  },
  server: {
    port: 3000,
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
    fs: {
      allow: [path.resolve(__dirname, "..")],
    },
  },
  preview: {
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
  },
});
