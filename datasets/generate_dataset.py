"""
Kalpixk — Generador de Dataset de Ataque/Defensa
Blue Team defensivo: simula logs de ataques REALES para entrenar el modelo

Este script genera el dataset de entrenamiento que necesitas para el hackathon.
NO genera herramientas de ataque — genera logs que el SIEM debe DETECTAR.

Tipos de ataques simulados (basados en MITRE ATT&CK):
  T1110 — Brute Force (SSH, RDP, DB2)
  T1078 — Valid Accounts (sesiones anómalas)  
  T1485 — Data Destruction (DROP TABLE)
  T1005 — Data Collection (EXPORT masivo)
  T1543 — Create/Modify System Process (servicios maliciosos)
  T1136 — Create Account (usuarios no autorizados)
  T1059 — Command and Scripting Interpreter (PowerShell)

Uso:
  python datasets/generate_dataset.py --output datasets/kalpixk_train.json --size 5000
"""

import json
import random
import argparse
import datetime
from pathlib import Path

random.seed(42)

# ─── Configuración realista de CEDIS Cancún ───────────────────────────────────

INTERNAL_IPS = [f"192.168.{random.randint(1,5)}.{random.randint(1,254)}" for _ in range(50)]
EXTERNAL_MALICIOUS_IPS = ["45.33.32.156", "203.0.113.45", "185.220.101.35", "198.51.100.88", "91.108.56.130"]
LEGITIMATE_USERS = ["jjuarez", "lbasto", "aquintana", "ireyes", "cedis_app", "wms_svc", "backup_usr"]
DB2_USERS = ["CEDIS_APP", "CEDIS_USR", "WMS_SVC", "BACKUP_SVC", "DBA_ADMIN"]
SENSITIVE_TABLES = ["NOMINAS", "EMPLEADOS", "INVENTARIO", "BILLING", "WMS_USER", "ORDER_HEADER", "SHIPMENT"]
SAFE_TABLES = ["CATALOGO_PRODUCTOS", "RUTAS", "ALMACENES", "UNIDADES"]
WINDOWS_COMPUTERS = ["CEDIS-DC01", "APPSERVER01", "WORKSTATION42", "WS-JJUAREZ", "WS-LBASTO"]
PROCESSES = ["sshd", "cron", "systemd", "sudo", "python3", "java", "db2sysc"]

def rand_ts(hours_back=72):
    base = datetime.datetime.now()
    delta = datetime.timedelta(seconds=random.randint(0, hours_back * 3600))
    return (base - delta).strftime("%Y-%m-%dT%H:%M:%SZ")

def rand_ts_syslog(hours_back=72):
    base = datetime.datetime.now()
    delta = datetime.timedelta(seconds=random.randint(0, hours_back * 3600))
    dt = base - delta
    return dt.strftime("Apr %d %H:%M:%S")

def is_off_hours(ts_str):
    try:
        if "T" in ts_str:
            hour = int(ts_str[11:13])
        else:
            parts = ts_str.split()
            hour = int(parts[-1].split(":")[0]) if parts else 12
        return hour < 7 or hour >= 20
    except:
        return False

# ─── Generadores de logs normales ─────────────────────────────────────────────

def gen_normal_ssh_login():
    user = random.choice(LEGITIMATE_USERS)
    src = random.choice(INTERNAL_IPS)
    port = random.randint(40000, 60000)
    ts = rand_ts_syslog()
    return {
        "raw": f"{ts} cancun-srv01 sshd[{random.randint(1000,9999)}]: Accepted publickey for {user} from {src} port {port}",
        "source_type": "syslog", "label": 0, "score": 0.10,
        "event_type": "login_success", "user": user, "src_ip": src
    }

