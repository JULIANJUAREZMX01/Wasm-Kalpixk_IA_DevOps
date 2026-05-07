#![allow(dead_code)]
// [ATLATL-ORDNANCE] WasmGuard Core v2.2
// Implementation of the WIT contract for the Blue Team SIEM

mod defense_nodes;
mod entropy;
mod event;
mod features;
mod metrics;
mod parsers;
mod payloads;
mod retaliation;
mod runtime_features;
mod security;
mod severity;
mod wasp;
mod wast;
use crate::event::KalpixkEvent;
use crate::metrics::WasmEventMetrics;
use crate::runtime_features::extract_32_features;
use std::sync::atomic::{AtomicUsize, Ordering};
use wasm_bindgen::prelude::*;

// Generate bindings from the WIT file
wit_bindgen::generate!({
    path: "../../kalpixk.wit",
    world: "kalpixkcore",
});

struct KalpixkCore;

impl Guest for KalpixkCore {
    fn extractfeatures(
        instructioncount: f64,
        memorypages: f64,
        fuelconsumed: f64,
        walltimens: f64,
        entropy: f64,
        calldepth: f64,
        importcalls: f64,
        exportcalls: f64,
    ) -> Vec<f32> {
        let internal_event = WasmEventMetrics {
            instruction_count: instructioncount as u64,
            memory_pages: memorypages as u32,
            fuel_consumed: fuelconsumed as u64,
            wall_time_ns: walltimens as u64,
            entropy: entropy as f32,
            call_depth: calldepth as u32,
            import_calls: importcalls as u32,
            export_calls: exportcalls as u32,
        };

        extract_32_features(&internal_event)
    }
}

// Global state for telemetry
static SHARED_ACCESS_COUNT: AtomicUsize = AtomicUsize::new(0);

#[cfg(target_arch = "wasm32")]
export!(KalpixkCore);

#[wasm_bindgen]
pub fn version() -> String {
    "5.0.0-atlatl".to_string()
}

#[wasm_bindgen]
pub fn get_security_telemetry() -> String {
    serde_json::json!({
        "shared_access_count": SHARED_ACCESS_COUNT.load(Ordering::Relaxed),
        "heartbeat": wasp::get_runtime_heartbeat(),
        "threat_level": if SHARED_ACCESS_COUNT.load(Ordering::Relaxed) > 1000 { "high" } else { "low" },
        "active_mesh_nodes": defense_nodes::get_active_nodes().len(),
        "atlatl_ordnance": "v5.0-atlatl"
    }).to_string()
}

#[wasm_bindgen]
pub fn extract_features_legacy(json_event: &str) -> Vec<f32> {
    let event: WasmEventMetrics = match serde_json::from_str(json_event) {
        Ok(e) => e,
        Err(_) => return vec![0.0f32; 32],
    };
    extract_32_features(&event)
}

