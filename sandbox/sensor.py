"""
Kalpixk — Real-time Sensor
Lee /sandbox/logs/events.jsonl, extrae 32 features reales,
y las envía a la API Kalpixk via HTTP POST /analyze.
"""
import json
import time
import math
import os
import logging
import requests
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SENSOR] %(message)s")
log = logging.getLogger("sensor")

LOGS_PATH = Path("/sandbox/logs/events.jsonl")
API_URL = os.getenv("KALPIXK_API", "http://defender:8000")
POLL_INTERVAL = 0.25  # segundos

# Mapeo de tipos de evento a riesgo base
EVENT_RISK = {
    "RANSOMWARE_START": 0.95, "RANSOMWARE_DONE": 0.99, "FILE_ENCRYPTED": 0.90,
    "SSH_BRUTE": 0.75, "EXFIL_SENT": 0.95, "FILE_READ_SENSITIVE": 0.65,
    "PRIVESC_FILE_WRITE": 0.85, "PRIVESC_ATTEMPT": 0.80,
    "DATA_READ_SENSITIVE": 0.60, "EXFIL_COMPLETE": 0.90,
    "FILE_ENCRYPTED": 0.88,
}
NORMAL_EVENTS = {"FILE_READ", "FILE_WRITE", "PROCESS_START", "NET_CONNECT"}

def shannon_entropy(data: bytes) -> float:
    if not data: return 0.0
    freq = [0] * 256
    for b in data: freq[b] += 1
    n = len(data)
    h = 0.0
    for f in freq:
        if f > 0:
            p = f / n
            h -= p * math.log2(p)
    return h / 8.0  # normalizado [0,1]

def extract_features(event: dict) -> list[float]:
    """Extrae el vector de 32 features del contrato kalpixk.wit"""
    etype = event.get("event", "UNKNOWN")
    ts = event.get("ts", "")
    hour = int(ts[11:13]) if len(ts) > 13 else 12
    dow = datetime.fromisoformat(ts[:19]).weekday() if ts else 3

    risk = EVENT_RISK.get(etype, 0.1)
    is_destructive = 1.0 if any(k in etype for k in ["ENCRYPT","DROP","DELETE","EXFIL","PRIVESC"]) else 0.0
    is_net = 1.0 if any(k in etype for k in ["SSH","BRUTE","EXFIL","C2"]) else 0.0
    is_privesc = 1.0 if "PRIV" in etype else 0.0
    is_ransomware = 1.0 if "RANSOMWARE" in etype or "ENCRYPT" in etype else 0.0
    entropy_val = float(event.get("entropy", risk * 0.9))
    file_bytes = float(event.get("bytes", event.get("size_bytes", 0)))
    bytes_norm = min(math.log10(file_bytes + 1) / 7.0, 1.0)
    attempt = min(float(event.get("attempt", 0)) / 20.0, 1.0)
    is_offhours = 1.0 if hour < 7 or hour > 22 else 0.0
    is_sensitive = 1.0 if any(k in str(event) for k in ["nominas","passwd","sudoers","clientes","inventario"]) else 0.0

    # 32 features del contrato WIT
    features = [
        # Temporales
        hour / 23.0,           # 0: hora normalizada
        dow / 6.0,             # 1: día semana
        is_offhours,           # 2: fuera de horario
        1.0 if dow >= 5 else 0.0,  # 3: fin de semana

        # Tipo y riesgo de evento
        risk,                  # 4: riesgo base del evento
        is_destructive,        # 5: operación destructiva
        is_net,                # 6: actividad de red
        is_privesc,            # 7: escalada de privilegios
        is_ransomware,         # 8: firma de ransomware

        # Entropía y volumen
        entropy_val,           # 9: entropía del archivo/payload
        bytes_norm,            # 10: tamaño normalizado (log10)
        attempt,               # 11: intento número (brute force)

        # Sensibilidad
        is_sensitive,          # 12: archivo sensible
        1.0 if "root" in str(event) else 0.0,  # 13: usuario privilegiado
        1.0 if "0.0.0.0" in str(event) or "c2" in str(event) else 0.0,  # 14: destino externo

        # Señales de MITRE ATT&CK
        1.0 if "T1486" in str(event) or is_ransomware else 0.0,  # 15: T1486
        1.0 if "T1110" in str(event) or "BRUTE" in etype else 0.0,  # 16: T1110
        1.0 if "T1041" in str(event) or "EXFIL" in etype else 0.0,  # 17: T1041
        1.0 if "T1548" in str(event) or is_privesc else 0.0,  # 18: T1548

        # Scores compuestos
        (risk + is_destructive + entropy_val) / 3.0,  # 19: composite_threat
        (is_net + attempt + is_offhours) / 3.0,       # 20: composite_network
        (is_sensitive + is_privesc) / 2.0,             # 21: composite_data_risk

        # Padding con variaciones contextuales
        risk * entropy_val,                   # 22
        is_destructive * is_offhours,          # 23
        is_ransomware * bytes_norm,            # 24
        min(risk + attempt, 1.0),              # 25
        is_net * is_offhours,                  # 26
        is_sensitive * is_destructive,         # 27
        (risk + is_net + is_destructive) / 3,  # 28
        entropy_val * is_ransomware,           # 29
        is_privesc * is_offhours,              # 30
        risk * risk,                           # 31: risk cuadrático
    ]
    return features

def run():
    log.info(f"Sensor iniciado. Monitoreando: {LOGS_PATH}")
    log.info(f"API destino: {API_URL}")

    # Esperar hasta que exista el archivo
    while not LOGS_PATH.exists():
        log.info("Esperando archivo de logs...")
        time.sleep(1)

    # Esperar que la API esté lista
    for _ in range(30):
        try:
            r = requests.get(f"{API_URL}/status", timeout=2)
            if r.status_code == 200:
                log.info("API lista.")
                break
        except Exception:
            pass
        time.sleep(2)

    # Entrenar modelo con datos normales primero
    try:
        r = requests.post(f"{API_URL}/train?n_samples=2000", timeout=10)
        log.info(f"Modelo entrenado: {r.json()}")
    except Exception as e:
        log.warning(f"Train error: {e}")

    last_pos = 0
    while True:
        try:
            with open(LOGS_PATH, "r") as f:
                f.seek(last_pos)
                lines = f.readlines()
                last_pos = f.tell()

            for line in lines:
                line = line.strip()
                if not line: continue
                try:
                    event = json.loads(line)
                    features = extract_features(event)
                    payload = {
                        "features": features,
                        "raw_log": json.dumps(event),
                        "source": event.get("event", "UNKNOWN")
                    }
                    r = requests.post(f"{API_URL}/analyze", json=payload, timeout=3)
                    result = r.json()
                    sev = result.get("severity","?")
                    score = result.get("anomaly_score", 0)
                    log.info(f"[{sev}] {event.get('event')} score={score:.4f}")
                except Exception as e:
                    log.error(f"Error procesando evento: {e}")

        except Exception as e:
            log.error(f"Error leyendo logs: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run()
