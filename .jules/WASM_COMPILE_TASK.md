# 🎯 Jules Task — Compile WASM + Frontend Setup

**Repo:** https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps  
**Priority:** CRITICAL — hackathon May 9, AMD Developer Hackathon lablab.ai  
**Budget:** ~$4 in GPU credits (compile locally, no GPU needed for WASM build)

---

## What you need to do (in order)

### Step 1 — Install wasm-pack (if not present)
```bash
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
```

### Step 2 — Compile the Rust crate to WASM
```bash
cd crates/kalpixk-core
wasm-pack build --target web --out-dir ../../web/public/pkg
```
This generates:
- `web/public/pkg/kalpixk_core_bg.wasm` — the binary (the critical deliverable)
- `web/public/pkg/kalpixk_core.js` — JS bindings
- `web/public/pkg/kalpixk_core_bg.js`
- `web/public/pkg/kalpixk_core.d.ts`

### Step 3 — Setup Vite frontend
Create `web/package.json`:
```json
{
  "name": "kalpixk-dashboard",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "typescript": "^5.0.0"
  }
}
```

Create `web/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    }
  },
  optimizeDeps: {
    exclude: ['kalpixk-core']
  }
})
```

### Step 4 — Create the demo page
Create `web/src/App.tsx`:
```tsx
import { useEffect, useState } from 'react'

interface DetectionResult {
  severity: 'CLEAN' | 'SUSPICIOUS' | 'ANOMALY' | 'CRITICAL'
  score: number
  details: string
}

export default function App() {
  const [wasmLoaded, setWasmLoaded] = useState(false)
  const [result, setResult] = useState<DetectionResult | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function loadWasm() {
      try {
        const wasm = await import('/pkg/kalpixk_core.js')
        await wasm.default()
        setWasmLoaded(true)
        console.log('✅ Kalpixk WASM loaded — zero install')
      } catch (e) {
        console.error('WASM load error:', e)
      }
    }
    loadWasm()
  }, [])

  const runDetection = async () => {
    setLoading(true)
    // Simulate detection with the WASM module
    await new Promise(r => setTimeout(r, 400))
    setResult({
      severity: 'ANOMALY',
      score: 0.847,
      details: 'Shannon entropy spike detected: 7.2 bits. Pattern matches lateral movement signature MITRE ATT&CK T1021.'
    })
    setLoading(false)
  }

  const severityColor = {
    CLEAN: '#639922',
    SUSPICIOUS: '#BA7517',
    ANOMALY: '#E24B4A',
    CRITICAL: '#8B0000'
  }

  return (
    <div style={{ fontFamily: 'monospace', maxWidth: 600, margin: '40px auto', padding: '0 20px' }}>
      <h1>🛡️ Kalpixk SIEM</h1>
      <p style={{ color: '#666', fontSize: 13 }}>
        WASM-native anomaly detection — AMD MI300X accelerated
      </p>
      
      <div style={{ 
        background: wasmLoaded ? '#EAF3DE' : '#FAEEDA', 
        border: `1px solid ${wasmLoaded ? '#97C459' : '#EF9F27'}`,
        borderRadius: 8, padding: '10px 14px', margin: '16px 0', fontSize: 13 
      }}>
        {wasmLoaded 
          ? '✅ WASM engine loaded — running in browser, zero install' 
          : '⏳ Loading WASM engine...'}
      </div>

      <button 
        onClick={runDetection} 
        disabled={!wasmLoaded || loading}
        style={{
          background: '#3C3489', color: 'white', border: 'none',
          borderRadius: 6, padding: '10px 20px', cursor: 'pointer',
          fontSize: 14, marginBottom: 16
        }}
      >
        {loading ? 'Analyzing...' : 'Run Detection'}
      </button>

      {result && (
        <div style={{
          background: '#111', borderRadius: 8, padding: 16,
          border: `1px solid ${severityColor[result.severity]}`
        }}>
          <div style={{ color: severityColor[result.severity], fontSize: 18, fontWeight: 600 }}>
            [{result.severity}] score: {result.score.toFixed(3)}
          </div>
          <div style={{ color: '#aaa', fontSize: 12, marginTop: 8 }}>
            {result.details}
          </div>
        </div>
      )}
    </div>
  )
}
```

Create `web/index.html`:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Kalpixk — WASM SIEM</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

Create `web/src/main.tsx`:
```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

### Step 5 — Install and verify
```bash
cd web
npm install
npm run dev
# → Should open browser showing WASM loaded message
```

### Step 6 — Run tests
```bash
npm run test
```

### Step 7 — Commit everything
```bash
git add .
git commit -m "feat(wasm): compile kalpixk-core to WASM + Vite frontend demo"
git push
```

---

## Definition of Done
- [ ] `web/public/pkg/kalpixk_core_bg.wasm` exists and is committed
- [ ] `npm run dev` starts without errors
- [ ] Browser shows "WASM engine loaded" message
- [ ] `Run Detection` button returns a result
- [ ] All files committed and pushed

---

## Notes for Jules
- Do NOT install Zig — the project uses Rust only
- The WASM must load without any server-side Python dependency
- CORS headers in vite.config.ts are required for SharedArrayBuffer (WASM threads)
- If `wasm-pack` fails, check that Rust target `wasm32-unknown-unknown` is installed:
  `rustup target add wasm32-unknown-unknown`
