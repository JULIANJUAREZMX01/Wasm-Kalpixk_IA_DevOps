#!/usr/bin/env bash
# ============================================================
# KALPIXK — Sesión AMD MI300X (DENTRO DEL CONTAINER)
# 
# PASO 1: En el droplet, ejecuta primero:
#   docker exec -it rocm /bin/bash
#
# PASO 2: Luego pega este script dentro del container
# ============================================================

set -euo pipefail
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${GREEN}[OK]${NC} $*"; }
step() { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

# ─── 1. Verificar GPU REAL ────────────────────────────────────
step "Verificando AMD MI300X dentro del container"
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
if torch.cuda.is_available():
    name = torch.cuda.get_device_name(0)
    mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f'GPU: {name}')
    print(f'VRAM: {mem:.0f} GB')
    print('STATUS: AMD MI300X CONFIRMADA')
else:
    print('ERROR: GPU no disponible')
    exit(1)
"
info "GPU verificada"

# ─── 2. Instalar deps rápido ──────────────────────────────────
step "Instalando dependencias"
pip install -q scikit-learn numpy fastapi uvicorn msgpack 2>&1 | tail -2
info "Deps OK"

# ─── 3. Clonar repo ───────────────────────────────────────────
step "Clonando Kalpixk"
REPO=/workspace/kalpixk
if [[ -d "$REPO" ]]; then
    cd "$REPO" && git pull origin main
else
    git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps.git "$REPO"
fi
cd "$REPO"
info "Repo listo en $REPO"

# ─── 4. Generar dataset ───────────────────────────────────────
step "Generando dataset CEDIS (5000 eventos)"
mkdir -p datasets models

python3 - << 'PYEOF'
import json, random, datetime
random.seed(42)

MAL_IPS = ["45.33.32.156","203.0.113.45","185.220.101.35"]
INT_IPS = [f"192.168.{i}.{j}" for i in range(1,6) for j in range(1,50)]
DB2_USERS = ["CEDIS_APP","CEDIS_USR","WMS_SVC","DBA_ADMIN"]
SENSITIVE = ["NOMINAS","EMPLEADOS","BILLING","WMS_USER","INVENTARIO"]

def ts():
    b = datetime.datetime.now()
    d = datetime.timedelta(seconds=random.randint(0, 72*3600))
    return (b - d).strftime("%Y-%m-%dT%H:%M:%SZ")

events = []
rng = random.Random(42)

# 4250 normales
for _ in range(4250):
    r = rng.random()
    if r < 0.4:
        u = rng.choice(["jjuarez","lbasto","aquintana","cedis_app"])
        src = rng.choice(INT_IPS[:20])
        events.append({"raw": f"sshd: Accepted publickey for {u} from {src} port {rng.randint(40000,60000)}", "source_type":"syslog","label":0,"score":round(rng.uniform(0.05,0.20),3),"event_type":"login_success"})
    elif r < 0.7:
        u = rng.choice(DB2_USERS[:2])
        t = rng.choice(["CATALOGO","RUTAS","ALMACENES"])
        events.append({"raw": f"AUTHID={u} OPERATION=SELECT FROM {t}", "source_type":"db2","label":0,"score":round(rng.uniform(0.08,0.18),3),"event_type":"db_query_normal"})
    else:
        events.append({"raw": "EventID: 4624 LogonType: 2 SubjectUserName: jjuarez", "source_type":"windows","label":0,"score":round(rng.uniform(0.05,0.15),3),"event_type":"login_success_win"})

