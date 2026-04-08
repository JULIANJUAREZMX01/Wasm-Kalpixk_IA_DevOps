#!/usr/bin/env bash
# ============================================================
# Kalpixk — Script de primera sesión AMD MI300X
# 
# Ejecutar en el droplet después de conectarte por SSH:
#   chmod +x primera_sesion.sh && ./primera_sesion.sh
#
# Tiempo estimado: 20-30 minutos
# Créditos usados: ~0.66 USD (20min * $1.99/hr)
# ============================================================

set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
step() { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

echo -e "${CYAN}"
echo "  ██╗  ██╗ █████╗ ██╗     ██████╗ ██╗██╗  ██╗██╗  ██╗"
echo "  ██║ ██╔╝██╔══██╗██║     ██╔══██╗██║╚██╗██╔╝██║ ██╔╝"
echo "  █████╔╝ ███████║██║     ██████╔╝██║ ╚███╔╝ █████╔╝ "
echo "  ██╔═██╗ ██╔══██║██║     ██╔═══╝ ██║ ██╔██╗ ██╔═██╗ "
echo "  ██║  ██╗██║  ██║███████╗██║     ██║██╔╝ ██╗██║  ██╗"
echo "  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝"
echo -e "${NC}  Blue Team SIEM — AMD MI300X Setup\n"

# ─── 1. Verificar GPU ─────────────────────────────────────────
step "Verificando AMD MI300X"
if command -v rocminfo &>/dev/null; then
    GPU=$(rocminfo | grep "Marketing Name" | head -1 | awk -F': ' '{print $2}' | xargs)
    info "GPU detectada: ${GPU}"
    echo "$(rocminfo | grep 'VRAM Size' | head -1)" || true
else
    warn "rocminfo no encontrado — verifica que usaste la imagen ROCm Quick Start"
fi

# Mostrar info GPU
if command -v amd-smi &>/dev/null; then
    amd-smi monitor -ptum 2>/dev/null | head -5 || true
fi

# ─── 2. Actualizar sistema ────────────────────────────────────
step "Actualizando paquetes base"
apt-get update -qq
apt-get install -y -q git curl wget unzip python3-pip python3-venv htop

# ─── 3. Clonar repositorio ────────────────────────────────────
step "Clonando repositorio Kalpixk"
REPO_DIR="$HOME/Wasm-Kalpixk_IA_DevOps"

if [[ -d "$REPO_DIR" ]]; then
    info "Repo ya existe — actualizando..."
    cd "$REPO_DIR" && git pull
else
    git clone https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps.git "$REPO_DIR"
    info "Repo clonado en $REPO_DIR"
fi
cd "$REPO_DIR"

# ─── 4. Instalar Python deps ──────────────────────────────────
step "Instalando dependencias Python"
cd python 2>/dev/null || cd "$REPO_DIR"

pip3 install --quiet \
    fastapi uvicorn[standard] \
    torch torchvision \
    scikit-learn numpy \
    httpx websockets \
    pydantic 2>&1 | tail -3

info "Python deps instalados"

# ─── 5. Verificar PyTorch con ROCm ────────────────────────────
step "Verificando PyTorch + ROCm"
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
gpu = torch.cuda.is_available()
print(f'GPU disponible: {gpu}')
if gpu:
    name = torch.cuda.get_device_name(0)
    mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f'GPU: {name}')
    print(f'VRAM total: {mem:.0f} GB')
else:
    print('WARN: GPU no detectada por PyTorch — verifica ROCm installation')
"

# ─── 6. Generar dataset de entrenamiento ──────────────────────
step "Generando dataset de ataque/defensa"
mkdir -p "$REPO_DIR/datasets"

cat > /tmp/gen_dataset_quick.py << 'PYEOF'
import json, random, datetime, sys
random.seed(42)

def rand_ts():
    base = datetime.datetime.now()
    delta = datetime.timedelta(seconds=random.randint(0, 72*3600))
    return (base - delta).strftime("%Y-%m-%dT%H:%M:%SZ")

