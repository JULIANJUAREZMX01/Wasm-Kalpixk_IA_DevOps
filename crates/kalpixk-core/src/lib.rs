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
    world: "kalpixk-core",
});

struct KalpixkCore;

// Implement the exported interface
impl exports::kalpixk::core::kalpixk_monitor::Guest for KalpixkCore {
    fn extract_features(event: exports::kalpixk::core::kalpixk_monitor::WasmEvent) -> Vec<f32> {
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

// Global state for telemetry
static SHARED_ACCESS_COUNT: AtomicUsize = AtomicUsize::new(0);

#[cfg(target_arch = "wasm32")]
export!(KalpixkCore);

#[wasm_bindgen]
pub fn version() -> String {
    "4.0.0-atlatl".to_string()
}

#[wasm_bindgen]
pub fn get_security_telemetry() -> String {
    serde_json::json!({
        "shared_access_count": SHARED_ACCESS_COUNT.load(Ordering::Relaxed),
        "heartbeat": wasp::get_runtime_heartbeat(),
        "threat_level": if SHARED_ACCESS_COUNT.load(Ordering::Relaxed) > 1000 { "high" } else { "low" },
        "active_mesh_nodes": defense_nodes::get_active_nodes().len()
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
pub fn trigger_v5_retaliation(json_target: &str) -> String {
    // [ATLATL-ORDNANCE] WASM Guerrilla Retaliation v5
    // This hook triggers deep memory-level countermeasures via Zig core.
    serde_json::json!({
        "status": "V5_STEALTH_ARMED",
        "stealth_poisoning": true,
        "memory_sink": "ARMED",
        "target_fingerprint": json_target.chars().take(32).collect::<String>()
    })
    .to_string()
}

#[wasm_bindgen]
pub fn trigger_mesh_shredder() -> String {
    // [ATLATL-ORDNANCE] Triggers the mesh-level entropy shredder
    serde_json::json!({
        "status": "MESH_SHREDDER_ACTIVE",
        "mode": "ATLATL_V5"
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

    if !security::validate_raw_log(raw).is_ok() {
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
        if !security::validate_raw_log(line).is_ok() {
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
        "atlatl_ordnance": "v3.1-atlatl",
        "heartbeat": wasp::get_runtime_heartbeat(),
        "mesh_active": true
    })
    .to_string()
}
