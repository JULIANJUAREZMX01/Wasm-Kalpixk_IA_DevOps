"""
Utilidades de dispositivo — detección automática de AMD ROCm
"""

import logging
import torch

logger = logging.getLogger("kalpixk.utils.device")


def get_rocm_device() -> torch.device:
    """
    Detectar automáticamente el mejor dispositivo disponible.
    
    Prioridad: AMD ROCm GPU → CUDA GPU → CPU
    """
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        logger.info(f"GPU detectada: {device_name}")
        
        if "Instinct" in device_name or "Radeon" in device_name or "AMD" in device_name:
            logger.info("AMD GPU detectada — usando ROCm")
        else:
            logger.info("NVIDIA GPU detectada — usando CUDA")
        
        return torch.device("cuda:0")
    
    logger.warning("No se detectó GPU — usando CPU. Rendimiento reducido.")
    return torch.device("cpu")


def log_gpu_info(device: torch.device) -> None:
    """Loguear información del dispositivo GPU"""
    if device.type == "cpu":
        logger.info("Dispositivo: CPU")
        return
    
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        total_memory_gb = props.total_memory / (1024 ** 3)
        
        logger.info(f"=== GPU Info ===")
        logger.info(f"Nombre: {props.name}")
        logger.info(f"VRAM: {total_memory_gb:.1f} GB")
        logger.info(f"Multi-processors: {props.multi_processor_count}")
        logger.info(f"ROCm/CUDA version: {torch.version.cuda}")
        logger.info(f"================")


def get_memory_info() -> dict:
    """Obtener información de memoria GPU en tiempo real"""
    if not torch.cuda.is_available():
        return {"device": "cpu", "available": True}
    
    allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
    reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
    props = torch.cuda.get_device_properties(0)
    total = props.total_memory / (1024 ** 3)
    
    return {
        "device": torch.cuda.get_device_name(0),
        "total_gb": round(total, 2),
        "allocated_gb": round(allocated, 2),
        "reserved_gb": round(reserved, 2),
        "free_gb": round(total - reserved, 2),
        "utilization_pct": round((reserved / total) * 100, 1),
    }
