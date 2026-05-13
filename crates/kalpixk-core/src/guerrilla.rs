#![allow(dead_code)]
//! guerrilla.rs — Orquestación de Guerrilla Algorítmica v7.0
//!
//! Implementa la "Guillotina Algorítmica" y el "Ghost Protocol v7" para
//! la defensa descentralizada y el exterminio de infraestructuras agresoras.
//!
//! ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio."

use crate::defense_nodes::{register_threat_signature, ThreatSignature};
use crate::event::KalpixkEvent;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;

lazy_static::lazy_static! {
    /// Orquestador global de guerrilla para el nodo actual
    static ref ORCHESTRATOR: Mutex<GuerrillaOrchestrator> = Mutex::new(GuerrillaOrchestrator::new());
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggressorVector {
    pub ip: String,
    pub cumulative_score: f64,
    pub event_count: u32,
    pub last_seen: i64,
    pub phase: GuerrillaPhase,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum GuerrillaPhase {
    Monitor,      // Fase inicial, observación pasiva
    Interdiction, // Bloqueo activo de conexiones
    PhaseBlack,   // Exterminio: Guillotina Algorítmica activada
}

pub struct GuerrillaOrchestrator {
    pub aggressors: HashMap<String, AggressorVector>,
    pub ghost_mode: bool,
    pub threshold_interdiction: f64,
    pub threshold_black: f64,
}

impl GuerrillaOrchestrator {
    pub fn new() -> Self {
        Self {
            aggressors: HashMap::new(),
            ghost_mode: true,
            threshold_interdiction: 2.5, // Score acumulado para bloqueo
            threshold_black: 5.0,        // Score acumulado para Phase Black
        }
    }

    /// Evalúa un evento y actualiza el estado de guerrilla del agresor
    pub fn evaluate_agression(&mut self, event: &KalpixkEvent, score: f64) -> GuerrillaPhase {
        let now = Utc::now().timestamp();
        let vector = self
            .aggressors
            .entry(event.source.clone())
            .or_insert(AggressorVector {
                ip: event.source.clone(),
                cumulative_score: 0.0,
                event_count: 0,
                last_seen: now,
                phase: GuerrillaPhase::Monitor,
            });

        vector.cumulative_score += score;
        vector.event_count += 1;
        vector.last_seen = now;

        // Máquina de estados de la Guillotina
        if vector.cumulative_score >= self.threshold_black {
            vector.phase = GuerrillaPhase::PhaseBlack;
        } else if vector.cumulative_score >= self.threshold_interdiction {
            vector.phase = GuerrillaPhase::Interdiction;
        }

        // Si entramos en Phase Black, registramos la firma para la malla descentralizada
        if vector.phase == GuerrillaPhase::PhaseBlack {
            register_threat_signature(ThreatSignature {
                source: vector.ip.clone(),
                node_id: "ATLATL-GUERRILLA-V7".to_string(),
                technique: "ALGORITHMIC_GUILLOTINE".to_string(),
                score: vector.cumulative_score,
                timestamp: now * 1000,
                signature: Some("V7_STRIKE_CONFIRMED".to_string()),
            });
        }

        vector.phase
    }

    pub fn get_vector(&self, ip: &str) -> Option<AggressorVector> {
        self.aggressors.get(ip).cloned()
    }

    pub fn toggle_ghost_mode(&mut self, enabled: bool) {
        self.ghost_mode = enabled;
    }
}

/// Punto de entrada para el motor de guerrilla (WASM/Host bridge)
pub fn process_guerrilla_signal(json_event: &str, score: f64) -> String {
    let event: KalpixkEvent = match serde_json::from_str(json_event) {
        Ok(e) => e,
        Err(_) => return "{\"error\": \"invalid event\"}".to_string(),
    };

    let mut orch = ORCHESTRATOR.lock().unwrap();
    let phase = orch.evaluate_agression(&event, score);

    serde_json::json!({
        "status": "GUERRILLA_ACTIVE",
        "phase": format!("{:?}", phase),
        "ghost_mode": orch.ghost_mode,
        "target": event.source,
        "action": match phase {
            GuerrillaPhase::PhaseBlack => "ALGORITHMIC_GUILLOTINE",
            GuerrillaPhase::Interdiction => "BLOCK_ACTIVE",
            GuerrillaPhase::Monitor => "OBSERVE",
        },
        "retaliation_recommended": phase == GuerrillaPhase::PhaseBlack,
        "timestamp": Utc::now().timestamp_millis()
    })
    .to_string()
}

/// [ATLATL-ORDNANCE] Ghost Protocol v7: Heartbeat Ofuscado
pub fn ghost_heartbeat_v7(node_id: &str) -> String {
    let orch = ORCHESTRATOR.lock().unwrap();
    if !orch.ghost_mode {
        return "{\"status\": \"GHOST_MODE_DISABLED\"}".to_string();
    }

    // El heartbeat v7 no solo confirma vida, sincroniza el estado de la guillotina
    let active_strikes: Vec<String> = orch
        .aggressors
        .iter()
        .filter(|(_, v)| v.phase == GuerrillaPhase::PhaseBlack)
        .map(|(ip, _)| ip.clone())
        .collect();

    serde_json::json!({
        "protocol": "GHOST-v7",
        "node": node_id,
        "integrity": "ARMED",
        "active_strikes": active_strikes,
        "sync_ts": Utc::now().timestamp_millis()
    })
    .to_string()
}

pub fn get_guerrilla_status() -> String {
    let orch = ORCHESTRATOR.lock().unwrap();
    serde_json::json!({
        "aggressors_count": orch.aggressors.len(),
        "phase_black_count": orch.aggressors.values().filter(|v| v.phase == GuerrillaPhase::PhaseBlack).count(),
        "ghost_mode": orch.ghost_mode,
        "engine": "ATLATL-ORDNANCE-v7"
    }).to_string()
}
