#!/usr/bin/env python3
"""
Skill: benchmark
Mide throughput del motor Kalpixk en AMD MI300X
Uso: python skills/benchmark.py [--samples 100000] [--runs 5] [--notify]
"""
import sys, os, argparse, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=100000)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--notify", action="store_true")
    args = parser.parse_args()

    import torch
    from src.ui import KalpixkTheme, ANSI
    from src.detector import AnomalyDetector
    from src.runtime import WasmRuntimeMonitor

    KalpixkTheme.print_banner()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n⚡ BENCHMARK KALPIXK")
    print(f"  Device:  {device}")
    if device.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"  GPU:     {props.name}")
        print(f"  VRAM:    {props.total_memory/1e9:.1f} GB")
    print(f"  Samples: {args.samples:,} | Runs: {args.runs}\n")

    det = AnomalyDetector()
    mon = WasmRuntimeMonitor()
    data = mon.generate_normal_baseline(500)
    det.train(data, epochs=30)

    import numpy as np
    bench_data = np.random.randn(args.samples, 10).astype("float32")
    
    # Warmup
    det.predict(bench_data[:100])
    if device.type == "cuda":
        torch.cuda.synchronize()

    times = []
    for i in range(args.runs):
        t0 = time.perf_counter()
        det.predict(bench_data)
        if device.type == "cuda":
            torch.cuda.synchronize()
        elapsed = time.perf_counter() - t0
        tput = args.samples / elapsed
        times.append(elapsed)
        status = KalpixkTheme.STATUS["ok"]
        print(f"  {status} Run {i+1}: {elapsed*1000:.1f}ms | {tput:>12,.0f} samples/sec")

    avg = sum(times)/len(times)
    best = min(times)
    throughput = args.samples / avg
    best_throughput = args.samples / best

    print(f"""
{ANSI.RED_BRIGHT}{'='*50}{ANSI.RESET}
{ANSI.BOLD}  RESULTADOS BENCHMARK{ANSI.RESET}
  Avg throughput:  {throughput:>12,.0f} samples/sec
  Best throughput: {best_throughput:>12,.0f} samples/sec
  Avg time:        {avg*1000:>10.2f} ms
  Best time:       {best*1000:>10.2f} ms
  Device:          {device}
{ANSI.RED_BRIGHT}{'='*50}{ANSI.RESET}
""")

    if args.notify and os.getenv("TELEGRAM_BOT_TOKEN"):
        from src.channels.telegram_bot import KalpixkTelegramBot
        bot = KalpixkTelegramBot()
        bot.send_benchmark_result(throughput, str(device), avg*1000)

    return {"throughput": throughput, "avg_ms": avg*1000, "device": str(device)}

if __name__ == "__main__":
    run()
