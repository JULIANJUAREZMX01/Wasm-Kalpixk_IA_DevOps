"""
ATLATL-ORDNANCE — Decentralized Node Orchestrator
Manages P2P threat synchronization and node health.
"""
import asyncio
import httpx
from loguru import logger
from typing import List, Set
import json
import os

class NodeOrchestrator:
    def __init__(self):
        self.nodes = set(json.loads(os.getenv("DEFENSE_NODES", '["http://localhost:8001", "http://localhost:8002"]')))
        self.global_blacklist: Set[str] = set()
        logger.info(f"Orchestrator initiated with {len(self.nodes)} nodes.")

    async def sync_threats(self, new_threats: List[str]):
        """Propagates new threat signatures to all registered nodes."""
        if not new_threats:
            return

        self.global_blacklist.update(new_threats)
        logger.info(f"Syncing {len(new_threats)} threats across {len(self.nodes)} nodes...")

        async with httpx.AsyncClient() as client:
            tasks = []
            for node in self.nodes:
                tasks.append(self._sync_to_node(client, node, new_threats))
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _sync_to_node(self, client, node_url, threats):
        try:
            resp = await client.post(
                f"{node_url}/api/v1/nodes/sync",
                json={"threats": threats},
                headers={"X-Kalpixk-Key": os.getenv("KALPIXK_API_KEY", "development")},
                timeout=2.0
            )
            if resp.status_code == 200:
                logger.debug(f"Successfully synced with node: {node_url}")
            else:
                logger.warning(f"Failed to sync with node {node_url}: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error syncing with node {node_url}: {str(e)}")

    def add_node(self, node_url: str):
        self.nodes.add(node_url)
        logger.info(f"Node added: {node_url}")

    def get_blacklist(self) -> List[str]:
        return list(self.global_blacklist)

# Global Orchestrator
orchestrator = NodeOrchestrator()
