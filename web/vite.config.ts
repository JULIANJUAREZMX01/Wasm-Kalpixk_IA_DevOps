import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import wasm from "vite-plugin-wasm"
import topLevelAwait from "vite-plugin-top-level-await"
import path from "path"

// GitHub Pages siempre sirve desde /Wasm-Kalpixk_IA_DevOps/
// base HARDCODED — no depende de variable de entorno (que puede no llegar a Rollup)
const BASE = "/Wasm-Kalpixk_IA_DevOps/"

export default defineConfig({
  plugins: [
    react(),
    wasm(),
    topLevelAwait()
  ],
  base: BASE,
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 1000,
    // Sin manualChunks para evitar problemas de cache con hash estático
  },
  server: {
    port: 3000,
    host: "0.0.0.0",
    fs: { allow: [".", ".."] },
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp"
    },
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true }
    }
  },
  optimizeDeps: {
    exclude: ["kalpixk-core"]
  }
})
