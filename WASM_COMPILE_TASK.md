# ⚡ TAREA CRÍTICA — Compilar WASM y hacer deploy

## Estado actual
- ✅ Código Rust en `crates/kalpixk-core/src/` listo para compilar
- ✅ Frontend en `web/` configurado (Vite + wasm-plugin + Vitest)
- ❌ `crates/kalpixk-core/pkg/` NO existe — falta compilar
- ❌ CI workflow no puede modificarse via API (necesita scope `workflow`)

## Pasos para compilar (Jules o manualmente)

### 1. Compilar el WASM
```bash
cd crates/kalpixk-core
rustup target add wasm32-unknown-unknown
cargo install wasm-pack
wasm-pack build --target web --release
```

Resultado esperado:
```
crates/kalpixk-core/pkg/
  kalpixk_core_bg.wasm   ← el binario (~50-200 KB)
  kalpixk_core.js        ← glue code JS
  kalpixk_core.d.ts      ← tipos TypeScript
  package.json
```

### 2. Verificar que el frontend funciona
```bash
cd web
pnpm install
pnpm build    # debe compilar sin errores
pnpm test     # 5 tests deben pasar
pnpm dev      # abre http://localhost:3000 — debe mostrar "✅ Motor WASM listo"
```

### 3. Commitear pkg/ al repo
```bash
git add crates/kalpixk-core/pkg/
git add web/
git commit -m "feat: compilar kalpixk-core a WASM + frontend funcional"
git push
```

### 4. Fix del CI (requiere GitHub UI o token con scope workflow)
El archivo `.github/workflows/ci.yml` tiene `cargo fmt --check` que falla.
**Solución:** ir a GitHub → Actions → (desactivar el job rust-check temporalmente)
O agregar `rustfmt` y correr `cargo fmt` antes del push.

## Por qué es crítico
El hackathon AMD (Mayo 9-10, 2026) requiere demostrar:
- El WASM corre en el browser — cero instalación
- Detecta SSH brute force y DROP TABLE DB2 en tiempo real
- Feature matrix de 32 dimensiones compatible con el modelo AMD MI300X

**Sin el pkg/ compilado, el frontend no puede importar el WASM.**
