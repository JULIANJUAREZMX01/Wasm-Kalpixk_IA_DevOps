//! kalpixk-core — WASM-native log parser & feature extractor
pub mod event;
pub mod features;
pub mod parsers;

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

/// Parsea una línea de log y retorna JSON con el evento + severidad.
/// Retorna None si la línea está vacía o no se puede parsear.
#[wasm_bindgen]
pub fn parse_log_line(raw: &str, source_type: &str) -> Option<String> {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);
    let parser = parsers::get_parser(source_type)?;
    let event = parser.parse(raw).ok()?;
    serde_json::to_string(&serde_json::json!({
        "event_type": format!("{:?}", event.event_type),
        "local_severity": event.local_severity,
        "source": event.source,
        "user": event.user,
        "fingerprint": event.fingerprint,
        "source_type": event.source_type,
    }))
    .ok()
}

/// Procesa un batch de logs JSON y retorna feature matrix + metadata.
/// Input: JSON array de strings
/// Output: { parsed_count, anomaly_count, feature_matrix: [[f64;32]] }
#[wasm_bindgen]
pub fn process_batch(logs_json: &str, source_type: &str) -> String {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);
    let lines: Vec<String> = serde_json::from_str(logs_json).unwrap_or_default();
    let parser = match parsers::get_parser(source_type) {
        Some(p) => p,
        None => {
            return serde_json::json!({
                "error": format!("Unknown source_type: {}", source_type),
                "parsed_count": 0,
                "feature_matrix": []
            })
            .to_string()
        }
    };

    let mut feature_matrix: Vec<Vec<f64>> = Vec::new();
    let mut anomaly_count = 0usize;
    let threshold = 0.5f64;

    for line in &lines {
        if line.trim().is_empty() {
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
        "contract_version": FEATURE_CONTRACT_VERSION,
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

/// Parsea un log JSON crudo (formato interno) y extrae features.
#[wasm_bindgen]
pub fn parse_and_extract(raw_log: &str) -> Result<String, JsValue> {
    SHARED_ACCESS_COUNT.fetch_add(1, Ordering::Relaxed);
    let event: event::KalpixkEvent = serde_json::from_str(raw_log)
        .map_err(|e| JsValue::from_str(&format!("Parse error: {}", e)))?;
    let feature_vec = features::extract(&event);
    let result = serde_json::json!({
        "features": feature_vec,
        "feature_dim": features::FEATURE_DIM,
        "event_type": format!("{:?}", event.event_type),
        "local_severity": event.local_severity,
        "contract_version": FEATURE_CONTRACT_VERSION,
    });
    Ok(result.to_string())
}

/// Retorna los nombres de las 32 features
#[wasm_bindgen]
pub fn get_feature_names() -> String {
    serde_json::to_string(features::FEATURE_NAMES).unwrap_or_default()
}

/// Health check del módulo
#[wasm_bindgen]
pub fn health_check() -> String {
    serde_json::json!({
        "status": "ok",
        "module": "kalpixk-core",
        "feature_dim": features::FEATURE_DIM,
        "contract_version": FEATURE_CONTRACT_VERSION,
    })
    .to_string()
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
        assert_eq!(h["feature_dim"], 32);
    }
}
