//! kalpixk-node — Standalone GuerrillaNode for Embedded Systems
//!
//! [ATLATL-ORDNANCE] Version 5.0-ATLATL
//! "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."

use serde::{Deserialize, Serialize};
use std::env;
use std::time::{SystemTime, UNIX_EPOCH};
use hmac::{Hmac, Mac};
use sha2::Sha256;
use uuid::Uuid;

type HmacSha256 = Hmac<Sha256>;

#[derive(Debug, Serialize, Deserialize)]
struct ThreatReport {
    node_id: String,
    threats: Vec<String>,
    timestamp: u64,
    version: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    let node_id = env::var("NODE_ID").unwrap_or_else(|_| format!("node-{}", Uuid::new_v4().to_string()[..8].to_string()));
    let api_key = env::var("KALPIXK_API_KEY").unwrap_or_else(|_| "development_secret".to_string());
    let upstream_url = env::var("UPSTREAM_URL").unwrap_or_else(|_| "http://localhost:8000/api/v1/nodes/sync".to_string());

    println!("🏹 ATLATL GuerrillaNode v5.0 Iniciando...");
    println!("📡 Node ID: {}", node_id);
    println!("🔗 Upstream: {}", upstream_url);

    loop {
        // Simulación de detección local
        let threats = vec!["LOCAL_RECON_DETECTED".to_string()];
        let timestamp = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();

        let report = ThreatReport {
            node_id: node_id.clone(),
            threats,
            timestamp,
            version: "4.0.0-atlatl".to_string(), // Compatibilidad con main.py
        };

        let _payload_json = serde_json::to_string(&report)?;

        // Deterministic JSON signing (matches src/api/main.py)
        let mut mac = HmacSha256::new_from_slice(api_key.as_bytes())?;

        // Re-serialize with sorted keys for HMAC parity
        let sorted_payload = serde_json::to_value(&report)?;
        let sorted_json = serde_json::to_string(&sorted_payload)?; // Simplified, real impl needs deep sort
        mac.update(sorted_json.as_bytes());
        let signature = hex::encode(mac.finalize().into_bytes());

        let client = reqwest::Client::new();
        let res = client.post(&upstream_url)
            .header("X-Kalpixk-Key", &api_key)
            .header("X-Kalpixk-Signature", signature)
            .json(&report)
            .send()
            .await;

        match res {
            Ok(resp) => {
                if resp.status().is_success() {
                    println!("✅ Sincronización exitosa: {}", resp.status());
                } else {
                    println!("❌ Error en sincronización: {} - {:?}", resp.status(), resp.text().await?);
                }
            }
            Err(e) => println!("⚠️ No se pudo contactar al upstream: {}", e),
        }

        tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
    }
}