def gen_normal_db2_query():
    user = random.choice(DB2_USERS[:3])
    table = random.choice(SAFE_TABLES)
    host = random.choice(INTERNAL_IPS[:10])
    ts = rand_ts()
    return {
        "raw": f"TIMESTAMP={ts.replace('-','').replace(':','.').replace('T','-').replace('Z','')} AUTHID={user} HOSTNAME={host} OPERATION=EXECUTE STATEMENT=SELECT * FROM {table} WHERE ALMACEN='CUN427'",
        "source_type": "db2", "label": 0, "score": 0.12,
        "event_type": "db_query_normal", "user": user, "src_ip": host
    }

def gen_normal_cron():
    ts = rand_ts_syslog()
    return {
        "raw": f"{ts} cedis-app cron[{random.randint(1000,9999)}]: (root) CMD (/usr/local/bin/backup.sh)",
        "source_type": "syslog", "label": 0, "score": 0.08,
        "event_type": "scheduled_task_normal", "user": "root", "src_ip": "127.0.0.1"
    }

# ─── Generadores de ataques (T1110 — Brute Force) ─────────────────────────────

def gen_brute_force_ssh():
    """T1110 — Ataque de fuerza bruta SSH contra usuarios privilegiados"""
    attacker = random.choice(EXTERNAL_MALICIOUS_IPS)
    target_user = random.choice(["root", "admin", "administrator", "ubuntu"])
    ts = rand_ts_syslog()
    port = random.randint(40000, 60000)
    score = 0.85 + random.uniform(0, 0.10)
    return {
        "raw": f"{ts} cancun-srv01 sshd[{random.randint(1000,9999)}]: Failed password for {target_user} from {attacker} port {port}",
        "source_type": "syslog", "label": 1, "score": round(score, 3),
        "event_type": "brute_force_ssh", "mitre": "T1110",
        "user": target_user, "src_ip": attacker,
        "description": f"Brute force SSH contra {target_user} desde IP externa {attacker}"
    }

def gen_brute_force_db2():
    """T1110 — Fuerza bruta contra autenticación DB2"""
    attacker = random.choice(EXTERNAL_MALICIOUS_IPS)
    ts = rand_ts()
    score = 0.80 + random.uniform(0, 0.10)
    return {
        "raw": f"TIMESTAMP={ts} AUTHID=UNKNOWN_USER HOSTNAME={attacker} OPERATION=CONNECT SQLCODE=-1035 REASON=AUTHENTICATION_FAILURE ATTEMPTS={random.randint(5,50)}",
        "source_type": "db2", "label": 1, "score": round(score, 3),
        "event_type": "brute_force_db2", "mitre": "T1110",
        "user": "UNKNOWN_USER", "src_ip": attacker,
        "description": f"Múltiples fallos de autenticación DB2 desde {attacker}"
    }

# ─── T1485 — Data Destruction ─────────────────────────────────────────────────

def gen_data_destruction():
    """T1485 — Destrucción de datos críticos del WMS"""
    user = random.choice(DB2_USERS[2:])
    table = random.choice(SENSITIVE_TABLES)
    attacker_host = random.choice(EXTERNAL_MALICIOUS_IPS + [random.choice(INTERNAL_IPS)])
    ts = rand_ts()
    score = 0.92 + random.uniform(0, 0.07)
    ops = ["DROP TABLE", "TRUNCATE TABLE", "DELETE FROM"]
    op = random.choice(ops)
    return {
        "raw": f"TIMESTAMP={ts} AUTHID={user} HOSTNAME={attacker_host} OPERATION=DDL STATEMENT={op} {table}",
        "source_type": "db2", "label": 1, "score": round(score, 3),
        "event_type": "data_destruction", "mitre": "T1485",
        "user": user, "src_ip": attacker_host,
        "description": f"Operación destructiva {op} en tabla sensible {table}"
    }

# ─── T1005 — Data Collection / Exfiltración ───────────────────────────────────

