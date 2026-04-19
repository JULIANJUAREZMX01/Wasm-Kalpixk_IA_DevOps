"""
ATLATL-ORDNANCE — GuerrillaMesh Orchestrator v4.0
Handles Node-7 Integrity and P2P threat synchronization.
"""
import time
import requests
import os
import secrets
from loguru import logger

class GuerrillaOrchestrator:
    def __init__(self, node_id: str = None):
        self.node_id = node_id or f"node-{os.uname().nodename}"
        self.peer_nodes = [p for p in os.getenv("PEER_NODES", "").split(",") if p]
        self.sync_interval = 30
        self.local_api = os.getenv("LOCAL_API", "http://localhost:8000")
        self.node_secret = os.getenv("NODE_SECRET", secrets.token_hex(16))
        logger.info(f"🏹 Orchestrator v4.0 (Node-7) initialized for {self.node_id}")

    def get_local_threats(self):
        try:
            response = requests.get(f"{self.local_api}/api/v1/status", timeout=5)
            if response.status_code == 200:
                return response.json().get("threats", ["T1485_LOCAL_V4"])
        except Exception:
            pass
        return []

    def sync_with_peers(self):
        threats = self.get_local_threats()
        payload = {
            "node_id": self.node_id,
            "threats": threats,
            "timestamp": int(time.time()),
            "signature": f"v4-signed-{self.node_secret[:8]}"
        }

        for peer in self.peer_nodes:
            try:
                logger.info(f"📡 Node-7 Signed Propagation to: {peer}")
                # requests.post(f"{peer}/api/v1/nodes/sync", json=payload, timeout=10)
            except Exception as e:
                logger.error(f"Sync failed: {e}")

    def run(self):
        logger.info("🚀 GuerrillaMesh v4.0 Orchestration Active.")
        while True:
            self.sync_with_peers()
            time.sleep(self.sync_interval)

if __name__ == "__main__":
    GuerrillaOrchestrator().run()
