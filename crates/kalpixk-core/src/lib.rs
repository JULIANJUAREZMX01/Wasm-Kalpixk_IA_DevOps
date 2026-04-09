// [ATLATL-ORDNANCE] WasmGuard Core v2.1
// Implementation of the WIT contract for the Blue Team SIEM

mod metrics;
mod entropy;
mod runtime_features;
mod defense_nodes;
mod event;
mod features;
mod parsers;
mod payloads;
mod security;
mod retaliation;
mod wasp;
mod wast;
mod severity;

use wasm_bindgen::prelude::*;
use crate::runtime_features::extract_32_features;
use crate::metrics::WasmEventMetrics;

// Generate bindings from the WIT file
// Note: In a real environment, this macro looks for kalpixk.wit in the root or parent
wit_bindgen::generate!({
    path: "../../../kalpixk.wit",
    world: "kalpixk-core",
});

struct KalpixkCore;

impl exports::kalpixk_monitor::Guest for KalpixkCore {
    fn extract_features(event: exports::kalpixk_monitor::WasmEvent) -> Vec<f32> {
        // Map WIT record to internal record
        let internal_event = WasmEventMetrics {
            instruction_count: event.instruction_count,
            memory_pages: event.memory_pages,
            fuel_consumed: event.fuel_consumed,
            wall_time_ns: event.wall_time_ns,
            entropy: event.entropy,
            call_depth: event.call_depth,
            import_calls: event.import_calls,
            export_calls: event.export_calls,
        };

        extract_32_features(&internal_event)
    }
}

export!(KalpixkCore);

// Keep wasm-bindgen exports for backward compatibility with the current frontend
#[wasm_bindgen]
pub fn extract_features_legacy(json_event: &str) -> Vec<f32> {
    let event: WasmEventMetrics = match serde_json::from_str(json_event) {
        Ok(e) => e,
        Err(_) => return vec![0.0f32; 32],
    };
    extract_32_features(&event)
}

#[wasm_bindgen]
pub fn health_check() -> String {
    serde_json::json!({
        "status": "ok",
        "module": "kalpixk-core",
        "feature_dim": 32,
        "wit_implemented": true,
        "atlatl_ordnance": "v2.1"
    })
    .to_string()
}