def gen_data_exfiltration():
    """T1005 — Exportación masiva de datos sensibles"""
    user = random.choice(DB2_USERS)
    table = random.choice(SENSITIVE_TABLES)
    dst = f"/tmp/{table.lower()}_{random.randint(100,999)}.csv"
    attacker = random.choice(INTERNAL_IPS[30:] + EXTERNAL_MALICIOUS_IPS[:2])
    ts = rand_ts()
    score = 0.78 + random.uniform(0, 0.12)
    return {
        "raw": f"TIMESTAMP={ts} AUTHID={user} HOSTNAME={attacker} OPERATION=EXPORT STATEMENT=EXPORT TO {dst} OF DEL SELECT * FROM {table}",
        "source_type": "db2", "label": 1, "score": round(score, 3),
        "event_type": "data_exfiltration", "mitre": "T1005",
        "user": user, "src_ip": attacker,
        "description": f"Exportación masiva de tabla {table} a archivo externo"
    }

# ─── T1543 — Malicious Service ────────────────────────────────────────────────

def gen_malicious_service():
    """T1543 — Servicio malicioso instalado en ruta sospechosa"""
    computer = random.choice(WINDOWS_COMPUTERS)
    paths = ["C:\\temp\\update.exe", "C:\\Windows\\Temp\\svchost32.exe", 
             "C:\\Users\\Public\\service.exe", "%APPDATA%\\microsoft\\service.dll"]
    svc_path = random.choice(paths)
    svc_names = ["WindowsUpdate", "MicrosoftHelp", "SystemService32", "WmiProviderHost"]
    ts = rand_ts()
    score = 0.88 + random.uniform(0, 0.08)
    return {
        "raw": f"EventID: 7045 ServiceName: {random.choice(svc_names)} Computer: {computer} ServiceFileName: {svc_path} ServiceAccount: LocalSystem",
        "source_type": "windows", "label": 1, "score": round(score, 3),
        "event_type": "malicious_service", "mitre": "T1543",
        "user": "SYSTEM", "src_ip": computer,
        "description": f"Servicio instalado en ruta sospechosa {svc_path} en {computer}"
    }

# ─── T1136 — Account Creation ─────────────────────────────────────────────────

def gen_unauthorized_account():
    """T1136 — Creación de cuenta no autorizada"""
    new_user = f"support_{random.randint(100,999)}"
    creator = random.choice(["administrator", "SYSTEM"])
    computer = random.choice(WINDOWS_COMPUTERS[:2])
    ts = rand_ts()
    score = 0.72 + random.uniform(0, 0.15)
    off_hours = True
    return {
        "raw": f"EventID: 4720 SubjectUserName: {creator} TargetUserName: {new_user} Computer: {computer} IpAddress: {random.choice(EXTERNAL_MALICIOUS_IPS)}",
        "source_type": "windows", "label": 1, "score": round(score, 3),
        "event_type": "unauthorized_account", "mitre": "T1136",
        "user": creator, "src_ip": computer,
        "description": f"Cuenta {new_user} creada por {creator} en {computer}"
    }

# ─── T1059 — PowerShell / Command Injection ───────────────────────────────────

def gen_powershell_attack():
    """T1059 — Ejecución de PowerShell con técnicas de evasión"""
    encoded_cmds = [
        "powershell.exe -WindowStyle Hidden -EncodedCommand JAB...",
        "powershell -nop -exec bypass -c IEX (New-Object Net.WebClient).DownloadString",
        "powershell.exe -c \"Invoke-Expression (Get-Content C:\\temp\\script.ps1)\""
    ]
    computer = random.choice(WINDOWS_COMPUTERS)
    user = random.choice(["administrator", "SYSTEM", "www-data"])
    ts = rand_ts()
    score = 0.82 + random.uniform(0, 0.12)
    return {
        "raw": f"EventID: 4688 Computer: {computer} SubjectUserName: {user} CommandLine: {random.choice(encoded_cmds)} ParentImage: C:\\Windows\\System32\\cmd.exe",
        "source_type": "windows", "label": 1, "score": round(score, 3),
        "event_type": "powershell_evasion", "mitre": "T1059",
        "user": user, "src_ip": computer,
        "description": f"PowerShell con técnicas de evasión ejecutado por {user} en {computer}"
    }

