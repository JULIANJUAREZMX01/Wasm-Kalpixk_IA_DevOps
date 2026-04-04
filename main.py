"""
Kalpixk — Entry Point Principal
Integra: AnomalyDetector + WasmMonitor + FastAPI + Telegram Bot + Dashboard
Estética: SACITY/dhell (rojo/negro/cyber)
"""
import asyncio
import os
import time
import threading
from pathlib import Path
from loguru import logger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.ui import KalpixkTheme
from src.detector import AnomalyDetector
from src.runtime import WasmRuntimeMonitor
from src.channels.telegram_bot import KalpixkTelegramBot
from src.channels.whatsapp_twilio import KalpixkWhatsApp
from src.monitor import KalpixkSystemMonitor

# ── Boot visual ───────────────────────────────────────────
KalpixkTheme.print_banner()
KalpixkTheme.print_boot()

# ── Inicializar componentes ───────────────────────────────
detector = AnomalyDetector(threshold=0.5)
monitor_wasm = WasmRuntimeMonitor()
telegram = KalpixkTelegramBot(detector=detector, monitor=monitor_wasm)
whatsapp = KalpixkWhatsApp()
sys_monitor = KalpixkSystemMonitor(
    detector=detector,
    telegram_bot=telegram,
    whatsapp=whatsapp,
    check_interval=float(os.getenv("MONITOR_INTERVAL", "30"))
)

# ── Entrenar al arranque ──────────────────────────────────
logger.info("Entrenando detector con baseline normal...")
normal_data = monitor_wasm.generate_normal_baseline(n_samples=500)
detector.train(normal_data, epochs=50)
telegram.send_message("🚀 *Kalpixk iniciado*\nMotor entrenado y listo.\nAMD MI300X online ✅")

# ── FastAPI App ───────────────────────────────────────────
app = FastAPI(
    title="Wasm-Kalpixk_IA_DevOps",
    description="WASM Anomaly Detection Engine — AMD MI300X",
    version="0.1.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Servir dashboard estático
dashboard_path = Path("src/dashboard")
if dashboard_path.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_path)), name="static")

@app.get("/")
def root():
    index = dashboard_path / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Kalpixk API", "docs": "/docs"}

@app.get("/health")
def health():
    import torch
    return {
        "status": "ok",
        "model_trained": detector.is_trained,
        "device": str(detector.device),
        "gpu_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }

@app.get("/metrics")
def get_metrics():
    m = monitor_wasm.capture_metrics()
    result = detector.predict(m.to_array())
    return {"metrics": m.__dict__, "detection": result}

@app.post("/detect")
def detect(payload: dict):
    import numpy as np
    features = payload.get("features", [])
    X = __import__('numpy').array([features], dtype='float32')
    return detector.predict(X)

@app.get("/simulate/{anomaly_type}")
def simulate(anomaly_type: str):
    m = monitor_wasm.simulate_anomaly(anomaly_type)
    result = detector.predict(m.to_array())
    return {
        "anomaly_type": anomaly_type,
        "metrics": m.__dict__,
        "detection": result,
        "detected": any(result["anomalies"])
    }

@app.post("/train")
def train_model(payload: dict = {}):
    n = payload.get("n_samples", 500)
    epochs = payload.get("epochs", 50)
    data = monitor_wasm.generate_normal_baseline(n_samples=n)
    detector.train(data, epochs=epochs)
    telegram.send_message(f"🧠 Modelo re-entrenado\n{n} samples, {epochs} epochs")
    return {"success": True, "samples": n, "epochs": epochs}

@app.get("/benchmark")
def benchmark():
    import torch, time
    device = str(detector.device)
    import torch.nn as nn
    model = detector.model
    data = __import__('torch').randn(10000, 10).to(detector.device)
    start = time.perf_counter()
    with __import__('torch').no_grad():
        _ = model(data)
    if __import__('torch').cuda.is_available():
        __import__('torch').cuda.synchronize()
    elapsed = (time.perf_counter() - start) * 1000
    throughput = 10000 / (elapsed / 1000)
    result = {"throughput": throughput, "elapsed_ms": elapsed, "device": device}
    telegram.send_benchmark_result(throughput, device, elapsed)
    return result

@app.get("/status/telegram")
def check_telegram():
    ok = telegram.send_message("🔔 Test Kalpixk → Telegram OK")
    return {"sent": ok, "token_configured": bool(telegram.token)}

@app.get("/status/whatsapp")
def check_whatsapp():
    ok = whatsapp.send("🔔 Test Kalpixk → WhatsApp OK")
    return {"sent": ok, "enabled": whatsapp.enabled}


def run_telegram_bot():
    """Corre el bot de Telegram en thread separado."""
    try:
        telegram.start_polling()
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")


if __name__ == "__main__":
    import uvicorn
    # Iniciar monitor en background
    sys_monitor.start()
    # Iniciar Telegram bot en thread separado
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        t = threading.Thread(target=run_telegram_bot, daemon=True)
        t.start()
        logger.info("🤖 Telegram bot arrancado")
    # Levantar API
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"🚀 API en http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
