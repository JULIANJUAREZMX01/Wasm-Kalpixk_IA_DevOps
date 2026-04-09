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
  },

  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws":  { target: "ws://localhost:8000",  ws: true },
    },
  },

  // Prevent Vite from pre-bundling the WASM module
  optimizeDeps: {
    exclude: ["kalpixk-core"],
  },
});