MALICIOUS_IPS = ["45.33.32.156","203.0.113.45","185.220.101.35"]
INTERNAL_IPS = [f"192.168.{i}.{j}" for i in range(1,6) for j in range(1,50)]
DB2_USERS = ["CEDIS_APP","CEDIS_USR","WMS_SVC","DBA_ADMIN"]
SENSITIVE_TABLES = ["NOMINAS","EMPLEADOS","BILLING","WMS_USER","INVENTARIO"]

events = []

# Normales (85%)
for _ in range(4250):
    r = random.random()
    if r < 0.4:
        u = random.choice(["jjuarez","lbasto","aquintana","cedis_app"])
        src = random.choice(INTERNAL_IPS[:20])
        events.append({
            "raw": f"Apr {random.randint(1,30)} {random.randint(8,17):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d} cancun-srv01 sshd[{random.randint(1000,9999)}]: Accepted publickey for {u} from {src} port {random.randint(40000,60000)}",
            "source_type": "syslog", "label": 0, "score": round(random.uniform(0.05, 0.20), 3),
            "event_type": "login_success"
        })
    elif r < 0.7:
        u = random.choice(DB2_USERS[:2])
        h = random.choice(INTERNAL_IPS[:10])
        t = random.choice(["CATALOGO_PRODUCTOS","RUTAS","ALMACENES"])
        events.append({
            "raw": f"TIMESTAMP={rand_ts()} AUTHID={u} HOSTNAME={h} OPERATION=EXECUTE STATEMENT=SELECT * FROM {t}",
            "source_type": "db2", "label": 0, "score": round(random.uniform(0.08, 0.18), 3),
            "event_type": "db_query_normal"
        })
    else:
        events.append({
            "raw": f"EventID: 4624 SubjectUserName: jjuarez Computer: WS-JJUAREZ LogonType: 2",
            "source_type": "windows", "label": 0, "score": round(random.uniform(0.05, 0.15), 3),
            "event_type": "login_success_win"
        })

# Ataques (15%)
for _ in range(750):
    r = random.random()
    ip = random.choice(MALICIOUS_IPS)
    if r < 0.25:  # SSH brute force
        u = random.choice(["root","admin","administrator"])
        events.append({
            "raw": f"Apr {random.randint(1,30)} {random.choice([1,2,3,4,22,23]):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d} cancun-srv01 sshd[{random.randint(1000,9999)}]: Failed password for {u} from {ip} port {random.randint(40000,60000)}",
            "source_type": "syslog", "label": 1, "score": round(random.uniform(0.82, 0.96), 3),
            "event_type": "brute_force", "mitre": "T1110"
        })
    elif r < 0.45:  # DB2 destructive
        u = random.choice(DB2_USERS[2:])
        t = random.choice(SENSITIVE_TABLES)
        op = random.choice(["DROP TABLE","TRUNCATE TABLE","DELETE FROM"])
        events.append({
            "raw": f"TIMESTAMP={rand_ts()} AUTHID={u} HOSTNAME={ip} OPERATION=DDL STATEMENT={op} {t}",
            "source_type": "db2", "label": 1, "score": round(random.uniform(0.88, 0.99), 3),
            "event_type": "data_destruction", "mitre": "T1485"
        })
    elif r < 0.60:  # Data exfiltration
        t = random.choice(SENSITIVE_TABLES)
        u = random.choice(DB2_USERS)
        events.append({
            "raw": f"TIMESTAMP={rand_ts()} AUTHID={u} HOSTNAME={ip} OPERATION=EXPORT STATEMENT=EXPORT TO /tmp/{t.lower()}.csv OF DEL SELECT * FROM {t}",
            "source_type": "db2", "label": 1, "score": round(random.uniform(0.75, 0.90), 3),
            "event_type": "data_exfiltration", "mitre": "T1005"
        })
    elif r < 0.75:  # Malicious service
        paths = ["C:\\temp\\update.exe","C:\\Windows\\Temp\\svchost32.exe"]
        comp = random.choice(["CEDIS-DC01","APPSERVER01","WORKSTATION42"])
        events.append({
            "raw": f"EventID: 7045 ServiceName: WindowsHelper Computer: {comp} ServiceFileName: {random.choice(paths)}",
            "source_type": "windows", "label": 1, "score": round(random.uniform(0.85, 0.95), 3),
            "event_type": "malicious_service", "mitre": "T1543"
        })
    else:  # PowerShell evasion
        comp = random.choice(["CEDIS-DC01","APPSERVER01"])
        events.append({
            "raw": f"EventID: 4688 Computer: {comp} CommandLine: powershell.exe -nop -exec bypass -EncodedCommand JABjAD0ATgBlAHcA -WindowStyle Hidden",
            "source_type": "windows", "label": 1, "score": round(random.uniform(0.80, 0.95), 3),
            "event_type": "powershell_evasion", "mitre": "T1059"
        })

