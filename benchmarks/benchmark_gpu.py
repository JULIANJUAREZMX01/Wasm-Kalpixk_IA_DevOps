"""
Wasm-Kalpixk — Benchmark AMD MI300X
Mide throughput del detector en la GPU
"""
import torch
import time
import numpy as np
from loguru import logger

def benchmark_detector(n_samples=10000, input_dim=10, runs=5):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Benchmark en: {device}")
    
    if device.type == "cuda":
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")

    # Crear modelo simple para benchmark
    import torch.nn as nn
    model = nn.Sequential(
        nn.Linear(input_dim, 16), nn.ReLU(),
        nn.Linear(16, 3), nn.ReLU(),
        nn.Linear(3, 16), nn.ReLU(),
        nn.Linear(16, input_dim)
    ).to(device)

    data = torch.randn(n_samples, input_dim).to(device)
    
    # Warmup
    _ = model(data[:100])
    if device.type == "cuda":
        torch.cuda.synchronize()

    times = []
    for i in range(runs):
        start = time.perf_counter()
        with torch.no_grad():
            out = model(data)
        if device.type == "cuda":
            torch.cuda.synchronize()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        logger.info(f"Run {i+1}: {elapsed*1000:.2f}ms | {n_samples/elapsed:.0f} samples/sec")

    avg = sum(times) / len(times)
    throughput = n_samples / avg
    
    print(f"""
=== KALPIXK BENCHMARK RESULTS ===
Device:      {device}
Samples:     {n_samples:,}
Avg time:    {avg*1000:.2f} ms
Throughput:  {throughput:,.0f} samples/sec
Min time:    {min(times)*1000:.2f} ms
Max time:    {max(times)*1000:.2f} ms
=================================
""")
    return throughput

if __name__ == "__main__":
    benchmark_detector(n_samples=100000, runs=5)
