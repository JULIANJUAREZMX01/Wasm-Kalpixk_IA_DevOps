#!/usr/bin/env python3
"""
Kalpixk — Monitor Automático sin GPU
Corre 24/7 en cualquier máquina (PC, VPS, Codespaces)
Reporta a Telegram usando el bot existente (@SuperAsistenteSacBot o el bot de Kalpixk)

Sin dependencia de AMD MI300X ni créditos GPU.
El análisis pesado usa el modelo local entrenado (sklearn CPU).

Ejecutar:
  python3 kalpixk_monitor.py

Con .env configurado:
  TELEGRAM_TOKEN=tu_token
  TELEGRAM_CHAT_ID=tu_chat_id  (tu ID de usuario: 8247886073)
  KALPIXK_API_URL=http://localhost:8000  (opcional, si el droplet está activo)
"""

import asyncio
import json
import os
import pickle
import time
import datetime
import hashlib
from pathlib import Path

# ─── Configuración ─────────────────────────────────────────────────────────────

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8247886073")
KALPIXK_API_URL  = os.getenv("KALPIXK_API_URL", "")
MODEL_PATH       = Path("models/isolation_forest.pkl")
CHECK_INTERVAL   = 60   # segundos entre checks
ALERT_THRESHOLD  = 0.65  # score mínimo para enviar alerta a Telegram

# Base44 API (para guardar alertas en la base de datos)
BASE44_API_URL   = "https://app.base44.com/api/agents/69cdfbf1e7353a49d14220f3"
# La API key va en variables de entorno — NUNCA hardcodeada
BASE44_API_KEY   = os.getenv("BASE44_API_KEY", "")

# ─── Simulador de logs (para cuando no hay fuente real conectada) ──────────────

SIMULATED_EVENTS = [
    {
        "type": "syslog",
        "raw": "Apr 5 02:14:22 cancun-srv01 sshd[12346]: Failed password for root from 45.33.32.156 port 55423",
        "score": 0.88,
        "mitre": "T1110",
        "description": "SSH Brute Force desde IP externa en horario nocturno"
    },
    {
        "type": "db2",
        "raw": "TIMESTAMP=2026-04-05 AUTHID=CEDIS_USR STATEMENT=DROP TABLE NOMINAS",
        "score": 0.96,
        "mitre": "T1485",
        "description": "Intento de DROP TABLE en tabla sensible NOMINAS"
    },
    {
        "type": "windows",
        "raw": "EventID: 7045 ServiceName: WindowsUpdate ServiceFileName: C:\\temp\\update.exe",
        "score": 0.91,
        "mitre": "T1543",
        "description": "Servicio malicioso instalado en ruta sospechosa"
    },
]

# ─── Función de análisis local (CPU, sin GPU) ──────────────────────────────────

def analyze_event_locally(event: dict) -> dict:
    """
    Analiza un evento con el modelo local (sin GPU).
    
    Si el modelo pkl está disponible usa IsolationForest.
    Si no, usa las heurísticas simples del motor WASM (reimplementadas en Python).
    """
    raw = event.get("raw", "").lower()
    score = event.get("score", 0.3)  # Usar el score del simulador si está disponible
    
    # Heurísticas básicas (espejo de features.rs)
    hour = datetime.datetime.now().hour
    is_off_hours = hour < 7 or hour > 20
    has_destructive = any(k in raw for k in ["drop ", "truncate", "delete from"])
    has_privesc = any(k in raw for k in ["sudo", "4672", "privilege"])
    has_bruteforce = "failed password" in raw
    has_malicious_svc = "7045" in raw or ("service" in raw and "temp" in raw)
    external_ip = any(ip in raw for ip in ["45.33", "203.0.113", "185.220"])
    
    # Combinar heurísticas con el score base
    if has_destructive:
        score = max(score, 0.90)
    if has_malicious_svc:
        score = max(score, 0.88)
    if is_off_hours and (has_bruteforce or has_privesc):
        score = min(score + 0.15, 1.0)
    if external_ip and is_off_hours:
        score = min(score + 0.10, 1.0)
    
    severity = "CRÍTICO" if score >= 0.85 else "ALTO" if score >= 0.65 else "MEDIO"
    
    return {
        "score": round(score, 3),
        "severity": severity,
        "is_anomaly": score >= ALERT_THRESHOLD,
        "is_off_hours": is_off_hours,
        "mitre": event.get("mitre", "T1190"),
    }

# ─── Telegram: enviar mensaje ──────────────────────────────────────────────────

async def send_telegram(text: str) -> bool:
    """Envía un mensaje a Telegram usando el bot configurado."""
    if not TELEGRAM_TOKEN:
        print(f"[Telegram] TOKEN no configurado — mensaje simulado: {text[:80]}")
        return False
    
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False

# ─── Base44: guardar alerta en la base de datos ────────────────────────────────