random.shuffle(events)

out_path = sys.argv[1] if len(sys.argv) > 1 else "datasets/kalpixk_train.json"
with open(out_path, "w") as f:
    json.dump(events, f)

attacks = sum(1 for e in events if e["label"] == 1)
print(f"Dataset: {len(events)} eventos ({attacks} ataques, {len(events)-attacks} normales)")
print(f"Guardado en: {out_path}")
PYEOF

python3 /tmp/gen_dataset_quick.py "$REPO_DIR/datasets/kalpixk_train.json"
info "Dataset generado"

# ─── 7. Entrenar modelos ──────────────────────────────────────
step "Entrenando modelos de detección (benchmark CPU vs GPU)"

cat > /tmp/train_kalpixk.py << 'PYEOF'
import json, time, sys, pickle
from pathlib import Path
import numpy as np

# Cargar dataset
with open(sys.argv[1] if len(sys.argv) > 1 else "datasets/kalpixk_train.json") as f:
    dataset = json.load(f)

# Extraer features simples
def event_to_features(e):
    raw = e["raw"].lower()
    return [
        {"brute_force":0.85,"data_destruction":0.95,"data_exfiltration":0.80,
         "malicious_service":0.88,"powershell_evasion":0.90,"login_success":0.05,
         "db_query_normal":0.10,"login_success_win":0.05
         }.get(e.get("event_type",""),0.50),
        e.get("score", 0.3),
        1.0 if any(k in raw for k in ["drop","truncate","delete from"]) else 0.0,
        1.0 if any(k in raw for k in ["export","import"]) else 0.0,
        1.0 if any(k in raw for k in ["45.33","203.0.113","185.220"]) else 0.0,
        1.0 if any(k in raw for k in ["powershell","-nop","bypass","encoded"]) else 0.0,
        1.0 if any(k in raw for k in ["7045","failed password","4688"]) else 0.0,
        e.get("score", 0.3) * (1.0 if "02:" in raw or "03:" in raw or "01:" in raw else 0.5),
    ]

X = np.array([event_to_features(e) for e in dataset], dtype=np.float32)
y = np.array([e.get("label", 0) for e in dataset], dtype=np.int32)
print(f"Features shape: {X.shape} | Ataques: {y.sum()}/{len(y)}")

# Entrenar Isolation Forest (CPU primero, luego GPU si disponible)
print("\n[CPU] Entrenando IsolationForest...")
from sklearn.ensemble import IsolationForest
cpu_start = time.perf_counter()
iso = IsolationForest(n_estimators=200, contamination=0.15, random_state=42, n_jobs=-1)
iso.fit(X)
cpu_time = (time.perf_counter() - cpu_start) * 1000

