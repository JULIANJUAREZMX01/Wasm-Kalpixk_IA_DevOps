from telegram import Update
"""
Kalpixk Telegram Bot
Portado y adaptado de SAC/notificaciones_telegram.py + KynicOS
Controla el motor de detección desde móvil via @SuperAsistenteSacBot
"""
import os
import asyncio
from datetime import datetime
from typing import Optional
from loguru import logger

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler,
        ContextTypes, MessageHandler, filters
    )
    TELEGRAM_OK = True
except ImportError:
    TELEGRAM_OK = False
    logger.warning("python-telegram-bot no instalado")


class KalpixkTelegramBot:
    """
    Bot de Telegram para control remoto del motor Kalpixk.
    Comandos disponibles:
        /start      — bienvenida y menu
        /status     — estado GPU + detector
        /detect     — correr detección ahora
        /benchmark  — benchmark rápido MI300X
        /train      — re-entrenar modelo
        /threshold  — ajustar umbral de anomalía
        /help       — ayuda
    """

    def __init__(self, detector=None, monitor=None):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.detector = detector
        self.monitor = monitor
        self.app: Optional[object] = None
        self._running = False

    # ── Envío de mensajes (compatible con SAC) ──────────────────

    def send_message(self, text: str, chat_id: str = None) -> bool:
        """Envía mensaje vía HTTP (sin async — compatible con threads)."""
        import requests
        cid = chat_id or self.chat_id
        if not self.token or not cid:
            logger.warning("Telegram no configurado (TOKEN o CHAT_ID faltante)")
            return False
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            r = requests.post(url, json={"chat_id": cid, "text": text, "parse_mode": "Markdown"}, timeout=5)
            return r.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False

    def send_anomaly_alert(self, score: float, anomaly_type: str = "WASM", details: dict = None):
        """Alerta de anomalía detectada — notificación urgente."""
        msg = f"""🚨 *ANOMALÍA DETECTADA — KALPIXK*
━━━━━━━━━━━━━━━━━━━━
🔴 Score: `{score:.4f}`
📍 Tipo: `{anomaly_type}`
🕐 Hora: `{datetime.now().strftime("%H:%M:%S")}`
"""
        if details:
            for k, v in details.items():
                msg += f"• {k}: `{v}`\n"
        msg += "━━━━━━━━━━━━━━━━━━━━"
        return self.send_message(msg)

    def send_status_report(self, status: dict):
        """Reporte de estado del sistema."""
        gpu = "✅ AMD MI300X" if status.get("gpu_ok") else "⚠️ CPU mode"
        trained = "✅ Entrenado" if status.get("trained") else "❌ Sin entrenar"
        msg = f"""📊 *KALPIXK STATUS REPORT*
━━━━━━━━━━━━━━━━━━━━
🖥️ GPU: {gpu}
🧠 Modelo: {trained}
⚡ Device: `{status.get("device", "N/A")}`
🎯 Threshold: `{status.get("threshold", 0.5)}`
🔄 Uptime: `{status.get("uptime", "N/A")}`
━━━━━━━━━━━━━━━━━━━━"""
        return self.send_message(msg)

    def send_benchmark_result(self, throughput: float, device: str, elapsed_ms: float):
        """Resultado de benchmark GPU."""
        msg = f"""⚡ *BENCHMARK AMD MI300X*
━━━━━━━━━━━━━━━━━━━━
🚀 Throughput: `{throughput:,.0f} samples/sec`
⏱️ Tiempo: `{elapsed_ms:.2f} ms`
🖥️ Device: `{device}`
━━━━━━━━━━━━━━━━━━━━
_Kalpixk motor OK_"""
        return self.send_message(msg)

    # ── Handlers async (para polling) ──────────────────────────

    def _is_authorized(self, update: Update) -> bool:
        """Verifica si el remitente es el administrador configurado."""
        if not self.chat_id:
            # Si no hay chat_id configurado, no permitimos nada por seguridad
            logger.warning("TELEGRAM_CHAT_ID no configurado. Acceso denegado.")
            return False

        current_chat_id = str(update.effective_chat.id)
        if current_chat_id != str(self.chat_id):
            logger.warning(f"Intento de acceso no autorizado desde chat_id: {current_chat_id}")
            return False
        return True

    async def cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            await update.message.reply_text("⛔ *Acceso denegado*", parse_mode="Markdown")
            return

        keyboard = [
            [InlineKeyboardButton("📊 Status", callback_data="status"),
             InlineKeyboardButton("🔍 Detectar", callback_data="detect")],
            [InlineKeyboardButton("⚡ Benchmark", callback_data="benchmark"),
             InlineKeyboardButton("🎯 Threshold", callback_data="threshold")],
            [InlineKeyboardButton("🔄 Re-entrenar", callback_data="train"),
             InlineKeyboardButton("❓ Help", callback_data="help")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔬 *Kalpixk Control Center*\n"
            "Motor de detección de anomalías WASM\n"
            "AMD MI300X | 205.8 GB VRAM",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def cmd_status(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            if update.callback_query:
                await update.callback_query.answer("Acceso denegado", show_alert=True)
            return

        import torch
        gpu_ok = torch.cuda.is_available()
        status = {
            "gpu_ok": gpu_ok,
            "trained": self.detector.is_trained if self.detector else False,
            "device": str(self.detector.device) if self.detector else "N/A",
            "threshold": self.detector.threshold if self.detector else 0.5,
            "uptime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.send_status_report(status)
        if update.callback_query:
            await update.callback_query.answer("Status enviado")

    async def cmd_detect(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            if update.callback_query:
                await update.callback_query.answer("Acceso denegado", show_alert=True)
            return

        if not self.detector or not self.monitor:
            await update.effective_message.reply_text("❌ Motor no inicializado")
            return
        metrics = self.monitor.capture_metrics()
        result = self.detector.predict(metrics.to_array())
        score = result["reconstruction_errors"][0]
        is_anomaly = result["anomalies"][0]
        if is_anomaly:
            self.send_anomaly_alert(score, "runtime_check", metrics.__dict__)
        else:
            await update.effective_message.reply_text(
                f"✅ *Sistema normal*\nScore: `{score:.4f}` (bajo umbral {self.detector.threshold})",
                parse_mode="Markdown"
            )

    async def button_handler(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            await update.callback_query.answer("Acceso denegado", show_alert=True)
            return

        query = update.callback_query
        await query.answer()
        if query.data == "status":
            await self.cmd_status(update, ctx)
        elif query.data == "detect":
            await self.cmd_detect(update, ctx)
        elif query.data == "benchmark":
            await query.edit_message_text("⚡ Corriendo benchmark... espera.")
        elif query.data == "help":
            await query.edit_message_text(
                "*Comandos Kalpixk:*\n"
                "/status — GPU + estado modelo\n"
                "/detect — detección ahora\n"
                "/benchmark — throughput MI300X\n"
                "/train — re-entrenar modelo\n"
                "/threshold X — cambiar umbral",
                parse_mode="Markdown"
            )

    def start_polling(self):
        """Inicia el bot en modo polling (para servidor siempre activo)."""
        if not TELEGRAM_OK:
            logger.error("python-telegram-bot no disponible")
            return
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN no configurado")
            return

        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("detect", self.cmd_detect))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        logger.info("🤖 Kalpixk Bot iniciado en polling mode")
        self.app.run_polling()
