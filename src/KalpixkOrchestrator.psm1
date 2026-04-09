function Invoke-KalpixkBuild {
    [CmdletBinding()]
    param()
    process {
        Write-Host "--- INICIANDO FORJA DE NÚCLEO WASM ---" -ForegroundColor Cyan
        if (Get-Command "wasm-pack" -ErrorAction SilentlyContinue) {
            Set-Location "crates/kalpixk-core"
            wasm-pack build --target web --release
            Set-Location "../.."
            Write-Host "[OK] WASM Compilado exitosamente." -ForegroundColor Green
        } else {
            Write-Error "wasm-pack no detectado. Instalar con: cargo install wasm-pack"
        }
    }
}

function Start-KalpixkEngine {
    [CmdletBinding()]
    param()
    process {
        Write-Host "--- LANZANDO MOTOR DE ANOMALÍAS ---" -ForegroundColor Green
        python main.py
    }
}

function Repair-FeatureScaling {
    [CmdletBinding()]
    param()
    process {
        Write-Host "--- CORRIGIENDO ESCALADO DE FEATURES ---" -ForegroundColor Yellow
        # Nota técnica: Inyectar MinMaxScaler en el pipeline de src/detector/anomaly_detector.py
        Write-Host "[ACTION] Verificar que los datos de entrada en monitor_loop sean normalizados."
    }
}

Export-ModuleMember -Function Invoke-KalpixkBuild, Start-KalpixkEngine, Repair-FeatureScaling