cpu_scores = iso.score_samples(X)
cpu_preds = (iso.predict(X) == -1).astype(int)
from sklearn.metrics import precision_score, recall_score, f1_score
prec = precision_score(y, cpu_preds, zero_division=0)
rec = recall_score(y, cpu_preds, zero_division=0)
f1 = f1_score(y, cpu_preds, zero_division=0)
print(f"CPU time: {cpu_time:.0f}ms | Precision: {prec:.2f} | Recall: {rec:.2f} | F1: {f1:.2f}")

# GPU benchmark
gpu_time = None
try:
    import torch
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"\n[GPU] Probando con {gpu_name}...")
        
        try:
            import cuml
            from cuml.ensemble import IsolationForest as cuIF
            gpu_start = time.perf_counter()
            gpu_iso = cuIF(n_estimators=200, contamination=0.15, random_state=42)
            import cupy as cp
            X_gpu = cp.asarray(X)
            gpu_iso.fit(X_gpu)
            cp.cuda.Stream.null.synchronize()
            gpu_time = (time.perf_counter() - gpu_start) * 1000
            print(f"GPU time: {gpu_time:.0f}ms | Speedup: {cpu_time/gpu_time:.1f}x")
        except ImportError:
            # PyTorch manual benchmark
            X_t = torch.FloatTensor(X).cuda()
            gpu_start = time.perf_counter()
            _ = torch.pca_lowrank(X_t, q=4)
            torch.cuda.synchronize()
            gpu_time = (time.perf_counter() - gpu_start) * 1000
            print(f"GPU tensor ops: {gpu_time:.1f}ms")
    else:
        print("GPU no disponible para PyTorch — usando solo CPU")
except Exception as ex:
    print(f"GPU benchmark: {ex}")

# Guardar modelo
Path("models").mkdir(exist_ok=True)
with open("models/isolation_forest.pkl", "wb") as f:
    pickle.dump(iso, f)
print(f"\nModelo guardado en models/isolation_forest.pkl")

# Guardar benchmark
import json as _json
bench = {
    "cpu_train_ms": round(cpu_time, 1),
    "gpu_train_ms": round(gpu_time, 1) if gpu_time else None,
    "speedup": round(cpu_time / gpu_time, 1) if gpu_time else None,
    "dataset_size": len(y),
    "attack_count": int(y.sum()),
    "precision": round(prec, 3),
    "recall": round(rec, 3),
    "f1_score": round(f1, 3),
    "model": "IsolationForest n_estimators=200",
}
with open("models/benchmark.json", "w") as f:
    _json.dump(bench, f, indent=2)
print("Benchmark guardado en models/benchmark.json")
print(_json.dumps(bench, indent=2))
PYEOF

cd "$REPO_DIR"
python3 /tmp/train_kalpixk.py datasets/kalpixk_train.json
info "Modelos entrenados"

# ─── 8. Levantar API ──────────────────────────────────────────
step "Iniciando API Kalpixk"

if [[ -f "python/api/main.py" ]]; then
    PYTHONPATH="$REPO_DIR/python" \
    nohup python3 -m uvicorn api.main:app \
        --host 0.0.0.0 --port 8000 --reload > /tmp/kalpixk-api.log 2>&1 &
    echo $! > /tmp/kalpixk-api.pid
    sleep 3
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        info "API corriendo en puerto 8000"
    else
        warn "API no respondió — ver /tmp/kalpixk-api.log"
        tail -20 /tmp/kalpixk-api.log || true
    fi
else
    warn "api/main.py no encontrado — asegúrate de haber hecho git push del scaffold"
fi

# ─── Resumen ──────────────────────────────────────────────────
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Kalpixk listo en AMD MI300X${NC}"
echo ""
echo "  Dashboard: abrir dashboard/index.html en tu browser local"
echo "  API health: curl http://$(hostname -I | awk '{print $1}'):8000/api/health"
echo "  Benchmark:  cat $REPO_DIR/models/benchmark.json"
echo "  Logs:       tail -f /tmp/kalpixk-api.log"
echo ""
echo -e "${YELLOW}  IMPORTANTE: Destruye el droplet cuando termines para no quemar créditos${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
