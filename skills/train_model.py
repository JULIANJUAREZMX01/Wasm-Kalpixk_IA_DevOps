#!/usr/bin/env python3
"""
Skill: train_model
Entrena/re-entrena el motor Kalpixk y guarda el modelo
Uso: python skills/train_model.py [--samples 500] [--epochs 100] [--sigma 2.0]
"""
import sys, os, argparse, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--sigma", type=float, default=2.0)
    parser.add_argument("--output", default="models/kalpixk_v2.pt")
    parser.add_argument("--notify", action="store_true", help="Notificar via Telegram al terminar")
    args = parser.parse_args()

    from src.ui import KalpixkTheme
    from src.detector import AnomalyDetector
    from src.runtime import WasmRuntimeMonitor

    KalpixkTheme.print_banner()
    print(f"\n🧠 Entrenando Kalpixk Motor")
    print(f"  Samples: {args.samples} | Epochs: {args.epochs} | Sigma: {args.sigma}")
    print(f"  Output:  {args.output}\n")

    det = AnomalyDetector()
    mon = WasmRuntimeMonitor()
    data = mon.generate_normal_baseline(n_samples=args.samples)

    stats = det.train(data, epochs=args.epochs, auto_threshold_sigma=args.sigma)

    # Evaluar con datos de prueba
    anomalies_test = __import__("numpy").tile([5000.0]*10, (20, 1)).astype("float32")
    eval_res = det.evaluate(data[:50], anomalies_test)

    print(f"\n📊 Resultados:")
    print(f"  Loss final:  {stats['final_loss']:.6f}")
    print(f"  Threshold:   {stats['threshold']:.4f}")
    print(f"  Precision:   {eval_res['precision']:.1%}")
    print(f"  Recall:      {eval_res['recall']:.1%}")
    print(f"  F1:          {eval_res['f1']:.1%}")

    # Guardar modelo
    os.makedirs("models", exist_ok=True)
    det.save(args.output)
    print(f"\n✅ Modelo guardado en {args.output}")

    if args.notify and os.getenv("TELEGRAM_BOT_TOKEN"):
        from src.channels.telegram_bot import KalpixkTelegramBot
        bot = KalpixkTelegramBot()
        bot.send_message(
            f"🧠 *Kalpixk entrenado*\n"
            f"Samples: {args.samples} | Epochs: {args.epochs}\n"
            f"F1: {eval_res['f1']:.1%} | Threshold: {stats['threshold']:.4f}"
        )

    return stats

if __name__ == "__main__":
    run()
