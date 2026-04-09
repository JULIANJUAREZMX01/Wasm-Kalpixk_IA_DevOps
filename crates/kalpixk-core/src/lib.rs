pub mod metrics;
pub mod entropy;
pub mod runtime_features;

// Keep existing modules if they exist and are useful
pub mod defense_nodes;
pub mod event;
pub mod features;
pub mod parsers;
pub mod payloads;
pub mod security;
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

    use defense_nodes::{analyze_all_nodes, get_max_severity, should_lockdown};

    let all_nodes = analyze_all_nodes(&event);
    let max = get_max_severity(&event);
    let lockdown = should_lockdown(&event);

    // Nodo con score más alto
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

/// [ATLATL-ORDNANCE] Security Telemetry
#[wasm_bindgen]
pub fn get_security_telemetry() -> String {
    let access_count = SHARED_ACCESS_COUNT.load(Ordering::Relaxed);
    serde_json::json!({
        "shared_access_count": access_count,
        "threat_level": if access_count > 1000 { "high" } else { "normal" },
        "timestamp": chrono::Utc::now().timestamp_millis(),
    }).to_string()
}

/// Bloquea un módulo WASM y genera reporte forense.
#[wasm_bindgen]
pub fn wasm_lockdown(node: &str, score: f64, event_json: &str) -> String {
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

/// Parsea una línea de log y retorna JSON con el evento + severidad.
#[wasm_bindgen]
pub fn parse_log_line(raw: &str, source_type: &str) -> Option<String> {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);

    // [ATLATL-ORDNANCE] Security Guard
    if !security::SecurityGuard::validate_raw_log(raw) {
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

/// Procesa un batch de logs JSON y retorna feature matrix + metadata.
#[wasm_bindgen]
pub fn process_batch(logs_json: &str, source_type: &str) -> String {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);
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
        if !security::SecurityGuard::validate_raw_log(line) { continue; }
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

/// Computa features UEBA desde una sesión de eventos JSON.
/// Input: JSON array de KalpixkEvent
/// Output: { features: [f64;32], risk_score: f64 }
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

    // Promediar features de todos los eventos
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
        "contract_version": FEATURE_CONTRACT_VERSION,
    })
    .to_string()
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
