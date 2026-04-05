import os
import asyncio
from dotenv import load_dotenv
from src.channels.telegram_bot import KalpixkTelegramBot
from loguru import logger

# Mocking detector and monitor if they are not easily available without GPU
class MockDetector:
    def __init__(self):
        self.is_trained = True
        self.device = "CPU (Mock)"
        self.threshold = 0.5

    def predict(self, data):
        return {"reconstruction_errors": [0.01], "anomalies": [False]}

class MockMonitor:
    def capture_metrics(self):
        class Metrics:
            def __init__(self):
                self.cpu_usage = 15.0
                self.heap_usage = 45.0
            def to_array(self): return [self.cpu_usage, self.heap_usage]
        return Metrics()

async def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or token == "your_bot_token_here":
        logger.error("TELEGRAM_BOT_TOKEN no configurado en .env")
        return

    logger.info("Iniciando Kalpixk Telegram Bot...")
    bot = KalpixkTelegramBot(detector=MockDetector(), monitor=MockMonitor())

    # We use start_polling which is a blocking call in the original class
    # but let's check if we can run it.
    try:
        bot.start_polling()
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
