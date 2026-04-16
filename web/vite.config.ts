import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  // CRITICAL: without this, GitHub Pages returns 404 on all assets
  // /assets/main.js → 404  (broken)
  // /Wasm-Kalpixk_IA_DevOps/assets/main.js → 200 (correct)
  base: process.env.VITE_BASE_URL ?? "/Wasm-Kalpixk_IA_DevOps/",

  build: {
    target: "es2022",
    outDir: "dist",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          charts: ["recharts"],
        },
      },
    },
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
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws":  { target: "ws://localhost:8000",  ws: true },
    },
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

  // Prevent Vite from pre-bundling the WASM module
  optimizeDeps: {
    exclude: ["kalpixk-core"],
  },
});