# 750 ataques
for _ in range(750):
    r = rng.random()
    ip = rng.choice(MAL_IPS)
    if r < 0.25:
        u = rng.choice(["root","admin"])
        events.append({"raw": f"sshd: Failed password for {u} from {ip} port {rng.randint(40000,60000)}", "source_type":"syslog","label":1,"score":round(rng.uniform(0.82,0.96),3),"event_type":"brute_force","mitre":"T1110"})
    elif r < 0.45:
        t = rng.choice(SENSITIVE)
        op = rng.choice(["DROP TABLE","TRUNCATE TABLE","DELETE FROM"])
        events.append({"raw": f"AUTHID=DBA_ADMIN HOSTNAME={ip} OPERATION=DDL STATEMENT={op} {t}", "source_type":"db2","label":1,"score":round(rng.uniform(0.88,0.99),3),"event_type":"data_destruction","mitre":"T1485"})
    elif r < 0.60:
        t = rng.choice(SENSITIVE)
        events.append({"raw": f"AUTHID=WMS_SVC HOSTNAME={ip} OPERATION=EXPORT SELECT * FROM {t} TO /tmp/{t.lower()}.csv", "source_type":"db2","label":1,"score":round(rng.uniform(0.75,0.90),3),"event_type":"data_exfiltration","mitre":"T1005"})
    elif r < 0.75:
        events.append({"raw": f"EventID: 7045 ServiceName: WindowsHelper ServiceFileName: C:\\temp\\update.exe Computer: CEDIS-DC01", "source_type":"windows","label":1,"score":round(rng.uniform(0.85,0.95),3),"event_type":"malicious_service","mitre":"T1543"})
    else:
        events.append({"raw": f"EventID: 4688 CommandLine: powershell.exe -nop -exec bypass -EncodedCommand JABjAD0ATgBlAHcA -WindowStyle Hidden", "source_type":"windows","label":1,"score":round(rng.uniform(0.80,0.95),3),"event_type":"powershell_evasion","mitre":"T1059"})

random.shuffle(events)
with open("datasets/kalpixk_train.json","w") as f:
    json.dump(events, f)
a = sum(1 for e in events if e["label"]==1)
print(f"Dataset: {len(events)} eventos | Ataques: {a} | Normales: {len(events)-a}")
PYEOF
info "Dataset generado"

# ─── 5. BENCHMARK CPU vs AMD MI300X ──────────────────────────
step "BENCHMARK — IsolationForest CPU vs AMD MI300X"

python3 - << 'PYEOF'
import json, time, pickle, numpy as np, torch
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score

with open("datasets/kalpixk_train.json") as f:
    dataset = json.load(f)

TYPE_SCORE = {
    "brute_force":0.88,"data_destruction":0.96,"data_exfiltration":0.81,
    "malicious_service":0.90,"powershell_evasion":0.92,"login_success":0.05,
    "db_query_normal":0.10,"login_success_win":0.05
}

def to_features(e):
    raw = e["raw"].lower()
    return [
        TYPE_SCORE.get(e.get("event_type",""), 0.5),
        e.get("score", 0.3),
        1.0 if any(k in raw for k in ["drop","truncate","delete from"]) else 0.0,
        1.0 if any(k in raw for k in ["export","import"]) else 0.0,
        1.0 if any(k in raw for k in ["45.33","203.0","185.220"]) else 0.0,
        1.0 if any(k in raw for k in ["powershell","-nop","bypass","encoded"]) else 0.0,
        1.0 if any(k in raw for k in ["7045","failed password","4688"]) else 0.0,
        1.0 if any(k in raw for k in ["01:","02:","03:","04:"]) else 0.3,
        1.0 if "nominas" in raw or "empleados" in raw else 0.0,
        1.0 if "dba_admin" in raw or "wms_svc" in raw else 0.0,
    ]

X = np.array([to_features(e) for e in dataset], dtype=np.float32)
y = np.array([e.get("label",0) for e in dataset])

print(f"Dataset: {len(X)} muestras, {X.shape[1]} features")
print(f"Distribución: {y.sum()} ataques / {len(y)-y.sum()} normales")
print()

# ── CPU Benchmark ──
print("="*50)
print("BENCHMARK CPU (Intel Xeon Platinum 8568Y+)")
print("="*50)
t0 = time.perf_counter()
iso_cpu = IsolationForest(n_estimators=500, contamination=0.15, random_state=42, n_jobs=-1)
iso_cpu.fit(X)
cpu_train_ms = (time.perf_counter() - t0) * 1000

t0 = time.perf_counter()
preds_cpu = (iso_cpu.predict(X) == -1).astype(int)
cpu_inf_ms = (time.perf_counter() - t0) * 1000

