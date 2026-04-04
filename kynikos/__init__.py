"""
KYNIKOS — Capa de Orquestación para Wasm-Kalpixk_IA_DevOps

KYNIKOS no ES un agente. Es la capa que:
  1. Recibe mensajes de cualquier canal (Telegram, WhatsApp, API)
  2. Entiende la intención del operador
  3. Enruta al agente especializado correcto (Kalpixk, HVAC, Concierge)
  4. Devuelve la respuesta con su voz y tono únicos

Arquitectura:
  Canal → KYNIKOS (soul+tono) → Agente especializado → Respuesta filtrada por KYNIKOS
"""

from .orchestrator import KynikosOrchestrator

__all__ = ["KynikosOrchestrator"]
