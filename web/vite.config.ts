// =============================================================================
// web/vite.config.ts — Configuración del servidor de desarrollo y build
// =============================================================================

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import wasm from 'vite-plugin-wasm'
import topLevelAwait from 'vite-plugin-top-level-await'

// base: path base del sitio en producción
// Por default para GitHub Pages: '/Wasm-Kalpixk_IA_DevOps/'
const base = process.env.VITE_BASE_URL || '/Wasm-Kalpixk_IA_DevOps/'

export default defineConfig({
  // Path base del sitio — importante para que los assets carguen correctamente
  base,

  plugins: [
    react(),
    // Soporte nativo de WASM como ES modules
    wasm(),
    // Soporte de top-level await (necesario para init() del WASM)
    topLevelAwait(),
  ],

  optimizeDeps: {
    // NO pre-bundlear kalpixk-core porque es un módulo WASM nativo
    exclude: ['kalpixk-core'],
  },

  build: {
    // esnext permite usar sintaxis moderna de JavaScript/WebAssembly
    target: 'esnext',
    chunkSizeWarningLimit: 1000,
  },

  server: {
    port: 3000,
    host: '0.0.0.0',
    fs: {
      // Permitir acceso a archivos fuera del directorio web/ (para el WASM)
      allow: ['.', '..'],
    },
    // Headers de seguridad críticos para WebAssembly (SharedArrayBuffer)
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
    // Proxy para API local (FastAPI)
    proxy: {
      "/api": "http://localhost:8000",
      "/ws":  { target: "ws://localhost:8000", ws: true },
    },
  },
})
