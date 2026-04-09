#!/bin/bash
set -e

# Kalpixk Unified Installer
# "Porque defender sistemas no debería requerir instalar nada."

echo "🛡️  Iniciando instalación de Kalpixk..."

# 1. Verificar dependencias de sistema
if ! command -v rustup >/dev/null 2>&1; then echo "❌ Rust is required but not installed."; fi
if ! command -v python3 >/dev/null 2>&1; then echo "❌ Python 3 is required."; fi
if ! command -v node >/dev/null 2>&1; then echo "❌ Node.js is required."; fi

# 2. Instalar backend python
echo "🐍 Instalando dependencias de Python..."
pip install -e "./python"
pip install -r requirements.txt

# 3. Compilar Core Rust → WASM
echo "🦀 Compilando motor Core en Rust (WASM)..."
if ! command -v wasm-pack >/dev/null 2>&1; then
    cargo install wasm-pack
fi
cd crates/kalpixk-core
wasm-pack build --target web --release
cd ../..

# 4. Sincronizar WASM con el frontend
echo "🔄 Sincronizando artefactos WASM..."
mkdir -p web/src/wasm
cp crates/kalpixk-core/pkg/kalpixk_core_bg.wasm web/src/wasm/
cp crates/kalpixk-core/pkg/kalpixk_core.js web/src/wasm/
cp crates/kalpixk-core/pkg/kalpixk_core.d.ts web/src/wasm/

# 5. Instalar y construir Frontend
echo "🌐 Construyendo dashboard web..."
cd web
npm install
npm run build
cd ..

# 6. Preparar entorno
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || echo "KALPIXK_API_KEY=dev_key_123" > .env
    echo "📝 Archivo .env creado."
fi

echo "✅ Instalación completada con éxito."
echo "🚀 Ejecuta 'make run' para iniciar Kalpixk."
