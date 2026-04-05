import time, json, numpy as np, torch, torch.nn as nn, subprocess, os

device = torch.device("cuda")
vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
try:
    out = subprocess.check_output(["rocminfo"], text=True, stderr=subprocess.DEVNULL)
    lines = [l for l in out.split("\n") if "Marketing Name" in l]
    gpu_name = lines[0].split(":")[1].strip() if lines else "AMD MI300X"
except:
    gpu_name = "AMD Instinct MI300X"

print(f"GPU: {gpu_name} | VRAM: {vram:.0f} GB")

N, F = 500000, 32
rng = np.random.default_rng(42)
X = rng.normal(0.3, 0.1, (N, F)).clip(0,1).astype(np.float32)
mask = rng.random(N) < 0.15
X[mask] = rng.uniform(0.7, 1.0, (mask.sum(), F)).astype(np.float32)
print(f"Dataset: {N:,} eventos | Ataques: {mask.sum():,} (15%)")

class AE(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(F,128),nn.ReLU(),nn.Linear(128,64),nn.ReLU(),nn.Linear(64,16))
        self.dec = nn.Sequential(nn.Linear(16,64),nn.ReLU(),nn.Linear(64,128),nn.ReLU(),nn.Linear(128,F),nn.Sigmoid())
    def forward(self,x): return self.dec(self.enc(x))
    def err(self,x):
        with torch.no_grad(): return ((self.forward(x)-x)**2).mean(dim=1)

loss_fn = nn.MSELoss()

# CPU benchmark
print("\n--- CPU (Xeon Platinum 8568Y+) ---")
mc = AE()
oc = torch.optim.Adam(mc.parameters())
Xc = torch.FloatTensor(X[:50000])
t0 = time.perf_counter()
mc.train()
for _ in range(5):
    for i in range(0, len(Xc), 512):
        b = Xc[i:i+512]
        oc.zero_grad()
        loss_fn(mc(b), b).backward()
        oc.step()
cpu_train = (time.perf_counter()-t0)*1000

mc.eval()
Xi = torch.FloatTensor(X)
t0 = time.perf_counter()
sc = torch.cat([mc.err(Xi[i:i+512]) for i in range(0, len(Xi), 512)]).numpy()
cpu_inf = (time.perf_counter()-t0)*1000
thr = np.percentile(sc, 85)
p = (sc > thr).astype(int)
tp = ((p==1) & mask).sum(); fp = ((p==1) & ~mask).sum(); fn = ((p==0) & mask).sum()
f1c = 2*tp/(2*tp+fp+fn) if tp > 0 else 0
tput_cpu = N/(cpu_inf/1000)
print(f"Train 50K x5ep: {cpu_train:.0f}ms | Inf 500K: {cpu_inf:.0f}ms | {tput_cpu:,.0f} ev/s | F1={f1c:.3f}")

# GPU benchmark
print(f"\n--- GPU ({gpu_name}) ---")
mg = AE().to(device)
og = torch.optim.Adam(mg.parameters())
Xg = torch.FloatTensor(X[:50000]).to(device)
torch.cuda.synchronize()
t0 = time.perf_counter()
mg.train()
for _ in range(5):
    for i in range(0, len(Xg), 8192):
        b = Xg[i:i+8192]
        og.zero_grad()
        loss_fn(mg(b), b).backward()
        og.step()
torch.cuda.synchronize()
gpu_train = (time.perf_counter()-t0)*1000

mg.eval()
Xgi = torch.FloatTensor(X).to(device)
torch.cuda.synchronize()
t0 = time.perf_counter()
sg = torch.cat([mg.err(Xgi[i:i+32768]) for i in range(0, len(Xgi), 32768)])
torch.cuda.synchronize()
gpu_inf = (time.perf_counter()-t0)*1000
sg = sg.cpu().numpy()
thr_g = np.percentile(sg, 85)
pg = (sg > thr_g).astype(int)
tpg = ((pg==1) & mask).sum(); fpg = ((pg==1) & ~mask).sum(); fng = ((pg==0) & mask).sum()
f1g = 2*tpg/(2*tpg+fpg+fng) if tpg > 0 else 0
tput_gpu = N/(gpu_inf/1000)
vused = torch.cuda.memory_allocated()/1024**3
print(f"Train 50K x5ep: {gpu_train:.0f}ms | Inf 500K: {gpu_inf:.0f}ms | {tput_gpu:,.0f} ev/s | F1={f1g:.3f}")
print(f"VRAM usada: {vused:.2f} GB / {vram:.0f} GB")

tr_sp = cpu_train/gpu_train
inf_sp = cpu_inf/gpu_inf
print(f"\n{'='*50}")
print(f"  Training speedup:  {tr_sp:.1f}x")
print(f"  Inference speedup: {inf_sp:.1f}x")
print(f"  CPU:  {tput_cpu:>12,.0f} eventos/segundo")
print(f"  GPU:  {tput_gpu:>12,.0f} eventos/segundo")
print(f"{'='*50}")

r = {
    "gpu": gpu_name, "vram_gb": round(vram,0),
    "cpu_train_ms": round(cpu_train,1), "gpu_train_ms": round(gpu_train,1),
    "cpu_inf_ms": round(cpu_inf,1), "gpu_inf_ms": round(gpu_inf,1),
    "cpu_eps": round(tput_cpu,0), "gpu_eps": round(tput_gpu,0),
    "training_speedup": round(tr_sp,1), "inference_speedup": round(inf_sp,1),
    "cpu_f1": round(f1c,3), "gpu_f1": round(f1g,3),
    "vram_used_gb": round(vused,2)
}
os.makedirs("/workspace/kalpixk/models", exist_ok=True)
with open("/workspace/kalpixk/models/benchmark_real.json","w") as f:
    json.dump(r, f, indent=2)
print(json.dumps(r, indent=2))
print("\nGuardado: /workspace/kalpixk/models/benchmark_real.json")
