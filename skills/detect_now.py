#!/usr/bin/env python3
"""
Skill: detect_now
Corre detección inmediata y reporta resultado
Uso: python skills/detect_now.py [--loop 60] [--notify]
"""
import sys, os, argparse, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", type=int, default=0, help="Monitoreo continuo cada N segundos (0=once)")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--model", default="models/kalpixk_v2.pt")
    args = parser.parse_args()

    from src.ui import KalpixkTheme, ANSI
    from src.detector import AnomalyDetector
    from src.runtime import WasmRuntimeMonitor
    from datetime import datetime

    det = AnomalyDetector()
    mon = WasmRuntimeMonitor()

    # Cargar modelo si existe, si no entrenar rápido
    if os.path.exists(args.model):
        det.load(args.model)
        print(f"✅ Modelo cargado: {args.model}")
    else:
        print("⚠️  Modelo no encontrado — entrenando baseline rápido...")
        data = mon.generate_normal_baseline(500)
        det.train(data, epochs=50)
        os.makedirs("models", exist_ok=True)
        det.save(args.model)

    telegram = None
    if args.notify and os.getenv("TELEGRAM_BOT_TOKEN"):
        from src.channels.telegram_bot import KalpixkTelegramBot
        telegram = KalpixkTelegramBot(detector=det, monitor=mon)

    def detect_once():
        metrics = mon.capture_metrics()
        result = det.predict(metrics.to_array())
        score = result["reconstruction_errors"][0]
        score_norm = result["scores_normalized"][0]
        is_anomaly = result["anomalies"][0]
        ts = datetime.now().strftime("%H:%M:%S")

        if is_anomaly:
            status_tag = KalpixkTheme.STATUS["anomaly"]
            print(f"[{ts}] {status_tag} Score={score:.2f} (norm={score_norm:.3f}) THRESHOLD={det.threshold:.4f}")
            if telegram:
                telegram.send_anomaly_alert(score, "detect_now", {
                    "cpu": f"{metrics.cpu_usage:.1f}%",
                    "ram": f"{metrics.memory_mb:.0f} MB",
                    "heap": f"{metrics.heap_usage:.1f}%",
                })
        else:
            status_tag = KalpixkTheme.STATUS["ok"]
            print(f"[{ts}] {status_tag} Score={score:.4f} (norm={score_norm:.3f}) NORMAL")

        return {"ts": ts, "score": score, "anomaly": is_anomaly, "metrics": metrics.__dict__}

    if args.loop > 0:
        print(f"\n🔄 Monitoreo continuo cada {args.loop}s (Ctrl+C para detener)\n")
        try:
            while True:
                detect_once()
                time.sleep(args.loop)
        except KeyboardInterrupt:
            print("\n⛔ Monitor detenido")
    else:
        return detect_once()

if __name__ == "__main__":
    run()