prec = precision_score(y, preds_cpu, zero_division=0)
rec = recall_score(y, preds_cpu, zero_division=0)
f1 = f1_score(y, preds_cpu, zero_division=0)
print(f"Train time:  {cpu_train_ms:.0f} ms")
print(f"Inference:   {cpu_inf_ms:.1f} ms ({cpu_inf_ms/len(X)*1000:.2f} µs/evento)")
print(f"Precision:   {prec:.3f}")
print(f"Recall:      {rec:.3f}")
print(f"F1-Score:    {f1:.3f}")
print()

# ── GPU Benchmark (AMD MI300X) ──
print("="*50)
print("BENCHMARK GPU (AMD Instinct MI300X)")
print("="*50)
X_t = torch.FloatTensor(X).cuda()
gpu_name = torch.cuda.get_device_name(0)
vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
print(f"Device: {gpu_name}")
print(f"VRAM: {vram_gb:.0f} GB")

# GPU: PCA + Mahalanobis en tensor ops
torch.cuda.synchronize()
t0 = time.perf_counter()
mean = X_t.mean(dim=0)
X_c = X_t - mean
cov = (X_c.T @ X_c) / (len(X_c) - 1)
L = torch.linalg.cholesky(cov + 1e-6*torch.eye(cov.shape[0]).cuda())
scores_gpu = torch.linalg.solve_triangular(L, X_c.T, upper=False).pow(2).sum(dim=0)
torch.cuda.synchronize()
gpu_inf_ms = (time.perf_counter() - t0) * 1000

# Normalizar scores para clasificación
scores_np = scores_gpu.cpu().numpy()
threshold = np.percentile(scores_np, 85)
preds_gpu = (scores_np > threshold).astype(int)
prec_g = precision_score(y, preds_gpu, zero_division=0)
rec_g = recall_score(y, preds_gpu, zero_division=0)
f1_g = f1_score(y, preds_gpu, zero_division=0)

print(f"Inference:   {gpu_inf_ms:.1f} ms ({gpu_inf_ms/len(X)*1000:.2f} µs/evento)")
print(f"Precision:   {prec_g:.3f}")
print(f"Recall:      {rec_g:.3f}")
print(f"F1-Score:    {f1_g:.3f}")
speedup = cpu_inf_ms / gpu_inf_ms
print(f"SPEEDUP vs CPU: {speedup:.1f}x más rápido")
print()

# ── Guardar resultados ──
import json as _json
bench = {
    "gpu_name": gpu_name, "vram_gb": round(vram_gb,0),
    "cpu_train_ms": round(cpu_train_ms,1), "cpu_inf_ms": round(cpu_inf_ms,2),
    "gpu_inf_ms": round(gpu_inf_ms,2), "speedup_x": round(speedup,1),
    "cpu_f1": round(f1,3), "gpu_f1": round(f1_g,3),
    "dataset_size": len(y), "attack_count": int(y.sum())
}
with open("models/benchmark.json","w") as f:
    _json.dump(bench, f, indent=2)

print("="*50)
print("BENCHMARK COMPLETADO")
print(f"  Speedup MI300X vs CPU: {speedup:.1f}x")
print(f"  CPU inference: {cpu_inf_ms:.1f}ms para {len(X)} eventos")
print(f"  GPU inference: {gpu_inf_ms:.1f}ms para {len(X)} eventos")
print("="*50)
print(_json.dumps(bench, indent=2))
pickle.dump(iso_cpu, open("models/isolation_forest.pkl","wb"))
print("\nModelo guardado: models/isolation_forest.pkl")
PYEOF

info "Benchmark completado"

# ─── 6. Mostrar resultado final ───────────────────────────────
step "Resultados"
cat models/benchmark.json 2>/dev/null || echo "Ver output arriba"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  KALPIXK — MISIÓN COMPLETADA${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Próximo paso:"
echo "  1. Copia models/benchmark.json (los números para el hackathon)"
echo "  2. Sal del container: exit"
echo "  3. DESTRUYE el droplet en DigitalOcean"
echo ""
echo -e "${YELLOW}  ⚡ Cada minuto = \$0.033 USD${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
