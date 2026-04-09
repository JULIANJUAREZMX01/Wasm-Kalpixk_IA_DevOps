# Script de compilación nativa para entornos Windows (QUINTANA)
$ErrorActionPreference = "Stop"

Write-Host "--- KALPIXK WASM BUILDER V2.1 ---" -ForegroundColor Cyan

try {
    # 1. Navegar a la crates
    Set-Location "$PSScriptRoot/../crates/kalpixk-core"

    # 2. Ejecutar compilación
    Write-Host "[*] Ejecutando wasm-pack build..." -ForegroundColor Yellow
    wasm-pack build --target web --release

    # 3. Optimizar binario si wasm-opt existe
    if (Get-Command "wasm-opt" -ErrorAction SilentlyContinue) {
        Write-Host "[*] Optimizando binario con wasm-opt -Oz..." -ForegroundColor Yellow
        wasm-opt -Oz pkg/kalpixk_core_bg.wasm -o pkg/kalpixk_core_bg.wasm
    }

    # 4. Sincronizar con el frontend
    Write-Host "[*] Sincronizando artefactos con web/src/wasm/..." -ForegroundColor Yellow
    $WasmDest = "$PSScriptRoot/../web/src/wasm"
    if (!(Test-Path $WasmDest)) { New-Item -ItemType Directory -Path $WasmDest }
    Copy-Item "pkg/*" -Destination $WasmDest -Recurse -Force

    Write-Host "[SUCCESS] Núcleo WASM forjado y sincronizado." -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Fallo en la forja: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Set-Location "$PSScriptRoot/.."
}
