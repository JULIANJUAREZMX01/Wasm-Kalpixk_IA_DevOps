//! kalpixk-core — WASM-native log parser & feature extractor
pub mod event;
pub mod features;
pub mod parsers;
pub mod severity;
pub mod defense_nodes;
pub mod retaliation;

use std::sync::atomic::{AtomicU64, Ordering};
use wasm_bindgen::prelude::*;

pub const FEATURE_CONTRACT_VERSION: &str = "1.0.0";

static SHARED_ACCESS_COUNT: AtomicU64 = AtomicU64::new(0);

/// Retorna la versión del motor
#[wasm_bindgen]
pub fn version() -> String {
    format!(
        "kalpixk-core/{} (contract {})",
        env!("CARGO_PKG_VERSION"),
        FEATURE_CONTRACT_VERSION
    )
}

/// Analiza un evento JSON y ejecuta represalias si es necesario.
/// Exportado a JS para monitoreo activo.
#[wasm_bindgen]
pub fn analyze_and_retaliate(event_json: &str) -> String {
    let event: event::KalpixkEvent = match serde_json::from_str(event_json) {
        Ok(e) => e,
        Err(e) => return serde_json::json!({"error": e.to_string()}).to_string(),
    };

    let (level, score, node) = defense_nodes::evaluate_offense_level(&event);

    let retaliation_payload = retaliation::execute_retaliation(&event, level, score, node);

    serde_json::json!({
        "offense_level": format!("{:?}", level),
        "score": score,
        "node": node,
        "retaliation": retaliation_payload.map(|p| serde_json::from_str::<serde_json::Value>(&p).unwrap_or_default()),
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
    }).to_string()
}

/// Parsea una línea de log y retorna JSON con el evento + severidad.
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
        None => return serde_json::json!({"error": "unknown source", "parsed_count": 0}).to_string(),
    };

    let mut feature_matrix: Vec<Vec<f64>> = Vec::new();
    let mut anomaly_count = 0usize;
    let threshold = 0.5f64;

    for line in &lines {
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
    }).to_string()
}

#[wasm_bindgen]
pub fn health_check() -> String {
    serde_json::json!({
        "status": "ok",
        "module": "kalpixk-core",
        "offensive_mode": true,
        "nodes": ["recon", "lateral", "credential", "payload"],
    }).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_process_batch_syslog() {
        let logs = serde_json::json!([
            "Apr  5 02:14:22 server sshd[123]: Failed password for root from 45.33.32.156 port 22",
            "Apr  5 10:00:00 server sshd[124]: Accepted publickey for jjuarez from 192.168.1.50 port 44321"
        ])
        .to_string();
        let result = process_batch(&logs, "syslog");
        let v: serde_json::Value = serde_json::from_str(&result).unwrap();
        assert_eq!(v["parsed_count"], 2);
        let matrix = v["feature_matrix"].as_array().unwrap();
        assert_eq!(matrix.len(), 2);
        assert_eq!(matrix[0].as_array().unwrap().len(), 32);
    }

    #[test]
    fn test_version() {
        let v = version();
        assert!(v.contains("kalpixk-core"));
    }

    #[test]
    fn test_health_check() {
        let h: serde_json::Value = serde_json::from_str(&health_check()).unwrap();
        assert_eq!(h["status"], "ok");
    }
}
