"""
Kalpixk WhatsApp Notifications — via Twilio
Portado de SAC/notificaciones_whatsapp.py
Configurable via .env o API endpoint
"""
import os
from datetime import datetime
from loguru import logger

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_OK = True
except ImportError:
    TWILIO_OK = False
    logger.warning("twilio no instalado — pip install twilio")


class KalpixkWhatsApp:
    """
    Notificaciones WhatsApp para el motor Kalpixk via Twilio.
    
    Config en .env:
        TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        TWILIO_AUTH_TOKEN=your_auth_token
        TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
        WHATSAPP_TO=whatsapp:+521234567890
    """

    def __init__(self):
        self.sid   = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_ = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        self.to    = os.getenv("WHATSAPP_TO", "")
        self.enabled = TWILIO_OK and bool(self.sid) and bool(self.token)
        if self.enabled:
            self.client = TwilioClient(self.sid, self.token)
            logger.info("✅ WhatsApp/Twilio configurado")
        else:
            logger.warning("WhatsApp/Twilio no disponible")

    def send(self, body: str, to: str = None) -> bool:
        """Envía mensaje WhatsApp."""
        if not self.enabled:
            logger.warning(f"[WhatsApp SIMULADO] {body[:80]}")
            return False
        try:
            msg = self.client.messages.create(
                body=body,
                from_=self.from_,
                to=to or self.to
            )
            logger.info(f"WhatsApp enviado: {msg.sid}")
            return True
        except Exception as e:
            logger.error(f"WhatsApp error: {e}")
            return False

    def send_anomaly_alert(self, score: float, details: dict = None) -> bool:
        body = (
            f"🚨 KALPIXK ANOMALÍA DETECTADA\n"
            f"Score: {score:.4f}\n"
            f"Hora: {datetime.now().strftime('%H:%M:%S')}\n"
        )
        if details:
            body += "\n".join([f"• {k}: {v}" for k, v in list(details.items())[:4]])
        return self.send(body)

    def send_status(self, status: dict) -> bool:
        gpu = "AMD MI300X ✅" if status.get("gpu_ok") else "CPU ⚠️"
        body = (
            f"📊 KALPIXK STATUS\n"
            f"GPU: {gpu}\n"
            f"Modelo: {'Entrenado ✅' if status.get('trained') else 'Sin entrenar ❌'}\n"
            f"Threshold: {status.get('threshold', 0.5)}\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        return self.send(body)

    def send_benchmark(self, throughput: float, elapsed_ms: float) -> bool:
        body = (
            f"⚡ BENCHMARK MI300X\n"
            f"Throughput: {throughput:,.0f} samples/sec\n"
            f"Tiempo: {elapsed_ms:.2f} ms\n"
            f"Kalpixk motor OK"
        )
        return self.send(body)
