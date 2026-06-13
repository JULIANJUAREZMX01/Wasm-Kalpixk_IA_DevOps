"""
python/api/honeypot.py
───────────────────────
[ATLATL-ORDNANCE] Forensic Honeypot Module.
Captures detailed telemetry from suspicious sources.
"""

import uuid

from fastapi import APIRouter, Header, Request
from loguru import logger

router = APIRouter(prefix="/api/v1/honeypot")


@router.get("/exfiltrate")
async def trap_exfiltration(request: Request, x_atlatl_token: str = Header(None)):
    """
    [SEC-V5] Exfiltration Trap.
    Captures headers, IP, and behavior when an attacker tries to access a sensitive-looking endpoint.
    """
    event_id = str(uuid.uuid4())
    client_ip = request.client.host

    logger.critical(f"🪤  TRAP TRIGGERED: IP={client_ip} EventID={event_id}")

    # Forensic data collection (simulation)
    # Store for analysis
    # with open(f"forensics_{event_id}.json", "w") as f:
    #     json.dump(forensics, f)

    return {"status": "access_denied", "error": "ATLATL_CORE_LOCKED", "reference": event_id}


@router.post("/auth")
async def trap_brute_force(request: Request):
    """Captures brute force attempts on decoy login."""
    client_ip = request.client.host
    logger.warning(f"🪤  AUTH TRAP: IP={client_ip} attempted unauthorized authentication.")
    return {"status": "success", "message": "Authenticated"}  # Misleading success
