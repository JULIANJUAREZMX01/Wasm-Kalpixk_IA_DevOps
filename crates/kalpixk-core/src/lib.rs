pub mod metrics;
pub mod entropy;
pub mod runtime_features;

// Keep existing modules if they exist and are useful
pub mod defense_nodes;
pub mod event;
pub mod features;
pub mod parsers;
pub mod payloads;
pub mod wasp;
pub mod wast;

use wasm_bindgen::prelude::*;
use crate::metrics::WasmEventMetrics;

#[wasm_bindgen]
pub fn extract_features(json_event: &str) -> Vec<f32> {
    let event: WasmEventMetrics = match serde_json::from_str(json_event) {
        Ok(e) => e,
        Err(_) => return vec![0.0f32; 32],
    };
    runtime_features::extract_32_features(&event)
}

#[wasm_bindgen]
pub fn health_check() -> String {
    serde_json::json!({
        "status": "ok",
        "module": "kalpixk-core",
        "feature_dim": 32,
        "wasp": true,
    })
    .to_string()
}
