#![allow(dead_code)]
//! Defense Nodes — MITRE ATT&CK Detection for Kalpixk
//!
//! 6 nodes for detecting Red Team techniques:
//! - Node-1: Reconnaissance
//! - Node-2: Lateral Movement
//! - Node-3: Credential Theft
//! - Node-4: Payload Execution
//! - Node-5: RCE / Injection
//! - Node-6: Exfiltration
//!
//! [ATLATL-ORDNANCE] Version 3.1: GuerrillaMesh & Orchestrated Retaliation

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
}

lazy_static::lazy_static! {
    /// Decentralized Peer-to-Peer Threat Sharing (GuerrillaMode)
    static ref GLOBAL_THREAT_REGISTRY: Mutex<HashSet<String>> = Mutex::new(HashSet::new());

    /// [ATLATL-ORDNANCE] Detailed Threat Signatures for P2P Sync
    static ref THREAT_SIGNATURE_DB: Mutex<HashMap<String, ThreatSignature>> = Mutex::new(HashMap::new());

    /// [ATLATL-ORDNANCE] GuerrillaMesh Node Health
    static ref MESH_NODES: Mutex<HashMap<String, i64>> = Mutex::new(HashMap::new());
}

/// Severity score from 0.0 to 1.0
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

/// [ATLATL-ORDNANCE] GuerrillaMesh: Register Node Heartbeat
pub fn register_node_heartbeat(node_id: String) {
    if let Ok(mut nodes) = MESH_NODES.lock() {
        nodes.insert(node_id, chrono::Utc::now().timestamp_millis());
    }
}

/// [ATLATL-ORDNANCE] GuerrillaMesh: Get Active Nodes
pub fn get_active_nodes() -> Vec<String> {
    if let Ok(nodes) = MESH_NODES.lock() {
        let now = chrono::Utc::now().timestamp_millis();
        nodes
            .iter()
            .filter(|(_, &ts)| now - ts < 60000) // Active if seen in last 60s
            .map(|(id, _)| id.clone())
            .collect()
    } else {
        Vec::new()
    }
}

/// [ATLATL-ORDNANCE] Export Global Blacklist for synchronization
pub fn get_global_blacklist() -> Vec<String> {
    if let Ok(registry) = GLOBAL_THREAT_REGISTRY.lock() {
        registry.iter().cloned().collect()
    } else {
        Vec::new()
    }
}

/// [ATLATL-ORDNANCE] Detailed Sync Logic
pub fn register_threat_signature(sig: ThreatSignature) {
    if let Ok(mut registry) = GLOBAL_THREAT_REGISTRY.lock() {
        registry.insert(sig.source.clone());
    }
    if let Ok(mut db) = THREAT_SIGNATURE_DB.lock() {
        db.insert(sig.source.clone(), sig);
    }
}

