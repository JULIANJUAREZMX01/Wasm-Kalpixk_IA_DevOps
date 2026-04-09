pub mod metrics;
pub mod entropy;
pub mod runtime_features;
pub mod defense_nodes;
pub mod event;
pub mod features;
pub mod parsers;
pub mod payloads;
pub mod wasp;
pub mod wast;

use wasm_bindgen::prelude::*;
use crate::metrics::WasmEventMetrics;
use std::sync::atomic::{AtomicU64, Ordering};

pub const FEATURE_CONTRACT_VERSION: &str = "1.0.0";
static SHARED_ACCESS_COUNT: AtomicU64 = AtomicU64::new(0);

#[wasm_bindgen]
pub fn extract_features(json_event: &str) -> Vec<f32> {
    let event: WasmEventMetrics = match serde_json::from_str(json_event) {
        Ok(e) => e,
        Err(_) => return vec![0.0f32; 32],
    };
    runtime_features::extract_32_features(&event)
}

#[wasm_bindgen]
pub fn version() -> String {
    format!(
        "kalpixk-core/{} (contract {})",
        env!("CARGO_PKG_VERSION"),
        FEATURE_CONTRACT_VERSION
    )
}

#[wasm_bindgen]
pub fn wasm_lockdown(node: &str, score: f64, event_json: &str) -> String {
    serde_json::json!({
        "action": "LOCKDOWN",
        "node": node,
        "score": score,
        "event_summary": event_json.chars().take(100).collect::<String>(),
        "status": "CRITICAL_BLOCK",
        "timestamp": chrono::Utc::now().timestamp_millis(),
    }).to_string()
}

#[wasm_bindgen]
pub fn analyze_and_retaliate(event_json: &str) -> String {
    let event: event::KalpixkEvent = match serde_json::from_str(event_json) {
        Ok(e) => e,
        Err(e) => return serde_json::json!({"error": e.to_string()}).to_string(),
    };
    use defense_nodes::{analyze_all_nodes, get_max_severity, should_lockdown};
    let all_nodes = analyze_all_nodes(&event);
    let max = get_max_severity(&event);
    let lockdown = should_lockdown(&event);
    let dominant_node = all_nodes
        .iter()
        .max_by(|a, b| a.score.partial_cmp(&b.score).unwrap_or(std::cmp::Ordering::Equal))
        .map(|n| n.node.clone())
        .unwrap_or_else(|| "NONE".to_string());

    serde_json::json!({
        "offense_level": format!("{:?}", max.level),
        "score": max.score,
        "node": dominant_node,
        "lockdown": lockdown,
        "all_nodes": all_nodes,
        "timestamp": chrono::Utc::now().timestamp_millis(),
    }).to_string()
}

#[wasm_bindgen]
pub fn parse_log_line(raw: &str, source_type: &str) -> Option<String> {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);
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
    })).ok()
}

#[wasm_bindgen]
pub fn process_batch(logs_json: &str, source_type: &str) -> String {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);
    let lines: Vec<String> = serde_json::from_str(logs_json).unwrap_or_default();
    let parser = match parsers::get_parser(source_type) {
        Some(p) => p,
        None => return serde_json::json!({"error": "unknown source", "parsed_count": 0}).to_string()
    };
    let mut feature_matrix: Vec<Vec<f64>> = Vec::new();
    let mut anomaly_count = 0usize;
    for line in &lines {
        if let Ok(event) = parser.parse(line) {
            let fvec = features::extract(&event);
            if event.local_severity > 0.5 { anomaly_count += 1; }
            feature_matrix.push(fvec);
        }
    }
    serde_json::json!({
        "parsed_count": feature_matrix.len(),
        "anomaly_count": anomaly_count,
        "feature_matrix": feature_matrix,
        "feature_names": features::FEATURE_NAMES,
    }).to_string()
}

#[wasm_bindgen]
pub fn compute_ueba_features(events_json: &str) -> String {
    let events: Vec<event::KalpixkEvent> = serde_json::from_str(events_json).unwrap_or_default();
    if events.is_empty() {
        return serde_json::json!({
            "features": vec![0.0f64; features::FEATURE_DIM],
            "risk_score": 0.0,
            "event_count": 0
        }).to_string();
    }
    let mut avg = vec![0.0f64; features::FEATURE_DIM];
    let n = events.len() as f64;
    for ev in &events {
        let fvec = features::extract(ev);
        for (i, v) in fvec.iter().enumerate() { avg[i] += v / n; }
    }
    serde_json::json!({
        "features": avg,
        "risk_score": avg[1],
        "event_count": events.len(),
        "contract_version": FEATURE_CONTRACT_VERSION,
    }).to_string()
}

#[wasm_bindgen]
pub fn parse_and_extract(raw_log: &str) -> Result<String, JsValue> {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);
    let event: event::KalpixkEvent = serde_json::from_str(raw_log)
        .map_err(|e| JsValue::from_str(&format!("Parse error: {}", e)))?;
    let feature_vec = features::extract(&event);
    Ok(serde_json::json!({
        "features": feature_vec,
        "feature_dim": features::FEATURE_DIM,
        "event_type": format!("{:?}", event.event_type),
        "local_severity": event.local_severity,
        "contract_version": FEATURE_CONTRACT_VERSION,
    }).to_string())
}

#[wasm_bindgen]
pub fn get_feature_names() -> String {
    serde_json::to_string(features::FEATURE_NAMES).unwrap_or_default()
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

#[wasm_bindgen]
pub fn validate_input_wasp(raw: &str, max_len: usize) -> String {
    serde_json::to_string(&wasp::validate_input(raw, max_len)).unwrap_or_default()
}

#[wasm_bindgen]
pub fn check_memory_bounds_wasp(offset: usize, length: usize, max_memory: usize) -> String {
    serde_json::to_string(&wasp::check_memory_bounds(offset, length, max_memory)).unwrap_or_default()
}

#[wasm_bindgen]
pub fn analyze_defense_nodes(event_json: &str) -> String {
    use defense_nodes::{analyze_all_nodes, get_max_severity, should_lockdown};
    let event: event::KalpixkEvent = match serde_json::from_str(event_json) {
        Ok(e) => e,
        Err(_) => return serde_json::json!({"error": "Invalid event JSON"}).to_string(),
    };
    serde_json::json!({
        "nodes": analyze_all_nodes(&event),
        "max": get_max_severity(&event),
        "lockdown_triggered": should_lockdown(&event),
    }).to_string()
}

#[wasm_bindgen]
pub fn check_lockdown(event_json: &str) -> bool {
    let event: event::KalpixkEvent = match serde_json::from_str(event_json) {
        Ok(e) => e,
        Err(_) => return false,
    };
    defense_nodes::should_lockdown(&event)
}
