import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import wasm from "vite-plugin-wasm"
import topLevelAwait from "vite-plugin-top-level-await"
import path from "path"

export default defineConfig({
  plugins: [
    react(),
    wasm(),
    topLevelAwait()
  ],
  base: process.env.VITE_BASE_URL ?? "/Wasm-Kalpixk_IA_DevOps/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  build: {
    target: "es2022",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          charts: ["recharts"]
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  server: {
    port: 3000,
    host: "0.0.0.0",
    fs: {
      allow: [".", ".."]
    },
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp"
    },
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": {
        target: "ws://localhost:8000",
        ws: true
      }
    }
  },
  optimizeDeps: {
    exclude: ["kalpixk-core"]
  }
})
