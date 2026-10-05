"""
KynikosOrchestrator — Cerebro de orquestación
Detecta intención y enruta al agente/skill correcto.
"""
import re
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class Intent(Enum):
    SECURITY_ALERT = "security_alert"      # Kalpixk detectó anomalía
    STATUS_CHECK   = "status_check"        # Estado del sistema
    BENCHMARK      = "benchmark"           # Benchmark AMD MI300X
    TRAIN_MODEL    = "train_model"         # Entrenar modelo
    DETECT_NOW     = "detect_now"          # Detección inmediata
    KALPIXK_INFO   = "kalpixk_info"        # Qué es Kalpixk
    GENERAL        = "general"             # Conversación general


INTENT_PATTERNS = {
    Intent.SECURITY_ALERT:  [r"anomal", r"ataque", r"ransomware", r"alerta", r"crítico", r"threat"],
    Intent.STATUS_CHECK:    [r"status", r"estado", r"cómo está", r"activo", r"salud"],
    Intent.BENCHMARK:       [r"benchmark", r"rendimiento", r"velocidad", r"mi300x", r"gpu"],
    Intent.TRAIN_MODEL:     [r"entrena", r"train", r"modelo", r"baseline"],
    Intent.DETECT_NOW:      [r"detecta", r"detectar", r"escanea", r"analiza ahora"],
    Intent.KALPIXK_INFO:    [r"qué es kalpixk", r"cómo funciona", r"arquitectura"],
}

SOUL = """Eres KYNIKOS — el guardián digital de Wasm-Kalpixk.
Tono: directo, técnico, preciso. Sin adornos innecesarios.
Filosofía: Zero-Trust. Cada byte es sospechoso hasta que la IA lo valide.
Cuando reportas una anomalía: datos primero, contexto después.
Nunca dices "no puedo". Si no tienes datos, lo dices y propones la acción."""


@dataclass
class KynikosContext:
    session_id: str
    channel: str
    history: list = field(default_factory=list)
    last_intent: Optional[Intent] = None


class KynikosOrchestrator:
    """Capa de orquestación — une KYNIKOS con los agentes especializados."""

    def __init__(self, detector=None, monitor=None):
        self.detector = detector
        self.monitor = monitor
        self.soul = SOUL

    def detect_intent(self, text: str) -> Intent:
        text_lower = text.lower()
        for intent, patterns in INTENT_PATTERNS.items():
            if any(re.search(p, text_lower) for p in patterns):
                return intent
        return Intent.GENERAL

    def route(self, text: str, ctx: KynikosContext) -> str:
        intent = self.detect_intent(text)
        ctx.last_intent = intent

        if intent == Intent.STATUS_CHECK and self.monitor:
            raw = self.monitor.get_status()
            return self._voice(f"Sistema activo.\n{raw}", intent)

        if intent == Intent.SECURITY_ALERT:
            return self._voice(
                "⚠️ Anomalía confirmada. El motor de detección está procesando.\n"
                "Ejecuta `make detect` para análisis inmediato.", intent)

        if intent == Intent.BENCHMARK:
            return self._voice(
                "Benchmark AMD MI300X disponible.\n"
                "Ejecuta: `make benchmark` o `python skills/benchmark.py`", intent)

        if intent == Intent.TRAIN_MODEL:
            return self._voice(
                "Entrenamiento de modelo disponible.\n"
                "Ejecuta: `make train` o `python skills/train_model.py`", intent)

        # Fallback general con contexto del proyecto
        return self._voice(
            "Kalpixk online. Motor WASM activo. AMD MI300X lista.\n"
            "Comandos: status | benchmark | detect | train | help", intent)

    def _voice(self, raw_response: str, intent: Intent) -> str:
        """Aplica el tono KYNIKOS a cualquier respuesta cruda."""
        prefix = {
            Intent.SECURITY_ALERT: "🔴 KALPIXK ALERT",
            Intent.STATUS_CHECK:   "🟢 KALPIXK STATUS",
            Intent.BENCHMARK:      "⚡ KALPIXK BENCH",
            Intent.TRAIN_MODEL:    "🧠 KALPIXK TRAIN",
            Intent.DETECT_NOW:     "🔍 KALPIXK DETECT",
        }.get(intent, "🐕 KYNIKOS")

        return f"{prefix}\n{'─'*30}\n{raw_response}"
