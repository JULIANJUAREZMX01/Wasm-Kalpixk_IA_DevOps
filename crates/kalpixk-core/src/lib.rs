//! kalpixk-core — WASM-native log parser & feature extractor
pub mod event;
pub mod features;

use wasm_bindgen::prelude::*;

pub const FEATURE_CONTRACT_VERSION: &str = "1.0.0";

/// Parsea un log JSON crudo y extrae el vector de 32 features.
#[wasm_bindgen]
pub fn parse_and_extract(raw_log: &str) -> Result<String, JsValue> {
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
pub fn health_check() -> String {
    serde_json::json!({
        "status": "ok",
        "module": "kalpixk-core",
        "feature_dim": features::FEATURE_DIM,
        "contract_version": FEATURE_CONTRACT_VERSION,
    }).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::{KalpixkEvent, EventType};
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
            assert!(*f >= 0.0 && *f <= 1.0,
                "Feature {} ({}) out of range: {}",
                i, features::FEATURE_NAMES[i], f);
        }
    }
}