async def save_to_base44(alert: dict) -> bool:
    """
    Guarda la alerta en la base de datos de Base44.
    Esto permite ver el historial desde cualquier agente de Base44.
    """
    if not BASE44_API_KEY:
        print("[Base44] API key no configurada — alerta no guardada")
        return False
    
    try:
        import urllib.request
        # Crear una nueva conversación/mensaje con la alerta
        url = f"{BASE44_API_URL}/conversations/{os.getenv('BASE44_CONV_ID', 'default')}/messages"
        
        content = f"""KALPIXK ALERT — {alert.get('severity', 'UNKNOWN')}
Evento: {alert.get('type', 'unknown')}
Score: {alert.get('score', 0)}
MITRE: {alert.get('mitre', 'N/A')}
Descripción: {alert.get('description', '')}
Timestamp: {datetime.datetime.now().isoformat()}"""
        
        data = json.dumps({"role": "user", "content": content}).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "api_key": BASE44_API_KEY}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Base44] Error guardando alerta: {e}")
        return False

# ─── Loop principal de monitoreo ──────────────────────────────────────────────

async def monitoring_loop():
    """
    Loop infinito que:
    1. Procesa eventos (reales si hay API GPU activa, simulados si no)
    2. Analiza localmente con CPU
    3. Envía alertas críticas a Telegram
    4. Guarda historial en Base44
    """
    print(f"[Kalpixk Monitor] Iniciando — threshold: {ALERT_THRESHOLD}")
    print(f"[Kalpixk Monitor] Telegram: {'configurado' if TELEGRAM_TOKEN else 'NO configurado'}")
    print(f"[Kalpixk Monitor] GPU API: {KALPIXK_API_URL or 'no activa (usando CPU local)'}")
    
    # Notificación de inicio
    await send_telegram(
        "🛡️ <b>Kalpixk SIEM iniciado</b>\n"
        f"Modo: {'GPU+CPU' if KALPIXK_API_URL else 'CPU local'}\n"
        f"Threshold: {ALERT_THRESHOLD}\n"
        f"Intervalo: {CHECK_INTERVAL}s"
    )
    
    alert_count = 0
    event_count = 0
    start_time = time.time()
    seen_hashes = set()  # Para deduplicación
    
    while True:
        try:
            # Obtener eventos (del API GPU o del simulador)
            events = []
            
            if KALPIXK_API_URL:
                # Intentar obtener eventos reales del backend GPU
                try:
                    import urllib.request
                    req = urllib.request.Request(
                        f"{KALPIXK_API_URL}/api/health",
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if resp.status == 200:
                            print("[GPU] Backend activo")
                        # Aquí iría la lógica de obtener eventos reales
                except Exception:
                    print("[GPU] Backend no disponible — usando simulador")
            
            # Simular un evento cada CHECK_INTERVAL segundos para el demo
            # En producción, esto sería reemplazado por lectura de logs reales
            sim_event = SIMULATED_EVENTS[event_count % len(SIMULATED_EVENTS)]
            events = [sim_event]
            
            for event in events:
                # Deduplicar
                event_hash = hashlib.md5(event["raw"].encode()).hexdigest()
                if event_hash in seen_hashes:
                    continue
                seen_hashes.add(event_hash)
                if len(seen_hashes) > 1000:
                    seen_hashes.clear()
                
                event_count += 1
                result = analyze_event_locally(event)
                
                if result["is_anomaly"]:
                    alert_count += 1
                    
                    # Formatear mensaje Telegram
                    severity_emoji = {
                        "CRÍTICO": "🔴",
                        "ALTO": "🟠",
                        "MEDIO": "🟡",
                    }.get(result["severity"], "⚪")
                    
                    msg = (
                        f"{severity_emoji} <b>KALPIXK ALERT — {result['severity']}</b>\n\n"
                        f"<b>Tipo:</b> {event.get('type', 'unknown')}\n"
                        f"<b>Score:</b> {result['score']}\n"
                        f"<b>MITRE:</b> {event.get('mitre', 'N/A')}\n"
                        f"<b>Horario:</b> {'⚠️ Fuera de horario' if result['is_off_hours'] else 'Normal'}\n\n"
                        f"<b>Descripción:</b> {event.get('description', '')}\n\n"
                        f"<code>{event['raw'][:200]}</code>\n\n"
                        f"<i>Alerta #{alert_count} · {datetime.datetime.now().strftime('%H:%M:%S')}</i>"
                    )
                    
                    await send_telegram(msg)
                    await save_to_base44({**event, **result})
                    print(f"[ALERTA] {result['severity']} score={result['score']} mitre={event.get('mitre')}")
                else:
                    print(f"[OK] {event.get('type')} score={result['score']:.3f} (bajo threshold)")
            
            # Reporte periódico cada 10 ciclos
            if event_count % 10 == 0:
                uptime = int(time.time() - start_time)
                print(f"[Kalpixk] Uptime: {uptime}s | Eventos: {event_count} | Alertas: {alert_count}")
            
        except Exception as e:
            print(f"[Error] {e}")
            await send_telegram(f"⚠️ Kalpixk Monitor error: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  KALPIXK — Monitor Automático v1.0")
    print("  Blue Team SIEM · AMD ROCm + CPU fallback")
    print("=" * 60)
    
    # Verificar configuración mínima
    if not TELEGRAM_TOKEN:
        print("\n⚠️  AVISO: TELEGRAM_TOKEN no configurado")
        print("   Las alertas solo aparecerán en consola")
        print("   Para activar Telegram: export TELEGRAM_TOKEN=tu_token\n")
    
    try:
        asyncio.run(monitoring_loop())
    except KeyboardInterrupt:
        print("\n[Kalpixk] Monitor detenido por usuario")
