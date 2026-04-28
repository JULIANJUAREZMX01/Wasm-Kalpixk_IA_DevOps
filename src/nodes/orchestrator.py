"""
ATLATL-ORDNANCE — GuerrillaMesh Orchestrator
Handles P2P heartbeats and threat synchronization between decentralized nodes.
Versión: 4.0-ATLATL
"""
import time
import requests
import os
import json
import hmac
import hashlib
from loguru import logger

class GuerrillaOrchestrator:
    def __init__(self, node_id: str = None):
        self.node_id = node_id or f"node-{os.uname().nodename}"
        self.peer_nodes = [p for p in os.getenv("PEER_NODES", "").split(",") if p]
        self.sync_interval = 30
        self.local_api = os.getenv("LOCAL_API", "http://localhost:8000")
        self.api_key = os.getenv("KALPIXK_API_KEY", "development_secret")
        logger.info(f"🏹 Orchestrator v4.0 initialized for {self.node_id} with {len(self.peer_nodes)} peers.")

    def sign_payload(self, payload: dict) -> str:
        """[ATLATL-ORDNANCE] Node-7 HMAC-SHA256 Signing."""
        # Use deterministic separators to match API verification
        data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(self.api_key.encode(), data, hashlib.sha256).hexdigest()

    def get_local_threats(self):
        try:
            headers = {"X-Kalpixk-Key": self.api_key}
            response = requests.get(f"{self.local_api}/api/v1/status", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json().get("threats", [])
        except Exception as e:
            logger.error(f"Failed to reach local API: {e}")
        return []

    def sync_with_peers(self):
        threats = self.get_local_threats()
        payload = {
            "node_id": self.node_id,
            "threats": threats,
            "timestamp": int(time.time()),
            "version": "4.0.0-atlatl"
        }
        signature = self.sign_payload(payload)

        headers = {
            "X-Kalpixk-Key": self.api_key,
            "X-Kalpixk-Signature": signature
        }

        for peer in self.peer_nodes:
            try:
                logger.info(f"📡 Propagating SIGNED threat signatures to mesh peer: {peer}")
                requests.post(f"{peer}/api/v1/nodes/sync", json=payload, headers=headers, timeout=10)
            except Exception as e:
                logger.error(f"Failed to sync with peer {peer}: {e}")

    def run(self):
        logger.info("🚀 GuerrillaMesh v4.0 Orchestration Loop Started.")
        while True:
            try:
                self.sync_with_peers()
            except Exception as e:
                logger.error(f"Orchestrator loop error: {e}")
            time.sleep(self.sync_interval)

if __name__ == "__main__":
    orchestrator = GuerrillaOrchestrator()
    orchestrator.run()
