// =============================================================================
// web/vite.config.ts — Configuración del servidor de desarrollo y build
// =============================================================================
//
// PROPÓSITO:
//   Vite es el bundler/servidor de desarrollo del frontend de Kalpixk.
//   Esta configuración tiene dos responsabilidades críticas:
//
//   1. Servir archivos .wasm correctamente
//      Los browsers modernos exigen headers de seguridad específicos para
//      cargar WebAssembly. Sin estos headers, el browser bloquea la carga
//      con el error "SharedArrayBuffer is not defined" o similar.
//
//   2. Permitir acceso a archivos fuera del directorio web/
//      El .wasm compilado está en crates/kalpixk-core/pkg/ (fuera de web/).
//      Por seguridad, Vite restringe el acceso a archivos externos por default.
//      fs.allow: ['.', '..'] le dice a Vite que puede acceder al directorio padre.
//
// PROBLEMA QUE RESOLVIÓ ESTA CONFIGURACIÓN:
//   En el Codespace, el servidor fallaba con:
//     "The request url /workspaces/.../pkg/kalpixk_core_bg.wasm
//      is outside of Vite serving allow list"
//   Solución: agregar fs.allow: ['.', '..'] en la sección server.
//
// USO:
//   Desarrollo:   npm run dev    → http://localhost:3000
//   Producción:   npm run build  → genera web/dist/
//   Preview:      npm run preview → preview del build de producción
//
// =============================================================================

import { defineConfig } from 'vite'

// vite-plugin-wasm: plugin oficial para cargar módulos WebAssembly
// Maneja automáticamente la importación de .wasm como ES modules
import wasm from 'vite-plugin-wasm'

// vite-plugin-top-level-await: permite usar `await` a nivel de módulo
// Necesario porque inicializar el módulo WASM es una operación async:
//   import init from './kalpixk_core.js'
//   await init()  // ← top-level await (no está dentro de async function)
import topLevelAwait from 'vite-plugin-top-level-await'

// base: path base del sitio en producción
// - En desarrollo local: '/' (raíz del servidor)
// - En GitHub Pages: '/Wasm-Kalpixk_IA_DevOps/' (nombre del repositorio)
// La variable de entorno VITE_BASE_URL se define en el workflow de GitHub Actions
const base = process.env.VITE_BASE_URL || '/'

export default defineConfig({
  // Path base del sitio — importante para que los assets carguen correctamente
  // tanto en desarrollo como en GitHub Pages
  base,

  // ── Plugins ─────────────────────────────────────────────────────────────────
  plugins: [
    // Soporte nativo de WASM como ES modules
    wasm(),
    // Soporte de top-level await (necesario para init() del WASM)
    topLevelAwait(),
  ],

  // ── Optimización de dependencias ────────────────────────────────────────────
  optimizeDeps: {
    // NO pre-bundlear kalpixk-core porque es un módulo WASM nativo,
    // no un paquete npm normal. Si Vite intenta pre-bundlearlo,
    // el proceso falla porque .wasm no es JavaScript.
    exclude: ['kalpixk-core'],
  },

  // ── Configuración del build de producción ────────────────────────────────────
  build: {
    // esnext permite usar sintaxis moderna de JavaScript/WebAssembly
    // como top-level await y dynamic imports
    target: 'esnext',

    // No dar warning si un chunk es grande (el .wasm puede pesar ~245KB)
    // Esto es esperado y normal para módulos WASM
    chunkSizeWarningLimit: 1000,
  },

  // ── Servidor de desarrollo ───────────────────────────────────────────────────
  server: {
    // Puerto fijo para que los links del README sean consistentes
    port: 3000,

    // 0.0.0.0 = escuchar en todas las interfaces de red
    // Necesario en Codespaces para que sea accesible desde el browser del PC
    host: '0.0.0.0',

    // ── File System Access ────────────────────────────────────────────────────
    fs: {
      // Por default, Vite solo sirve archivos dentro del directorio web/
      // '.'  = web/ (directorio actual)
      // '..' = raíz del repo (necesario para acceder a crates/kalpixk-core/pkg/)
      //
      // Esto resuelve el error:
      //   "request url is outside of Vite serving allow list"
      allow: ['.', '..'],
    },

    // ── Headers de seguridad para WebAssembly ─────────────────────────────────
    //
    // CONTEXTO IMPORTANTE:
    //   Los browsers modernos requieren estos dos headers para cargar WASM
    //   con características avanzadas como SharedArrayBuffer y WASM threads.
    //
    //   Sin estos headers, el browser muestra:
    //     "SharedArrayBuffer is not defined" o
    //     "Cross-Origin-Embedder-Policy header is required"
    //
    //   Estos headers crean un "contexto de origen aislado" que le dice
    //   al browser que el sitio controla todos sus recursos y puede
    //   usar características de bajo nivel como memoria compartida.
    //
    // REFERENCIA:
    //   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer#security_requirements
    //
    headers: {
      // Cross-Origin-Opener-Policy: same-origin
      // → El documento solo puede compartir el proceso del browser con
      //   páginas del mismo origen (no puede ser embebido en iframes externos)
      'Cross-Origin-Opener-Policy': 'same-origin',

      // Cross-Origin-Embedder-Policy: require-corp
      // → El documento solo puede cargar recursos externos si esos recursos
      //   incluyen el header CORP (Cross-Origin-Resource-Policy)
      //   Los archivos .wasm del mismo servidor cumplen esto automáticamente
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
  },
})
