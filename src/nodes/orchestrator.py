"""
ATLATL-ORDNANCE — GuerrillaMesh Orchestrator
Handles P2P heartbeats and threat synchronization between decentralized nodes.
Versión: 3.1-ATLATL
"""
import time
import requests
import os
import json
from loguru import logger

class GuerrillaOrchestrator:
    def __init__(self, node_id: str = None):
        self.node_id = node_id or f"node-{os.uname().nodename}"
        # Peer nodes passed as a comma-separated list of URLs
        self.peer_nodes = [p for p in os.getenv("PEER_NODES", "").split(",") if p]
        self.sync_interval = 30
        self.local_api = os.getenv("LOCAL_API", "http://localhost:8000")
        logger.info(f"🏹 Orchestrator initialized for {self.node_id} with {len(self.peer_nodes)} peers.")

    def get_local_threats(self):
        """Fetch detected threats from local API to propagate them."""
        try:
            # En v3.1, esto consultaría el registro local de Rust vía el API de Python
            response = requests.get(f"{self.local_api}/api/v1/status", timeout=5)
            if response.status_code == 200:
                return response.json().get("threats", [])
        except Exception as e:
            logger.error(f"Failed to reach local API: {e}")
        return []

    def sync_with_peers(self):
        """Broadcasts presence and local threats to peer nodes."""
        threats = self.get_local_threats()
        payload = {
            "node_id": self.node_id,
            "threats": threats,
            "timestamp": int(time.time())
        }

        for peer in self.peer_nodes:
            try:
                logger.info(f"📡 Propagating threat signatures to mesh peer: {peer}")
                # En un despliegue real, esto llamaría al endpoint /api/v1/nodes/sync del par
                # response = requests.post(f"{peer}/api/v1/nodes/sync", json=payload, timeout=10)
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Failed to sync with peer {peer}: {e}")

    def run(self):
        logger.info("🚀 GuerrillaMesh Orchestration Loop Started.")
        while True:
            try:
                self.sync_with_peers()
            except Exception as e:
                logger.error(f"Orchestrator loop error: {e}")
            time.sleep(self.sync_interval)

if __name__ == "__main__":
    orchestrator = GuerrillaOrchestrator()
    orchestrator.run()
