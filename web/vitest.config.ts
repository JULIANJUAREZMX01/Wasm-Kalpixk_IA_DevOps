import { defineConfig } from 'vitest/config'
import wasm from 'vite-plugin-wasm'
import topLevelAwait from 'vite-plugin-top-level-await'
import path from 'path'

export default defineConfig({
  plugins: [wasm(), topLevelAwait()],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts'],
  },
  resolve: {
    alias: {
      '../../../crates/kalpixk-core/pkg/kalpixk_core.js': path.resolve(__dirname, '../crates/kalpixk-core/pkg/kalpixk_core.js')
    }
  }
})