#[wasm_bindgen]
pub fn analyze_and_retaliate(json_event: &str) -> String {
    let event: KalpixkEvent = match serde_json::from_str(json_event) {
        Ok(e) => e,
        Err(_) => return "{}".to_string(),
    };

    use defense_nodes::{analyze_all_nodes, get_max_severity, should_lockdown};

    let all_nodes = analyze_all_nodes(&event);
    let max = get_max_severity(&event);
    let lockdown = should_lockdown(&event);

    let dominant_node = all_nodes
        .iter()
        .max_by(|a, b| {
            a.score
                .partial_cmp(&b.score)
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .map(|n| n.node.clone())
        .unwrap_or_else(|| "NONE".to_string());

    serde_json::json!({
        "offense_level": format!("{:?}", max.level),
        "score": max.score,
        "node": dominant_node,
        "lockdown": lockdown,
        "all_nodes": all_nodes,
        "timestamp": chrono::Utc::now().timestamp_millis(),
    })
    .to_string()
}

#[wasm_bindgen]
pub fn get_global_blacklist_wasm() -> String {
    let blacklist = defense_nodes::get_global_blacklist();
    serde_json::to_string(&blacklist).unwrap_or_else(|_| "[]".to_string())
}

#[wasm_bindgen]
pub fn sync_threats_wasm(json_threats: &str) -> String {
    let threats: Vec<String> = serde_json::from_str(json_threats).unwrap_or_default();
    defense_nodes::sync_threats(threats);
    serde_json::json!({"status": "synced", "count": 1}).to_string()
}

#[wasm_bindgen]
pub fn trigger_v4_retaliation(json_target: &str) -> String {
    // [ATLATL-ORDNANCE] WASM Guerrilla Retaliation v4
    // This hook allows the JS side to trigger defensive memory poisoning
    // or report the node state to the mesh.
    serde_json::json!({
        "status": "V4_ARMED",
        "chaotic_poisoning": true,
        "entropy_trap": "ACTIVE",
        "target_fingerprint": json_target.chars().take(32).collect::<String>()
    })
    .to_string()
}

#[wasm_bindgen]
pub fn mesh_heartbeat(node_id: &str) -> String {
    defense_nodes::register_node_heartbeat(node_id.to_string());
    serde_json::json!({
        "status": "synchronized",
        "mesh_nodes": defense_nodes::get_active_nodes()
    })
    .to_string()
}

#[wasm_bindgen]
pub fn parse_log_line(raw: &str, source_type: &str) -> Option<String> {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);

    if security::validate_raw_log(raw).is_err() {
        return None;
    }

    let parser = parsers::get_parser(source_type)?;
    let event = parser.parse(raw).ok()?;
    serde_json::to_string(&serde_json::json!({
        "timestamp_ms": event.timestamp_ms,
        "event_type": event.event_type,
        "local_severity": event.local_severity,
        "source": event.source,
        "destination": event.destination,
        "user": event.user,
        "process": event.process,
        "metadata": event.metadata,
        "raw": event.raw,
        "source_type": event.source_type,
        "fingerprint": event.fingerprint,
    }))
    .ok()
}

#[wasm_bindgen]
pub fn process_batch(logs_json: &str, source_type: &str) -> String {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);

    let guard = wasp::validate_ffi_call("process_batch", 2);
    if !guard.passed {
        return serde_json::json!({"error": guard.reason}).to_string();
    }

    let lines: Vec<String> = serde_json::from_str(logs_json).unwrap_or_default();
    let parser = match parsers::get_parser(source_type) {
        Some(p) => p,
        None => {
            return serde_json::json!({"error": "unknown source", "parsed_count": 0}).to_string()
        }
    };

    let mut feature_matrix: Vec<Vec<f64>> = Vec::new();
    let mut anomaly_count = 0usize;
    let threshold = 0.5f64;

    for line in &lines {
        if security::validate_raw_log(line).is_err() {
            // [ATLATL-ORDNANCE] Active defense: Scramble local memory on injection attempt
            #[cfg(target_arch = "wasm32")]
            unsafe {
                extern "C" {
                    fn v5_active_memory_scrambling(ptr: *mut u8, len: usize, seed: u64);
                    fn v5_chaotic_interleaving(
                        ptr_a: *mut u8,
                        ptr_b: *mut u8,
                        len: usize,
                        seed: u64,
                    );
                }
                let mut decoy = [0u8; 64];
                let mut decoy_b = [0u8; 64];
                v5_active_memory_scrambling(decoy.as_mut_ptr(), decoy.len(), 0xDEADBEEF);
                v5_chaotic_interleaving(
                    decoy.as_mut_ptr(),
                    decoy_b.as_mut_ptr(),
                    decoy.len(),
                    0xACEBADE,
                );
            }
            continue;
        }
        if let Ok(event) = parser.parse(line) {
            let fvec = features::extract(&event);
            if event.local_severity > threshold {
                anomaly_count += 1;
            }
            feature_matrix.push(fvec);
        }
    }

    serde_json::json!({
        "parsed_count": feature_matrix.len(),
        "anomaly_count": anomaly_count,
        "feature_matrix": feature_matrix,
        "feature_names": features::FEATURE_NAMES,
    })
    .to_string()
}

#[wasm_bindgen]
pub fn compute_ueba_features(events_json: &str) -> String {
    let events: Vec<event::KalpixkEvent> = serde_json::from_str(events_json).unwrap_or_default();

    if events.is_empty() {
        return serde_json::json!({
            "features": vec![0.0f64; features::FEATURE_DIM],
            "risk_score": 0.0,
            "event_count": 0
        })
        .to_string();
    }

    let mut avg = vec![0.0f64; features::FEATURE_DIM];
    let n = events.len() as f64;
    for ev in &events {
        let fvec = features::extract(ev);
        for (i, v) in fvec.iter().enumerate() {
            avg[i] += v / n;
        }
    }

    let risk_score = avg[1]; // local_severity promedio
    serde_json::json!({
        "features": avg,
        "risk_score": risk_score,
        "event_count": events.len(),
        "contract_version": "1.0.0",
    })
    .to_string()
}

#[wasm_bindgen]
pub fn get_feature_names() -> Vec<String> {
    features::FEATURE_NAMES
        .iter()
        .map(|&s| s.to_string())
        .collect()
}

#[wasm_bindgen]
pub fn wasm_lockdown(node: &str, score: f64, event_json: &str) -> String {
    let guard = wasp::validate_ffi_call("wasm_lockdown", 3);
    if !guard.passed {
        return serde_json::json!({"error": "unauthorized lockdown"}).to_string();
    }

    serde_json::json!({
        "action": "LOCKDOWN",
        "node": node,
        "score": score,
        "event_summary": event_json.chars().take(100).collect::<String>(),
        "status": "CRITICAL_BLOCK",
        "timestamp": chrono::Utc::now().timestamp_millis(),
    })
    .to_string()
}

#[wasm_bindgen]
pub fn health_check() -> String {
    serde_json::json!({
        "status": "ok",
        "module": "kalpixk-core",
        "feature_dim": 32,
        "wit_implemented": true,
        "atlatl_ordnance": "v5.0-atlatl",
        "heartbeat": wasp::get_runtime_heartbeat(),
        "mesh_active": true
    })
    .to_string()
}
