//! Defense Nodes — MITRE ATT&CK Detection for Kalpixk
//!
//! 6 nodes for detecting Red Team techniques:
//! - Node-1: Reconnaissance
//! - Node-2: Lateral Movement
//! - Node-3: Credential Theft
//! - Node-4: Payload Execution
//! - Node-5: RCE / Injection
//! - Node-6: Exfiltration

use crate::event::KalpixkEvent;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::collections::{HashSet, HashMap};

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
    /// Decentralized Peer-to-Peer Threat Sharing (Simulated)
    static ref GLOBAL_THREAT_REGISTRY: Mutex<HashSet<String>> = Mutex::new(HashSet::new());

    /// [ATLATL-ORDNANCE] Detailed Threat Signatures for P2P Sync
    static ref THREAT_SIGNATURE_DB: Mutex<HashMap<String, ThreatSignature>> = Mutex::new(HashMap::new());
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
// MITRE ATT&CK: TA0043
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn detect_reconnaissance(
    _event: &KalpixkEvent,
    raw_lower: &str,
    user_lower: &str,
    source_lower: &str,
) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let source = source_lower;
    let user = user_lower;
    let raw = raw_lower;

    if raw.contains("dns enumeration") || raw.contains("dns_query") || raw.contains("zone_transfer") {
        score += 0.3;
        techniques.push("T1595".to_string());
    }

    if raw.contains("scan") || raw.contains(" SYN") || raw.contains("sYN") {
        score += 0.4;
        techniques.push("T1595".to_string());
    }

    if raw.contains("subdomain") || raw.contains("subenum") || source.contains("test") {
        score += 0.3;
        techniques.push("T1593".to_string());
    }

    if raw.contains("nuclei") || raw.contains("cve-") || raw.contains("vulnerability") {
        score += 0.4;
        techniques.push("T1595".to_string());
    }

    if user.contains("spiderfoot") || user.contains("nmap") || user.contains("scan") {
        score += 0.5;
        techniques.push("T1595".to_string());
    }

    NodeResult {
        node: "NODE-1: RECON".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 { format!("Reconnaissance detected (score: {:.2})", score) } else { "No reconnaissance detected".to_string() },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 2: LATERAL MOVEMENT DETECTOR
// MITRE ATT&CK: TA0008
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

    let dst_port = metadata.get("dst_port").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
    if dst_port == 5985 || dst_port == 5986 || dst_port == 3389 {
        score += 0.4;
        techniques.push("T1021".to_string());
    }

    if raw.contains("smb") || raw.contains("\\\\") || raw.contains("IPC$") || raw.contains("evil-winrm") {
        score += 0.5;
        techniques.push("T1021".to_string());
    }

    if raw.contains("llmnr") || raw.contains("nbt-ns") || raw.contains("mdns") {
        score += 0.5;
        techniques.push("T1557".to_string());
    }

    NodeResult {
        node: "NODE-2: LATERAL".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 { format!("Lateral movement detected (score: {:.2})", score) } else { "No lateral movement detected".to_string() },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 3: CREDENTIAL THEFT DETECTOR
// MITRE ATT&CK: TA0006
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

    if raw.contains("lsass") || raw.contains("mimikatz") || raw.contains("procdump") {
        score += 0.9;
        techniques.push("T1003".to_string());
    }

    if raw.contains("sam") && (raw.contains("dump") || raw.contains("read")) {
        score += 0.8;
        techniques.push("T1003".to_string());
    }

    NodeResult {
        node: "NODE-3: CREDS".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 { format!("Credential theft detected (score: {:.2})", score) } else { "No credential theft detected".to_string() },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 4: PAYLOAD/EXECUTION DETECTOR
// MITRE ATT&CK: TA0002
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

    if raw.contains("encodedcommand") || raw.contains("downloadstring") || raw.contains("iex") || raw.contains("msfvenom") {
        score += 0.8;
        techniques.push("T1059".to_string());
    }

    if raw.contains("shellcode") || raw.contains("virtualalloc") {
        score += 0.7;
        techniques.push("T1055".to_string());
    }

    NodeResult {
        node: "NODE-4: PAYLOAD".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 { format!("Payload execution detected (score: {:.2})", score) } else { "No payload execution detected".to_string() },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 5: RCE / INJECTION DETECTOR
// MITRE ATT&CK: TA0002 / TA0001
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

    // SQL Injection
    if raw.contains("select") && (raw.contains("union") || raw.contains("sleep(") || raw.contains("benchmark(")) {
        score += 0.6;
        techniques.push("T1190".to_string()); // Exploit Public-Facing Application
    }

    // Command Injection
    if raw.contains(";") && (raw.contains("cat /etc/passwd") || raw.contains("whoami") || raw.contains("id")) {
        score += 0.8;
        techniques.push("T1059".to_string());
    }

    // Log4Shell / JNDI
    if raw.contains("${jndi:ldap") || raw.contains("${jndi:rmi") {
        score += 0.95;
        techniques.push("T1210".to_string()); // Exploitation of Remote Services
    }

    NodeResult {
        node: "NODE-5: RCE/INJ".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 { format!("RCE/Injection attempt detected (score: {:.2})", score) } else { "No RCE/Injection detected".to_string() },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 6: EXFILTRATION DETECTOR
// MITRE ATT&CK: TA0010
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

    // Data staging
    if raw.contains(".zip") || raw.contains(".tar.gz") || raw.contains(".7z") {
        if raw.contains("/tmp/") || raw.contains("/var/tmp/") {
            score += 0.4;
            techniques.push("T1074".to_string()); // Data Staged
        }
    }

    // Exfiltration tools
    if raw.contains("rclone") || raw.contains("scp") || raw.contains("rsync") {
        score += 0.3;
        techniques.push("T1048".to_string()); // Exfiltration Over Alternative Protocol
    }

    // Large data transfer patterns (simulated via log strings)
    if raw.contains("size=") && (raw.contains("gb") || raw.contains("tb")) {
        score += 0.7;
        techniques.push("T1048".to_string());
    }

    NodeResult {
        node: "NODE-6: EXFIL".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 { format!("Exfiltration activity detected (score: {:.2})", score) } else { "No exfiltration detected".to_string() },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// COMPLETE ANALYSIS — Run all 6 nodes
// ═══════════════════════════════════════════════════════════════════════════════════════

pub fn analyze_all_nodes(event: &KalpixkEvent) -> Vec<NodeResult> {
    let raw_lower = event.raw.to_lowercase();
    let user_lower = event.user.as_deref().map(|s| s.to_lowercase()).unwrap_or_default();
    let source_lower = event.source.to_lowercase();

    vec![
        detect_reconnaissance(event, &raw_lower, &user_lower, &source_lower),
        detect_lateral_movement(event, &raw_lower, &user_lower, &source_lower),
        detect_credential_theft(event, &raw_lower, &user_lower, &source_lower),
        detect_payload_execution(event, &raw_lower, &user_lower, &source_lower),
        detect_rce_injection(event, &raw_lower, &user_lower, &source_lower),
        detect_exfiltration(event, &raw_lower, &user_lower, &source_lower),
    ]
}

pub fn get_max_severity(event: &KalpixkEvent) -> NodeResult {
    let results = analyze_all_nodes(event);
    results.into_iter().max_by(|a, b| a.score.partial_cmp(&b.score).unwrap()).unwrap()
}

pub fn should_lockdown(event: &KalpixkEvent) -> bool {
    let score = get_max_severity(event).score;
    if score >= 0.7 {
        // Sync threat to decentralized registry
        if let Ok(mut registry) = GLOBAL_THREAT_REGISTRY.lock() {
            registry.insert(event.source.clone());
        }
        return true;
    }

    // Check if source is already globally blacklisted
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
