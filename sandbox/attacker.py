"""
Kalpixk — Attacker Simulator
Genera ataques REALES dentro del sandbox Docker aislado.
NO sale de la red Docker. Produce eventos reales que el sensor captura.
"""
import os
import time
import socket
import json
import struct
import hashlib
import logging
import random
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ATTACKER] %(message)s")
log = logging.getLogger("attacker")

TARGET_DIR = Path("/sandbox/target")
TARGET_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR = Path("/sandbox/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def emit(event_type: str, details: dict):
    event = {"ts": datetime.utcnow().isoformat(), "event": event_type, **details}
    with open(LOGS_DIR / "events.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")

def attack_ransomware():
    log.info("T1486 — Ransomware")
    key = os.urandom(16)
    for i in range(30):
        p = TARGET_DIR / f"doc_{i:03d}.txt"
        p.write_text(f"Factura #{random.randint(1000,9999)} CEDIS Cancún\n" * 100)
    emit("RANSOMWARE_START", {"key_hash": hashlib.md5(key).hexdigest(), "targets": 30})
    time.sleep(0.5)
    encrypted = 0
    for p in sorted(TARGET_DIR.glob("*.txt")):
        data = p.read_bytes()
        enc = bytes(b ^ key[i % 16] for i, b in enumerate(data))
        p.with_suffix(".enc").write_bytes(enc)
        p.unlink()
        emit("FILE_ENCRYPTED", {"file": p.name, "bytes": len(data), "entropy": len(set(enc))/256})
        encrypted += 1
        time.sleep(0.03)
    emit("RANSOMWARE_DONE", {"encrypted": encrypted})

def attack_ssh_brute():
    log.info("T1110 — SSH Brute Force")
    host = os.getenv("HONEYPOT_HOST", "honeypot")
    port = int(os.getenv("HONEYPOT_PORT", "2222"))
    passwords = ["admin","123456","root","password","toor","letmein","qwerty","abc123","1234","pass"]
    for attempt, pwd in enumerate(passwords * 2):
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect((host, port))
            s.recv(256)
            s.send(f"USER root\r\nPASS {pwd}\r\n".encode())
            s.close()
        except Exception:
            pass
        emit("SSH_BRUTE", {"host": host, "port": port, "attempt": attempt+1, "pwd_len": len(pwd)})
        time.sleep(0.1)

def attack_exfil():
    log.info("T1041 — Data Exfiltration")
    files = {"nominas.db": 5000, "inventario.csv": 8000, "clientes.json": 3000}
    payload = b""
    for fname, size in files.items():
        p = TARGET_DIR / fname
        data = os.urandom(size)
        p.write_bytes(data)
        payload += struct.pack(">I", len(data)) + data
        emit("FILE_READ_SENSITIVE", {"file": fname, "bytes": size})
        time.sleep(0.2)
    out = Path("/tmp/exfil.bin")
    out.write_bytes(payload)
    emit("EXFIL_SENT", {"total_bytes": len(payload), "dest": "c2_external"})

def attack_privesc():
    log.info("T1548 — Privilege Escalation")
    for fname in ["etc_passwd", "sudoers", "crontab"]:
        p = TARGET_DIR / fname
        p.write_text("root:x:0:0::/root:/bin/bash\nattacker:x:0:0::/:/bin/sh\n")
        emit("PRIVESC_FILE_WRITE", {"file": fname, "added_uid0": True})
        time.sleep(0.3)

ATTACKS = {
    "ransomware": attack_ransomware,
    "ssh_brute": attack_ssh_brute,
    "exfil": attack_exfil,
    "privesc": attack_privesc,
}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ATTACKS:
        ATTACKS[mode]()
    else:
        for name, fn in ATTACKS.items():
            log.info(f"--- {name} ---")
            try: fn()
            except Exception as e: log.error(f"{name} error: {e}")
            time.sleep(3)