pub fn get_threat_signatures() -> Vec<ThreatSignature> {
    if let Ok(db) = THREAT_SIGNATURE_DB.lock() {
        db.values().cloned().collect()
    } else {
        Vec::new()
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

impl SeverityLevel {
    pub fn as_str(&self) -> &'static str {
        match self {
            SeverityLevel::Clean => "CLEAN",
            SeverityLevel::Suspicious => "SUSPICIOUS",
            SeverityLevel::Anomaly => "ANOMALY",
            SeverityLevel::Critical => "CRITICAL",
        }
    }
}

/// Defense node detection result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeResult {
    pub node: String,
    pub score: f64,
    pub level: SeverityLevel,
    pub mitre_techniques: Vec<String>,
    pub description: String,
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 1: RECONNAISSANCE DETECTOR
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_reconnaissance(
    _event: &KalpixkEvent,
    raw_lower: &str,
    user_lower: &str,
    source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let _source = source_lower;
    let user = user_lower;
    let raw = raw_lower;

    // Advanced heuristics for recon
    if raw.contains("dns") && (raw.contains("enum") || raw.contains("axfr") || raw.contains("zone"))
    {
        score += 0.4;
        techniques.push("T1595".to_string());
    }

    if raw.contains("scan") || raw.contains("syn") || raw.contains("ack") || raw.contains("fin") {
        if raw.contains("nmap") || raw.contains("masscan") || raw.contains("zmap") {
            score += 0.6;
        } else {
            score += 0.3;
        }
        techniques.push("T1595".to_string());
    }

    if raw.contains(".git")
        || raw.contains(".env")
        || raw.contains(".aws/credentials")
        || raw.contains("cve-")
        || raw.contains("nuclei")
    {
        score += 0.5;
        techniques.push("T1593".to_string());
    }

    if user.contains("spiderfoot")
        || user.contains("shodan")
        || user.contains("censys")
        || user.contains("nuclei")
    {
        score += 0.5;
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

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 2: LATERAL MOVEMENT DETECTOR
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_lateral_movement(
    event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = raw_lower;
    let metadata = &event.metadata;

    let dst_port = metadata
        .get("dst_port")
        .and_then(|v| v.as_i64())
        .unwrap_or(0) as i32;
    if [5985, 5986, 3389, 22, 445].contains(&dst_port) {
        score += 0.3;
        techniques.push("T1021".to_string());
    }

    if raw.contains("psexec")
        || raw.contains("wmic")
        || raw.contains("winrm")
        || raw.contains("ssh -o")
    {
        score += 0.6;
        techniques.push("T1021".to_string());
    }

    if raw.contains("responder") || raw.contains("poison") || raw.contains("llmnr") {
        score += 0.7;
        techniques.push("T1557".to_string());
    }

    NodeResult {
        node: "NODE-2: LATERAL".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Lateral movement score: {:.2}", score),
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 3: CREDENTIAL THEFT DETECTOR
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_credential_theft(
    _event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = raw_lower;

    if raw.contains("lsass")
        || raw.contains("mimikatz")
        || raw.contains("sekurlsa")
        || raw.contains("logonpasswords")
    {
        score += 0.95;
        techniques.push("T1003".to_string());
    }

    if raw.contains("ntds.dit") || raw.contains("shadowcopy") || raw.contains("vssadmin") {
        score += 0.9;
        techniques.push("T1003.003".to_string());
    }

    if raw.contains("kerberoast") || raw.contains("tgs-rep") || raw.contains("as-rep") {
        score += 0.8;
        techniques.push("T1558".to_string());
    }

    NodeResult {
        node: "NODE-3: CREDS".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Credential theft score: {:.2}", score),
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 4: PAYLOAD/EXECUTION DETECTOR
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_payload_execution(
    _event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = raw_lower;

    if raw.contains("powershell")
        && (raw.contains("-enc")
            || raw.contains("-e ")
            || raw.contains("bypass")
            || raw.contains("hidden"))
    {
        score += 0.8;
        techniques.push("T1059.001".to_string());
    }

    if (raw.contains("bitsadmin")
        || raw.contains("certutil")
        || raw.contains("curl -s")
        || raw.contains("wget -q"))
        && (raw.contains("http")
            || raw.contains(".exe")
            || raw.contains(".sh")
            || raw.contains(".ps1"))
    {
        score += 0.7;
        techniques.push("T1105".to_string());
    }

    if raw.contains("msfvenom") || raw.contains("meterpreter") || raw.contains("cobaltstrike") {
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

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 5: RCE / INJECTION DETECTOR
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_rce_injection(
    _event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = raw_lower;

    if raw.contains("union select")
        || raw.contains("order by")
        || raw.contains("information_schema")
    {
        score += 0.8;
        techniques.push("T1190".to_string());
    }

    if raw.contains("base64")
        || raw.contains("eval(")
        || raw.contains("system(")
        || raw.contains("exec(")
    {
        score += 0.7;
        techniques.push("T1059".to_string());
    }

    if raw.contains("${") && (raw.contains("jndi") || raw.contains("ldap") || raw.contains("rmi")) {
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

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 6: EXFILTRATION DETECTOR
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_exfiltration(
    _event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = raw_lower;

    if raw.contains("rclone")
        || raw.contains("mega.nz")
        || raw.contains("dropbox")
        || raw.contains("googledrive")
    {
        score += 0.8;
        techniques.push("T1567".to_string());
    }

    if (raw.contains(".zip") || raw.contains(".7z") || raw.contains(".rar")) && raw.contains("-p") {
        score += 0.6;
        techniques.push("T1074".to_string());
    }

    if (raw.contains("bitsadmin")
        || raw.contains("certutil")
        || raw.contains("curl -s")
        || raw.contains("wget -q"))
        && (raw.contains("http")
            || raw.contains(".exe")
            || raw.contains(".sh")
            || raw.contains(".ps1"))
    {
        score += 0.7;
        techniques.push("T1105".to_string());
    }

    if raw.contains("dns") && raw.contains("txt") && raw.len() > 200 {
        score += 0.7;
        techniques.push("T1048".to_string());
    }

    NodeResult {
        node: "NODE-6: EXFIL".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Exfil score: {:.2}", score),
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 7: MESH_INTEGRITY DETECTOR
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_mesh_integrity(
    event: &KalpixkEvent,
    raw_lower: &str,
    _user_lower: &str,
    _source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = raw_lower;

    // Detect mesh spoofing or signature tampering
    if raw.contains("mesh_sync") && (raw.contains("spoof") || raw.contains("replay")) {
        score += 0.8;
        techniques.push("T1557".to_string()); // Adversary-in-the-Middle
    }

    if raw.contains("node_id") && raw.len() > 500 && raw.contains("threats") {
        // Suspiciously large mesh update payload
        score += 0.5;
        techniques.push("T1499".to_string()); // Endpoint DoS
    }

    // Check for unauthorized node registration patterns
    if raw.contains("register_node") && !raw.contains("WASM-CORE-ATLATL") {
        score += 0.6;
        techniques.push("T1204".to_string()); // User Execution
    }

    // Verify cryptographic fingerprint (simulated)
    if let Some(fingerprint) = event.metadata.get("fingerprint").and_then(|v| v.as_str()) {
        if fingerprint.len() < 32 {
            score += 0.4;
            techniques.push("T1036".to_string()); // Masquerading
        }
    }

    NodeResult {
        node: "NODE-7: MESH".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: format!("Mesh integrity score: {:.2}", score),
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// COMPLETE ANALYSIS — Run all 7 nodes
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn analyze_all_nodes(event: &KalpixkEvent) -> Vec<NodeResult> {
    let raw_lower = event.raw.to_lowercase();
    let user_lower = event
        .user
        .as_deref()
        .map(|s| s.to_lowercase())
        .unwrap_or_default();
    let source_lower = event.source.to_lowercase();

    vec![
        detect_reconnaissance(event, &raw_lower, &user_lower, &source_lower),
        detect_lateral_movement(event, &raw_lower, &user_lower, &source_lower),
        detect_credential_theft(event, &raw_lower, &user_lower, &source_lower),
        detect_payload_execution(event, &raw_lower, &user_lower, &source_lower),
        detect_rce_injection(event, &raw_lower, &user_lower, &source_lower),
        detect_exfiltration(event, &raw_lower, &user_lower, &source_lower),
        detect_mesh_integrity(event, &raw_lower, &user_lower, &source_lower),
    ]
}

pub fn get_max_severity(event: &KalpixkEvent) -> NodeResult {
    let results = analyze_all_nodes(event);
    results
        .into_iter()
        .max_by(|a, b| a.score.partial_cmp(&b.score).unwrap())
        .unwrap()
}

pub fn should_lockdown(event: &KalpixkEvent) -> bool {
    let score = get_max_severity(event).score;
    if score >= 0.7 {
        // [ATLATL-ORDNANCE] GuerrillaMode: Sync threat to decentralized registry
        register_threat_signature(ThreatSignature {
            source: event.source.clone(),
            node_id: "WASM-CORE-ATLATL".to_string(),
            technique: "TA-DETECTION".to_string(),
            score,
            timestamp: chrono::Utc::now().timestamp_millis(),
        });
        return true;
    }

    // Check global blacklist
    if let Ok(registry) = GLOBAL_THREAT_REGISTRY.lock() {
        if registry.contains(&event.source) {
            return true;
        }
    }

    false
}

/// [ATLATL-ORDNANCE] P2P Threat Sync
pub fn sync_threats(external_threats: Vec<String>) {
    if let Ok(mut registry) = GLOBAL_THREAT_REGISTRY.lock() {
        for threat in external_threats {
            registry.insert(threat);
        }
    }
}