# ─── T1078 — Privilege Escalation ─────────────────────────────────────────────

def gen_privilege_escalation():
    """T1078 — Uso de cuenta privilegiada en horario anómalo"""
    ts = rand_ts()
    priv_user = random.choice(["root", "administrator", "svc_manhattan", "DBA_ADMIN"])
    src = random.choice(EXTERNAL_MALICIOUS_IPS + INTERNAL_IPS[40:])
    score = 0.75 + random.uniform(0, 0.15)
    return {
        "raw": f"EventID: 4672 SubjectUserName: {priv_user} Computer: {random.choice(WINDOWS_COMPUTERS)} LogonType: 3 IpAddress: {src} WorkstationName: UNKNOWN",
        "source_type": "windows", "label": 1, "score": round(score, 3),
        "event_type": "privilege_logon", "mitre": "T1078",
        "user": priv_user, "src_ip": src,
        "description": f"Inicio de sesión privilegiado de {priv_user} desde {src}"
    }

# ─── T1560 — Large Network Transfer ──────────────────────────────────────────

def gen_large_transfer():
    """Transferencia masiva de datos vía red — potencial C2 o exfiltración"""
    src = random.choice(INTERNAL_IPS[:20])
    dst = random.choice(EXTERNAL_MALICIOUS_IPS)
    bytes_amt = random.randint(100_000_000, 2_000_000_000)
    port = random.choice([443, 80, 8080, 4444, 1337])
    score = 0.70 + random.uniform(0, 0.15)
    return {
        "raw": f"{src} {dst} {random.randint(40000,60000)} {port} TCP {bytes_amt} {random.randint(1000,50000)}",
        "source_type": "netflow", "label": 1, "score": round(score, 3),
        "event_type": "large_data_transfer", "mitre": "T1041",
        "user": None, "src_ip": src,
        "description": f"Transferencia de {bytes_amt//1024//1024}MB a IP externa {dst}:{port}"
    }

# ─── Generador principal ──────────────────────────────────────────────────────

ATTACK_GENERATORS = [
    (gen_brute_force_ssh, 0.20),
    (gen_brute_force_db2, 0.08),
    (gen_data_destruction, 0.07),
    (gen_data_exfiltration, 0.10),
    (gen_malicious_service, 0.08),
    (gen_unauthorized_account, 0.07),
    (gen_powershell_attack, 0.08),
    (gen_privilege_escalation, 0.12),
    (gen_large_transfer, 0.10),
]

NORMAL_GENERATORS = [
    gen_normal_ssh_login,
    gen_normal_db2_query,
    gen_normal_cron,
]

def generate_dataset(n_samples: int = 5000, attack_ratio: float = 0.15) -> list:
    """Generar dataset balanceado con n_samples eventos"""
    dataset = []
    n_attacks = int(n_samples * attack_ratio)
    n_normal = n_samples - n_attacks

    print(f"Generando {n_normal} eventos normales...")
    for _ in range(n_normal):
        gen = random.choice(NORMAL_GENERATORS)
        event = gen()
        event["timestamp"] = rand_ts()
        dataset.append(event)

    print(f"Generando {n_attacks} eventos de ataque...")
    for _ in range(n_attacks):
        r = random.random()
        cumulative = 0.0
        selected_gen = ATTACK_GENERATORS[0][0]
        for gen_fn, weight in ATTACK_GENERATORS:
            cumulative += weight
            if r <= cumulative:
                selected_gen = gen_fn
                break
        event = selected_gen()
        event["timestamp"] = rand_ts()
        dataset.append(event)

    random.shuffle(dataset)
    print(f"Dataset generado: {len(dataset)} eventos ({n_attacks} ataques, {n_normal} normales)")
    return dataset

