#!/usr/bin/env python3
"""
Skill: kalpixk_status
Reporte completo del estado del sistema Kalpixk
Uso: python skills/kalpixk_status.py [--json]
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run():
    import torch, psutil
    from src.ui import KalpixkTheme, ANSI

    data = {}

    # GPU
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        vram_used = torch.cuda.memory_allocated(0) / 1e9
        vram_total = props.total_memory / 1e9
        data["gpu"] = {
            "name": props.name, "vram_total_gb": round(vram_total,1),
            "vram_used_gb": round(vram_used,2),
            "vram_pct": round(vram_used/vram_total*100, 1),
            "status": "ok"
        }
    else:
        data["gpu"] = {"status": "cpu_mode", "name": "N/A"}

    # CPU / RAM / Disk
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    data["system"] = {
        "cpu_pct": psutil.cpu_percent(interval=1),
        "ram_used_gb": round(mem.used/1e9, 2),
        "ram_total_gb": round(mem.total/1e9, 1),
        "ram_pct": mem.percent,
        "disk_free_gb": round(disk.free/1e9, 1),
        "disk_pct": disk.percent,
    }

    # Modelo
    model_path = "models/kalpixk_v2.pt"
    data["model"] = {
        "exists": os.path.exists(model_path),
        "path": model_path,
        "size_kb": round(os.path.getsize(model_path)/1024, 1) if os.path.exists(model_path) else 0,
    }

    # Env vars configuradas
    data["config"] = {
        "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "twilio": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "amd_vllm": bool(os.getenv("AMD_VLLM_URL")),
        "env": os.getenv("ENV", "development"),
    }

    if "--json" in sys.argv:
        print(json.dumps(data, indent=2))
        return

    # Pretty print estilo SACITY
    KalpixkTheme.print_banner()
    g = data["gpu"]
    s = data["system"]
    m = data["model"]
    c = data["config"]

    gpu_line = f"{g['name']} | {g.get('vram_total_gb','N/A')} GB" if g["status"]=="ok" else "CPU mode"
    print(KalpixkTheme.status_line("GPU", gpu_line, "ok" if g["status"]=="ok" else "warn"))
    print(KalpixkTheme.status_line("CPU", f"{s['cpu_pct']}%", "ok" if s["cpu_pct"]<80 else "warn"))
    print(KalpixkTheme.status_line("RAM", f"{s['ram_used_gb']}/{s['ram_total_gb']} GB ({s['ram_pct']}%)",
          "ok" if s["ram_pct"]<85 else "warn"))
    print(KalpixkTheme.status_line("Disk free", f"{s['disk_free_gb']} GB", "ok"))
    print(KalpixkTheme.status_line("Model", "✅ loaded" if m["exists"] else "❌ not found",
          "ok" if m["exists"] else "error"))
    print(KalpixkTheme.status_line("Telegram", "✅" if c["telegram"] else "❌ not configured",
          "ok" if c["telegram"] else "warn"))
    print(KalpixkTheme.status_line("WhatsApp", "✅" if c["twilio"] else "❌ not configured",
          "ok" if c["twilio"] else "warn"))
    print(KalpixkTheme.status_line("Groq LLM", "✅" if c["groq"] else "❌ not configured",
          "ok" if c["groq"] else "warn"))
    print(KalpixkTheme.status_line("AMD vLLM", "✅ ACTIVE" if c["amd_vllm"] else "⚫ pending",
          "ok" if c["amd_vllm"] else "info"))

if __name__ == "__main__":
    run()
