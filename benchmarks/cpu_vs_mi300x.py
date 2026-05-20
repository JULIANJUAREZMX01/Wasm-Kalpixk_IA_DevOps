"""
Kalpixk Benchmark — CPU Python vs AMD MI300X ROCm
This is the technical proof for hackathon judges.
"""
import torch
import time

def benchmark_device(device, n_samples=10000, n_features=10, n_runs=100):
    model_enc = torch.nn.Sequential(
        torch.nn.Linear(n_features, 5),
        torch.nn.ReLU(),
        torch.nn.Linear(5, 2)
    ).to(device)
    model_dec = torch.nn.Sequential(
        torch.nn.Linear(2, 5),
        torch.nn.ReLU(),
        torch.nn.Linear(5, n_features)
    ).to(device)

    data = torch.randn(n_samples, n_features).to(device)

    # Warmup
    for _ in range(5):
        _ = model_dec(model_enc(data))

    # Benchmark
    start = time.perf_counter()
    for _ in range(n_runs):
        out = model_dec(model_enc(data))
        loss = torch.nn.MSELoss()(out, data)
    elapsed = time.perf_counter() - start

    return elapsed / n_runs * 1000  # ms per run


if __name__ == '__main__':
    print("=== Kalpixk Benchmark: CPU vs AMD MI300X ===\n")

    # CPU
    cpu_ms = benchmark_device('cpu')
    print(f"CPU:      {cpu_ms:.2f} ms/run")

    # GPU (AMD MI300X via ROCm)
    if torch.cuda.is_available():
        gpu_ms = benchmark_device('cuda')
        speedup = cpu_ms / gpu_ms
        print(f"MI300X:   {gpu_ms:.2f} ms/run")
        print(f"Speedup:  {speedup:.1f}x faster on AMD ROCm")
        print(f"Device:   {torch.cuda.get_device_name(0)}")
        print(f"VRAM:     {round(torch.cuda.get_device_properties(0).total_memory/1e9,1)} GB")
    else:
        print("GPU not available — run on kalpixk-dev-01")
