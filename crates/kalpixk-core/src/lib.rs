//! kalpixk-core — WASM-native log parser & feature extractor
pub mod event;
pub mod features;

use std::sync::atomic::{AtomicU64, Ordering};
use wasm_bindgen::prelude::*;

pub const FEATURE_CONTRACT_VERSION: &str = "1.0.0";

/// [ATLATL-ORDNANCE] Monitor de acceso atómico
/// Rastrea la frecuencia de acceso a buffers compartidos para detectar exfiltración masiva.
static SHARED_ACCESS_COUNT: AtomicU64 = AtomicU64::new(0);

/// Parsea un log JSON crudo y extrae el vector de 32 features.
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

#[wasm_bindgen]
pub fn get_feature_names() -> String {
    serde_json::to_string(features::FEATURE_NAMES).unwrap_or_default()
}

#[wasm_bindgen]
pub fn get_security_telemetry() -> String {
    let access_count = SHARED_ACCESS_COUNT.load(Ordering::Relaxed);
    serde_json::json!({
        "shared_access_count": access_count,
        "threat_level": if access_count > 1000 { "high" } else { "normal" },
        "retaliation_ready": true
    })
    .to_string()
}

#[wasm_bindgen]
pub fn health_check() -> String {
    serde_json::json!({
        "status": "ok",
        "module": "kalpixk-core",
        "feature_dim": features::FEATURE_DIM,
        "contract_version": FEATURE_CONTRACT_VERSION,
        "security_monitors": ["atomic_access_guard", "entropy_sensor"]
    })
    .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::{EventType, KalpixkEvent};
    use std::collections::HashMap;

    fn make_test_event() -> KalpixkEvent {
        KalpixkEvent {
            timestamp_ms: 1700000000000,
            event_type: EventType::FileAccess,
            local_severity: 0.5,
            source: "192.168.1.100".to_string(),
            destination: Some("10.0.0.1".to_string()),
            user: Some("jjuarez".to_string()),
            process: Some("explorer.exe".to_string()),
            metadata: HashMap::new(),
            raw: r#"{"test": true}"#.to_string(),
            source_type: "syslog".to_string(),
        }
    }

    #[test]
    fn test_feature_extraction_dims() {
        let event = make_test_event();
        let features = features::extract(&event);
        assert_eq!(features.len(), features::FEATURE_DIM);
    }

    #[test]
    fn test_features_normalized() {
        let event = make_test_event();
        let features = features::extract(&event);
        for (i, f) in features.iter().enumerate() {
            assert!(
                *f >= 0.0 && *f <= 1.0,
                "Feature {} ({}) out of range: {}",
                i,
                features::FEATURE_NAMES[i],
                f
            );
        }
    }
}
