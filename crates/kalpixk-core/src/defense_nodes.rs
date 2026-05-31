#![allow(dead_code)]
//! Defense Nodes — MITRE ATT&CK Detection for Kalpixk
//!
//! 8 nodes for detecting Red Team techniques:
//! - Node-1 to Node-6: MITRE Heuristics
//! - Node-7: MESH_INTEGRITY (v4.0-ATLATL)
//! - Node-8: GUERRILLA (v8.0.0-GUERRILLA)
//!
//! [ATLATL-ORDNANCE] Version 8.0: Guerrilla Mesh Coordination

use crate::event::KalpixkEvent;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::sync::Mutex;

/// [ATLATL-ORDNANCE] Global Threat Data Structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThreatSignature {
    pub source: String,
    pub node_id: String,
    pub technique: String,
    pub score: f64,
    pub timestamp: i64,
    pub signature: Option<String>,
}

lazy_static::lazy_static! {
    static ref GLOBAL_THREAT_REGISTRY: Mutex<HashSet<String>> = Mutex::new(HashSet::new());
    static ref THREAT_SIGNATURE_DB: Mutex<HashMap<String, ThreatSignature>> = Mutex::new(HashMap::new());
    static ref MESH_NODES: Mutex<HashMap<String, i64>> = Mutex::new(HashMap::new());
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct SeverityScore(pub f64);

impl SeverityScore {
    pub fn new(score: f64) -> Self {
        Self(score.clamp(0.0, 1.0))
    }

    pub fn as_f64(&self) -> f64 {
        self.0
    }

    pub fn as_level(&self) -> SeverityLevel {
        match self.0 {
            0.0..=0.29 => SeverityLevel::Clean,
            0.30..=0.49 => SeverityLevel::Suspicious,
            0.50..=0.69 => SeverityLevel::Anomaly,
            _ => SeverityLevel::Critical,
        }
    }
}

pub fn process_ghost_signal(node_id: &str, _payload: &str) {
    if let Ok(mut nodes) = MESH_NODES.lock() {
        nodes.insert(
            format!("v8-ghost-{}", node_id),
            chrono::Utc::now().timestamp_millis(),
        );
    }
}

pub fn register_node_heartbeat(node_id: String) {
    if let Ok(mut nodes) = MESH_NODES.lock() {
        nodes.insert(node_id, chrono::Utc::now().timestamp_millis());
    }
}

pub fn get_active_nodes() -> Vec<String> {
    if let Ok(nodes) = MESH_NODES.lock() {
        let now = chrono::Utc::now().timestamp_millis();
        nodes
            .iter()
            .filter(|(_, &ts)| now - ts < 60000)
            .map(|(id, _)| id.clone())
            .collect()
    } else {
        Vec::new()
    }
}

pub fn get_global_blacklist() -> Vec<String> {
    if let Ok(registry) = GLOBAL_THREAT_REGISTRY.lock() {
        registry.iter().cloned().collect()
    } else {
        Vec::new()
    }
}

pub fn register_threat_signature(sig: ThreatSignature) {
    if let Ok(mut registry) = GLOBAL_THREAT_REGISTRY.lock() {
        registry.insert(sig.source.clone());
    }
    if let Ok(mut db) = THREAT_SIGNATURE_DB.lock() {
        db.insert(sig.source.clone(), sig);
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum SeverityLevel {
    Clean,
    Suspicious,
    Anomaly,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeResult {
    pub node: String,
    pub score: f64,
    pub level: SeverityLevel,
    pub mitre_techniques: Vec<String>,
    pub description: String,
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 1-6: MITRE HEURISTICS
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_reconnaissance(
    _event: &KalpixkEvent,
    raw_lower: &str,
    user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();

    if raw_lower.contains("dns") && (raw_lower.contains("enum") || raw_lower.contains("axfr")) {
        score += 0.4;
        techniques.push("T1595".to_string());
    }
    if raw_lower.contains("scan") || user_lower.contains("shodan") || user_lower.contains("nuclei")
    {
        score += 0.6;
        techniques.push("T1595".to_string());
    }

    NodeResult {
        node: "NODE-1: RECON".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Recon score: {:.2}", score),
    }
}

pub fn detect_lateral_movement(
    event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let dst_port = event
        .metadata
        .get("dst_port")
        .and_then(|v| v.as_i64())
        .unwrap_or(0);

    if [5985, 5986, 3389, 22, 445].contains(&dst_port) {
        score += 0.3;
        techniques.push("T1021".to_string());
    }
    if raw_lower.contains("psexec") || raw_lower.contains("wmic") {
        score += 0.6;
        techniques.push("T1021".to_string());
    }

    NodeResult {
        node: "NODE-2: LATERAL".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Lateral movement score: {:.2}", score),
    }
}

pub fn detect_credential_theft(
    _event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    if raw_lower.contains("lsass") || raw_lower.contains("mimikatz") {
        score += 0.95;
        techniques.push("T1003".to_string());
    }
    NodeResult {
        node: "NODE-3: CREDS".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Credential theft score: {:.2}", score),
    }
}

pub fn detect_payload_execution(
    _event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    if raw_lower.contains("powershell")
        && (raw_lower.contains("-enc") || raw_lower.contains("bypass"))
    {
        score += 0.8;
        techniques.push("T1059.001".to_string());
    }
    if raw_lower.contains("msfvenom") || raw_lower.contains("meterpreter") {
        score += 1.0;
        techniques.push("T1059".to_string());
    }
    NodeResult {
        node: "NODE-4: PAYLOAD".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Execution score: {:.2}", score),
    }
}

pub fn detect_rce_injection(
    _event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    if raw_lower.contains("union select") || raw_lower.contains("information_schema") {
        score += 0.8;
        techniques.push("T1190".to_string());
    }
    if raw_lower.contains("jndi") || raw_lower.contains("ldap") {
        score += 1.0;
        techniques.push("T1210".to_string());
    }
    NodeResult {
        node: "NODE-5: RCE/INJ".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("RCE score: {:.2}", score),
    }
}

pub fn detect_exfiltration(
    _event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    if raw_lower.contains("rclone") || raw_lower.contains("mega.nz") {
        score += 0.8;
        techniques.push("T1567".to_string());
    }
    NodeResult {
        node: "NODE-6: EXFIL".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Exfil score: {:.2}", score),
    }
}

pub fn detect_mesh_integrity(event: &KalpixkEvent) -> NodeResult {
    let mut score = 0.0;
    if event.source_type == "mesh_sync" {
        if event.metadata.get("mesh_token").is_none() {
            score = 1.0;
        }
    }
    NodeResult {
        node: "NODE-7: MESH_INTEGRITY".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: vec!["T1557".to_string()],
        description: "Mesh integrity validation".to_string(),
    }
}

pub fn detect_guerrilla_threat(event: &KalpixkEvent) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = event.raw.to_lowercase();

    if raw.contains("guerrilla") || raw.contains("jit_shield") || raw.contains("entropy_shredder") {
        score += 0.9;
        techniques.push("T1595".to_string());
    }

    if event.source_type == "guerrilla_strike" {
        score = 1.0;
        techniques.push("T1548".to_string());
    }

    NodeResult {
        node: "NODE-8: GUERRILLA".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: "Coordination of Stage 8 retaliation against v8 guerrilla threats".to_string(),
    }
}

pub fn analyze_all_nodes(event: &KalpixkEvent) -> Vec<NodeResult> {
    let raw_lower = event.raw.to_lowercase();
    let user_lower = event.user.as_deref().unwrap_or("").to_lowercase();
    let source_lower = event.source.to_lowercase();

    vec![
        detect_reconnaissance(event, &raw_lower, &user_lower, &source_lower),
        detect_lateral_movement(event, &raw_lower, &user_lower, &source_lower),
        detect_credential_theft(event, &raw_lower, &user_lower, &source_lower),
        detect_payload_execution(event, &raw_lower, &user_lower, &source_lower),
        detect_rce_injection(event, &raw_lower, &user_lower, &source_lower),
        detect_exfiltration(event, &raw_lower, &user_lower, &source_lower),
        detect_mesh_integrity(event),
        detect_guerrilla_threat(event),
    ]
}

pub fn get_max_severity(event: &KalpixkEvent) -> NodeResult {
    let results = analyze_all_nodes(event);
    results
        .into_iter()
        .max_by(|a, b| {
            a.score
                .partial_cmp(&b.score)
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .unwrap()
}

pub fn should_lockdown(event: &KalpixkEvent) -> bool {
    let score = get_max_severity(event).score;
    if score >= 0.7 {
        register_threat_signature(ThreatSignature {
            source: event.source.clone(),
            node_id: "WASM-CORE-GUERRILLA-V8".to_string(),
            technique: "TA-GUERRILLA-V8".to_string(),
            score,
            timestamp: chrono::Utc::now().timestamp_millis(),
            signature: Some("V8_GUERRILLA_SIG".to_string()),
        });
        return true;
    }
    false
}

pub fn sync_threats(external_threats: Vec<String>) {
    if let Ok(mut registry) = GLOBAL_THREAT_REGISTRY.lock() {
        for threat in external_threats {
            registry.insert(threat);
        }
    }
}
