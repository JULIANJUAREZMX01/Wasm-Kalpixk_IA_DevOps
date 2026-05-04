//! [ATLATL-ORDNANCE] GuerrillaNode v5.0
//! Standalone implementation for embedded systems.

use hmac::{Hmac, Mac};
use sha2::Sha256;
use serde_json::json;
use std::env;
use std::time::{SystemTime, UNIX_EPOCH};

type HmacSha256 = Hmac<Sha256>;

fn main() {
    env_logger::init();
    let node_id = env::var("NODE_ID").unwrap_or_else(|_| "embedded-guerrilla-01".to_string());
    let api_key = env::var("KALPIXK_API_KEY").unwrap_or_else(|_| "development_secret".to_string());

    println!("🏹 GuerrillaNode v5.0 starting on device...");
    println!("Node ID: {}", node_id);

    // Initial heartbeat
    let payload = json!({
        "node_id": node_id,
        "threats": [],
        "timestamp": SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
        "version": "5.0.0-atlatl"
    });

    let mut mac = HmacSha256::new_from_slice(api_key.as_bytes())
        .expect("HMAC can take key of any size");

    // [ATLATL-ORDNANCE] Deterministic JSON serialization for Node-7 verification
    // Matches Python separators=(",", ":") and sort_keys=True
    let payload_str = json_to_deterministic_string(&payload);
    mac.update(payload_str.as_bytes());
    let result = mac.finalize();
    let signature = hex::encode(result.into_bytes());

    println!("📡 Initialized MESH_INTEGRITY signature: {}", signature);
    println!("GuerrillaNode operational. Monitoring local bus...");
}

fn json_to_deterministic_string(value: &serde_json::Value) -> String {
    // Note: serde_json's to_string for Map sorts keys by default
    serde_json::to_string(value).unwrap()
}
