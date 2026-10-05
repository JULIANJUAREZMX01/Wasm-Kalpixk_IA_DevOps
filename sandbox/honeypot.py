"""
Kalpixk — SSH Honeypot
Escucha en puerto 2222, registra intentos de autenticación reales.
"""
import socket
import threading
import logging
import json
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [HONEYPOT] %(message)s")
log = logging.getLogger("honeypot")
LOGS_DIR = Path("/sandbox/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def emit(event_type: str, details: dict):
    event = {"ts": datetime.utcnow().isoformat(), "event": event_type, **details}
    with open(LOGS_DIR / "events.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")

def handle(conn, addr):
    try:
        conn.send(b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6\r\n")
        data = conn.recv(512).decode(errors="ignore")
        emit("SSH_BRUTE", {
            "src_ip": addr[0],
            "src_port": addr[1],
            "payload": data[:200],
            "attempt": 1,
        })
        log.info(f"Intento SSH desde {addr[0]}:{addr[1]}")
    except Exception:
        pass
    finally:
        conn.close()

def run():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 2222))
    s.listen(50)
    log.info("Honeypot SSH escuchando en :2222")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    run()
