"""
Kalpixk System Monitor
Portado y simplificado de SAC/monitor.py + SAC/health_check.py
Monitoreo continuo del motor + GPU + notificaciones automáticas
"""
import time
import psutil
import threading
from datetime import datetime
from loguru import logger
from typing import Optional, Callable


class KalpixkSystemMonitor:
    """
    Monitor continuo del sistema Kalpixk.
    - Monitorea GPU, CPU, RAM en background
    - Dispara callbacks cuando detecta anomalías
    - Integra con Telegram y WhatsApp para alertas
    """

    def __init__(self, detector=None, telegram_bot=None, whatsapp=None,
                 check_interval: float = 30.0):
        self.detector = detector
        self.telegram = telegram_bot
        self.whatsapp = whatsapp
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats = {
            "checks_total": 0,
            "anomalies_found": 0,
            "last_check": None,
            "uptime_start": datetime.now(),
        }
        logger.info(f"SystemMonitor iniciado (interval: {check_interval}s)")

    def get_gpu_stats(self) -> dict:
        """Estadísticas de GPU AMD via pytorch."""
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                mem_used = torch.cuda.memory_allocated(0)
                mem_total = props.total_memory
                return {
                    "available": True,
                    "name": props.name,
                    "vram_total_gb": round(mem_total / 1e9, 1),
                    "vram_used_gb": round(mem_used / 1e9, 2),
                    "vram_pct": round(mem_used / mem_total * 100, 1),
                }
        except Exception:
            pass
        return {"available": False}

    def get_system_stats(self) -> dict:
        """CPU, RAM, disco."""
        mem = psutil.virtual_memory()
        return {
            "cpu_pct": psutil.cpu_percent(interval=1),
            "ram_used_gb": round(mem.used / 1e9, 2),
            "ram_total_gb": round(mem.total / 1e9, 1),
            "ram_pct": mem.percent,
            "timestamp": datetime.now().isoformat(),
        }

    def health_check(self) -> dict:
        """Health check completo del sistema."""
        sys_stats = self.get_system_stats()
        gpu_stats = self.get_gpu_stats()
        checks = {
            "system": sys_stats,
            "gpu": gpu_stats,
            "detector_trained": self.detector.is_trained if self.detector else False,
            "status": "ok",
        }
        # Verificar umbrales
        if sys_stats["ram_pct"] > 90:
            checks["status"] = "warn"
            checks["warning"] = "RAM > 90%"
        if gpu_stats.get("vram_pct", 0) > 85:
            checks["status"] = "warn"
            checks["warning"] = "VRAM > 85%"
        return checks

    def _monitor_loop(self):
        """Loop de monitoreo en background."""
        logger.info("🔄 Monitor loop iniciado")
        while self._running:
            try:
                self.stats["checks_total"] += 1
                self.stats["last_check"] = datetime.now().isoformat()
                
                # Health check
                health = self.health_check()
                
                # Si detector está entrenado, correr detección
                if self.detector and self.detector.is_trained:
                    from src.runtime import WasmRuntimeMonitor
                    mon = WasmRuntimeMonitor()
                    metrics = mon.capture_metrics()
                    result = self.detector.predict(metrics.to_array())
                    
                    if any(result["anomalies"]):
                        score = result["reconstruction_errors"][0]
                        self.stats["anomalies_found"] += 1
                        logger.warning(f"🚨 ANOMALÍA detectada! Score: {score:.4f}")
                        if self.telegram:
                            self.telegram.send_anomaly_alert(score, "monitor_loop", metrics.__dict__)
                        if self.whatsapp:
                            self.whatsapp.send_anomaly_alert(score, metrics.__dict__)

                if health["status"] != "ok":
                    logger.warning(f"Health warn: {health.get('warning')}")

            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
            
            time.sleep(self.check_interval)

    def start(self):
        """Inicia el monitor en background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("✅ SystemMonitor arrancado en background")

    def stop(self):
        """Detiene el monitor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("SystemMonitor detenido")

    def get_uptime(self) -> str:
        delta = datetime.now() - self.stats["uptime_start"]
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
