"""
Kalpixk — Unified SIEM Entry Point
Integrates: AI Anomaly Engine + WASM Monitor + FastAPI + Terminal TUI + Web Dashboard
"""
import os
import secrets
import socket
import threading
import time
from pathlib import Path
from loguru import logger
from fastapi import FastAPI, Depends, Security, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.ui import KalpixkTheme
from src.detector import AnomalyDetector
from src.runtime import WasmRuntimeMonitor
from src.channels.telegram_bot import KalpixkTelegramBot
from src.channels.whatsapp_twilio import KalpixkWhatsApp
from src.monitor import KalpixkSystemMonitor

# -- Helpers --
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# -- Boot visual --
KalpixkTheme.print_banner()

# -- Init components --
detector = AnomalyDetector()
monitor_wasm = WasmRuntimeMonitor()
telegram = KalpixkTelegramBot(detector=detector, monitor=monitor_wasm)
whatsapp = KalpixkWhatsApp()
sys_monitor = KalpixkSystemMonitor(
    detector=detector,
    telegram_bot=telegram,
    whatsapp=whatsapp,
    check_interval=float(os.getenv("MONITOR_INTERVAL", "30"))
)

# -- Auto-Train --
if not detector.is_trained:
    logger.info("🧠 Auto-training neural core...")
    normal_data = monitor_wasm.generate_normal_baseline(n_samples=500)
    detector.train(normal_data, epochs=50)
    logger.success("✅ Neural core calibrated.")

# -- Models --
class TrainPayload(BaseModel):
    n_samples: int = 500
    epochs: int = 50

# -- API Security --
API_KEY_NAME = "X-Kalpixk-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("KALPIXK_API_KEY")
    if not expected_key: return None
    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(status_code=403, detail="Invalid credentials")
    return api_key

# -- FastAPI App --
app = FastAPI(title="Kalpixk SIEM", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_trained": detector.is_trained,
        "device": str(detector.device),
        "ip_assigned": get_local_ip()
    }

@app.get("/metrics")
def get_metrics(api_key: str = Depends(verify_api_key)):
    m = monitor_wasm.capture_metrics()
    result = detector.predict(m.to_array())
    return {"metrics": m.__dict__, "detection": result}

@app.post("/train")
def train_api(payload: TrainPayload, api_key: str = Depends(verify_api_key)):
    data = monitor_wasm.generate_normal_baseline(n_samples=payload.n_samples)
    detector.train(data, epochs=payload.epochs)
    return {"success": True}

# -- SPA Static Serving --
dist_path = Path("web/dist")
if dist_path.exists():
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("health") or full_path.startswith("metrics") or full_path.startswith("train") or full_path.startswith("docs"):
            raise HTTPException(status_code=404)
        return FileResponse(dist_path / "index.html")

def run_api():
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")

def run_tui():
    from src.ui.terminal_dashboard import KalpixkTUI
    tui = KalpixkTUI(detector=detector, monitor=monitor_wasm)
    tui.run()

if __name__ == "__main__":
    sys_monitor.start()

    local_ip = get_local_ip()
    port = os.getenv("PORT", "8000")
    print(f"\n{KalpixkTheme.STATUS['info']} KALPIXK SIEM READY")
    print(f"  > BROWSER DASHBOARD: http://{local_ip}:{port}/")
    print(f"  > SYSTEM TELEMETRY:  Launching Terminal TUI...\n")

    # Run API in thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Run TUI in main thread
    try:
        run_tui()
    except KeyboardInterrupt:
        print("\nExiting Kalpixk...")
