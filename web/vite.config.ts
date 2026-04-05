import { defineConfig } from 'vite'
import wasm from 'vite-plugin-wasm'
import topLevelAwait from 'vite-plugin-top-level-await'

export default defineConfig({
  plugins: [
    wasm(),
    topLevelAwait()
  ],
  optimizeDeps: {
    exclude: ['kalpixk-core']
  },
  build: {
    target: 'esnext'
  },
  server: {
    port: 3000,
    fs: {
      allow: ['..']
    },
    headers: {
      // Necesario para SharedArrayBuffer y WASM threads
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    }
  }
})
