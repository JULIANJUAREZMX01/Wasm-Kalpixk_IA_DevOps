import { defineConfig, type Plugin } from "vite"
import react from "@vitejs/plugin-react"
import wasm from "vite-plugin-wasm"
import topLevelAwait from "vite-plugin-top-level-await"
import path from "path"
import { readFileSync, writeFileSync } from "fs"

const BASE = "/Wasm-Kalpixk_IA_DevOps/"

// Plugin que corrige el base en el index.html después del build
// (vite-plugin-wasm puede interferir con la transformación del HTML)
function fixBasePlugin(): Plugin {
  return {
    name: "fix-base-in-html",
    // Hook que se ejecuta DESPUÉS de que Vite escribe el dist/
    closeBundle() {
      try {
        const htmlPath = path.resolve(__dirname, "dist/index.html")
        let html = readFileSync(htmlPath, "utf-8")
        // Reemplazar rutas absolutas /assets/ → BASE/assets/
        const fixed = html
          .replace(/src="\/assets\//g, )
          .replace(/href="\/assets\//g, )
          .replace(/crossorigin src="\/assets\//g, )
        writeFileSync(htmlPath, fixed)
        console.log("[fix-base] dist/index.html corregido con base:", BASE)
      } catch (e) {
        console.warn("[fix-base] No se pudo leer dist/index.html:", e)
      }
    }
  }
}

export default defineConfig({
  plugins: [
    react(),
    wasm(),
    topLevelAwait(),
    fixBasePlugin(),
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