def dataset_to_features(dataset: list) -> tuple:
    """Convertir dataset a matrix de features [N, 32] para el modelo"""

    features = []
    labels = []

    for evt in dataset:
        lower = evt["raw"].lower()
        hour = 12
        try:
            if "T" in evt.get("timestamp", ""):
                hour = int(evt["timestamp"][11:13])
        except:
            pass

        f = [0.0] * 32
        f[0] = {"login_success": 0.05, "login_failure": 0.35, "brute_force_ssh": 0.85,
                "db_query_normal": 0.10, "data_destruction": 0.95, "data_exfiltration": 0.80,
                "malicious_service": 0.88, "unauthorized_account": 0.75, "powershell_evasion": 0.90,
                "privilege_logon": 0.78, "large_data_transfer": 0.70, "scheduled_task_normal": 0.05
                }.get(evt.get("event_type", ""), 0.50)
        f[1] = evt.get("score", 0.3)
        f[2] = hour / 23.0
        f[5] = 1.0 if (hour < 7 or hour >= 20) else 0.0
        src = evt.get("src_ip", "")
        f[6] = 1.0 if (src.startswith("10.") or src.startswith("192.168.") or src.startswith("172.")) else 0.0
        f[8] = 1.0 if evt.get("user") else 0.0
        f[15] = 1.0 if any(k in lower for k in ["select", "insert", "update", "delete", "drop", "grant"]) else 0.0
        f[16] = 1.0 if any(k in lower for k in ["drop ", "truncate", "delete from"]) else 0.0
        f[17] = 1.0 if any(t.lower() in lower for t in ["nominas", "empleados", "billing", "salary"]) else 0.0
        f[18] = 1.0 if any(k in lower for k in ["export", "import", "load "]) else 0.0
        f[20] = 1.0 if evt.get("user", "").lower() in ["root", "admin", "administrator", "dba_admin", "system"] else 0.0
        f[24] = min(len(evt["raw"]) / 500.0, 1.0)
        f[25] = 1.0 if any(k in lower for k in ["encoded", "aaqiaaiac", "base64"]) else 0.0
        f[26] = 1.0 if any(k in lower for k in ["powershell", "-nop", "bypass", "invoke-expression", "iex "]) else 0.0
        eid = 0
        m = __import__('re').search(r'EventID: (\d+)', evt["raw"])
        if m: eid = int(m.group(1))
        f[27] = {4625: 0.50, 4672: 0.80, 4720: 0.70, 7045: 0.90, 4688: 0.70}.get(eid, 0.20)
        f[30] = f[1] * f[5]
        f[31] = f[16] * f[8]

        features.append(f)
        labels.append(evt.get("label", 0))

    return features, labels

def main():
    parser = argparse.ArgumentParser(description="Generar dataset Blue Team para Kalpixk")
    parser.add_argument("--output", default="datasets/kalpixk_train.json")
    parser.add_argument("--size", type=int, default=5000)
    parser.add_argument("--attack-ratio", type=float, default=0.15)
    parser.add_argument("--export-npy", action="store_true", help="Exportar también como .npy para PyTorch")
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    dataset = generate_dataset(args.size, args.attack_ratio)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Dataset JSON guardado: {args.output} ({Path(args.output).stat().st_size // 1024}KB)")

    if args.export_npy:
        try:
            import numpy as np
            features, labels = dataset_to_features(dataset)
            X = np.array(features, dtype=np.float32)
            y = np.array(labels, dtype=np.int32)
            X_path = args.output.replace(".json", "_X.npy")
            y_path = args.output.replace(".json", "_y.npy")
            np.save(X_path, X)
            np.save(y_path, y)
            print(f"Features matrix: {X.shape} → {X_path}")
            print(f"Labels: {y.sum()} ataques de {len(y)} total ({100*y.mean():.1f}%)")
        except ImportError:
            print("numpy no disponible — solo se generó JSON")

    print("\n=== Resumen del dataset ===")
    from collections import Counter
    types = Counter(e.get("event_type", "unknown") for e in dataset)
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        label = "ATAQUE" if any(e.get("label") == 1 and e.get("event_type") == t for e in dataset) else "normal"
        print(f"  {t:<35} {c:>5} ({label})")

if __name__ == "__main__":
    main()
