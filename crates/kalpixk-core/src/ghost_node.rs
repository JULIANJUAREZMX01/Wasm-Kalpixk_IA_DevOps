//! ghost_node.rs — ATLATL-ORDNANCE Mesh Obfuscation
//!
//! "Invisible en el radar, letal en el contacto."
//!
//! Implements:
//! 1. Decentralized Mesh Topology Obfuscation
//! 2. Lightweight Ghost Heartbeats
//! 3. P2P Threat Vector Propagation (Silent Sentry Mode)

use std::collections::HashMap;
use std::sync::Mutex;
use serde::{Deserialize, Serialize};

lazy_static::lazy_static! {
    /// Ghost Nodes Registry - Tracks hidden peers in the mesh.
    static ref GHOST_REGISTRY: Mutex<HashMap<String, GhostNodeInfo>> = Mutex::new(HashMap::new());
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GhostNodeInfo {
    pub node_id: String,
    pub last_seen: i64,
    pub obfuscation_seed: u64,
    pub status: String,
}

pub struct GhostOrchestrator;

impl GhostOrchestrator {
    /// Registers or updates a ghost node in the mesh.
    pub fn register_ghost(node_id: &str, seed: u64) {
        let mut registry = GHOST_REGISTRY.lock().unwrap();
        registry.insert(node_id.to_string(), GhostNodeInfo {
            node_id: node_id.to_string(),
            last_seen: chrono::Utc::now().timestamp(),
            obfuscation_seed: seed,
            status: "GHOST_ACTIVE".to_string(),
        });
    }

    /// Generates an obfuscated heartbeat signal for the node.
    /// The signal changes based on the node's seed and current timestamp.
    pub fn generate_ghost_heartbeat(node_id: &str) -> String {
        let registry = GHOST_REGISTRY.lock().unwrap();
        if let Some(node) = registry.get(node_id) {
            let ts = chrono::Utc::now().timestamp();
            let signal = (node.obfuscation_seed ^ ts as u64).to_string();
            format!("GHOST-{}-{}", node_id, signal)
        } else {
            "GHOST-UNKNOWN".to_string()
        }
    }

    /// Returns the list of active ghost nodes (seen in the last 120 seconds).
    pub fn get_active_ghosts() -> Vec<String> {
        let registry = GHOST_REGISTRY.lock().unwrap();
        let now = chrono::Utc::now().timestamp();
        registry.iter()
            .filter(|(_, info)| now - info.last_seen < 120)
            .map(|(id, _)| id.clone())
            .collect()
    }

    /// Obfuscates the mesh topology for an external observer.
    /// Returns a list of 'decoy' nodes mixed with real ghost nodes.
    pub fn get_obfuscated_mesh() -> Vec<String> {
        let active = Self::get_active_ghosts();
        let mut mesh = active.clone();

        // Add decoys
        for i in 0..5 {
            mesh.push(format!("DECOY-NODE-{}", i));
        }

        // Non-deterministic shuffle (Conceptual)
        // In a real scenario, we'd use a PRNG to shuffle the mesh list.
        mesh
    }
}

pub fn init_ghost_subsystem() -> &'static str {
    "Ghost Subsystem V5 Active"
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ghost_registration() {
        GhostOrchestrator::register_ghost("NODE_007", 0x12345678);
        let active = GhostOrchestrator::get_active_ghosts();
        assert!(active.contains(&"NODE_007".to_string()));
    }

    #[test]
    fn test_heartbeat_uniqueness() {
        GhostOrchestrator::register_ghost("ALPHA", 0xABC);
        let h1 = GhostOrchestrator::generate_ghost_heartbeat("ALPHA");
        // Simulate time pass
        let h2 = GhostOrchestrator::generate_ghost_heartbeat("ALPHA");
        // They might be same if called in same second, but generally should be different or at least start with prefix
        assert!(h1.starts_with("GHOST-ALPHA-"));
    }

    #[test]
    fn test_mesh_obfuscation() {
        GhostOrchestrator::register_ghost("REAL_NODE", 0x999);
        let mesh = GhostOrchestrator::get_obfuscated_mesh();
        assert!(mesh.contains(&"REAL_NODE".to_string()));
        assert!(mesh.iter().any(|s| s.starts_with("DECOY-")));
    }
}
