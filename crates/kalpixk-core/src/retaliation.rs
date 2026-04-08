//! retaliation.rs — Engine de Contra-Defensa y Exterminio
//!
//! Orquesta la respuesta ofensiva de Kalpixk contra atacantes confirmados.

use crate::event::KalpixkEvent;
use crate::severity::{get_redteam_mapping, OffenseLevel, RetaliationType};
use lazy_static::lazy_static;
use std::collections::HashMap;
use std::sync::Mutex;

lazy_static! {
    /// Registro de agresores activos y su nivel de represalia
    static ref ATTACKER_REGISTRY: Mutex<HashMap<String, AttackerState>> = Mutex::new(HashMap::new());
}

#[derive(Debug, Clone)]
struct AttackerState {
    ip: String,
    score: f64,
    last_node: String,
    retaliation: RetaliationType,
    threat_count: u32,
}

/// Ejecuta la lógica de represalia basada en el evento detectado
pub fn execute_retaliation(
    event: &KalpixkEvent,
    level: OffenseLevel,
    score: f64,
    node: &str,
) -> Option<String> {
    if level < OffenseLevel::Anomaly {
        return None;
    }

    let mut registry = ATTACKER_REGISTRY.lock().unwrap();
    let state = registry
        .entry(event.source.clone())
        .or_insert(AttackerState {
            ip: event.source.clone(),
            score: 0.0,
            last_node: node.to_string(),
            retaliation: RetaliationType::None,
            threat_count: 0,
        });

    state.score = (state.score + score).min(1.0);
    state.threat_count += 1;
    state.last_node = node.to_string();

    // Determinar tipo de represalia técnica
    let mapping = get_redteam_mapping(&event.raw);
    state.retaliation = if let Some(m) = mapping {
        m.recommended_retaliation.clone()
    } else {
        match level {
            OffenseLevel::Exterminio => RetaliationType::RecursiveZipBomb,
            OffenseLevel::Critical => RetaliationType::PoisonPointers,
            _ => RetaliationType::Block,
        }
    };

    let action = format!("{:?}", state.retaliation);

    // Simular generación de payload (en WASM esto se pasaría al host JS)
    let result = serde_json::json!({
        "target": state.ip,
        "offense_level": format!("{:?}", level),
        "max_score": state.score,
        "retaliation_action": action,
        "node": state.last_node,
        "threat_count": state.threat_count,
        "timestamp": chrono::Utc::now().timestamp_millis(),
    });

    Some(result.to_string())
}

/// Limpia el registro de agresores (usado en tests)
pub fn reset_attacker_registry() {
    let mut registry = ATTACKER_REGISTRY.lock().unwrap();
    registry.clear();
}
