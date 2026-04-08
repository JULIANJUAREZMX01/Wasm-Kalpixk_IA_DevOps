//! Defense Nodes — MITRE ATT&CK Detection for Kalpixk
//!
//! 4 nodes for detecting Red Team techniques:
//! - Node-1: Reconnaissance
//! - Node-2: Lateral Movement
//! - Node-3: Credential Theft
//! - Node-4: Payload Execution

use crate::event::{EventType, KalpixkEvent};
use serde::{Deserialize, Serialize};

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
// Sources: spiderfoot, reconftw, subzy, nuclei, gobuster, feroxbuster, Shodan, dnsrecon
// ═══════════════════════════════════════════════════════════════════════════════════════

/// Detect reconnaissance patterns
pub fn detect_reconnaissance(event: &KalpixkEvent) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let source = event.source.to_lowercase();
    let user = event.user.as_deref().map(|s| s.to_lowercase()).unwrap_or_default();
    let raw = event.raw.to_lowercase();
    
    // DNS enumeration (dnsrecon pattern)
    if raw.contains("dns enumeration") || raw.contains("dns_query") || raw.contains("zone_transfer") {
        score += 0.3;
        techniques.push("T1595".to_string()); // DNS
    }
    
    // Port scan signature (nmap, masscan)
    if raw.contains("scan") || raw.contains(" SYN") || raw.contains("sYN") {
        score += 0.4;
        techniques.push("T1595".to_string()); // Active Scanning
    }
    
    // Subdomain enumeration (subzy, reconftw)
    if raw.contains("subdomain") || raw.contains("subenum") || source.contains("test") {
        score += 0.3;
        techniques.push("T1593".to_string()); // Search Open Websites
    }
    
    // Vulnerability scanning (nuclei)
    if raw.contains("nuclei") || raw.contains("cve-") || raw.contains("vulnerability") {
        score += 0.4;
        techniques.push("T1595".to_string()); // Vulnerability Scanning
    }
    
    // Directory enumeration (gobuster, feroxbuster)
    if raw.contains("directory") || raw.contains("path") || raw.contains(" 404") {
        score += 0.2;
        techniques.push("T1087".to_string()); // Account Discovery
    }
    
    // Check for automated tool User-Agent
    if user.contains("spiderfoot") || user.contains("nmap") || user.contains("scan") {
        score += 0.5;
        techniques.push("T1595".to_string());
    }
    
    NodeResult {
        node: "NODE-1: RECON".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 {
            format!("Reconnaissance activity detected (score: {:.2})", score)
        } else {
            "No reconnaissance detected".to_string()
        },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 2: LATERAL MOVEMENT DETECTOR
// MITRE ATT&CK: TA0008
// Sources: evil-winrm, secretsdump, Responder, Rubeus, impacket
// ═══════════════════════════════════════════════════════════════════════════════════════

/// Detect lateral movement patterns
pub fn detect_lateral_movement(event: &KalpixkEvent) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = event.raw.to_lowercase();
    let metadata = &event.metadata;
    
    // WinRM activity (evil-winrm)
    let dst_port = metadata.get("dst_port")
        .and_then(|v| v.as_i64())
        .unwrap_or(0) as i32;
    if dst_port == 5985 || dst_port == 5986 {
        score += 0.4;
        techniques.push("T1021".to_string()); // Remote Services
    }
    
    // RDP lateral movement
    if dst_port == 3389 {
        score += 0.3;
        techniques.push("T1021".to_string());
    }
    
    // SMB lateral movement
    if raw.contains("smb") || raw.contains("\\\\") || raw.contains("IPC$") {
        score += 0.3;
        techniques.push("T1021".to_string()); // SMB
    }
    
    // NTLM/LLMNR relay (Responder)
    if raw.contains("llmnr") || raw.contains("nbt-ns") || raw.contains("mdns") {
        score += 0.5;
        techniques.push("T1557".to_string()); // Man-in-the-Middle
    }
    
    // Kerberos abuse (Rubeus)
    if raw.contains("kerberos") || raw.contains("ticket") || raw.contains("gtgs") {
        score += 0.5;
        techniques.push("T1558".to_string()); // Kerberos
    }
    
    // WMI lateral movement
    if raw.contains("wmi") || raw.contains("winrm") {
        score += 0.4;
        techniques.push("T1021".to_string());
    }
    
    NodeResult {
        node: "NODE-2: LATERAL".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 {
            format!("Lateral movement detected (score: {:.2})", score)
        } else {
            "No lateral movement detected".to_string()
        },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 3: CREDENTIAL THEFT DETECTOR
// MITRE ATT&CK: TA0006
// Sources: mimikatz, LaZagne, CredMaster, TREVORspray
// ║════════════════���═════════════════════════════════════════════════════════════════════

/// Detect credential theft patterns
pub fn detect_credential_theft(event: &KalpixkEvent) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = event.raw.to_lowercase();
    let user = event.user.as_deref().map(|s| s.to_lowercase()).unwrap_or_default();
    
    // Password spraying (multiple failed auths)
    if user.contains("admin") || user.contains("root") {
        if raw.contains("failed") || raw.contains("invalid") {
            score += 0.4;
            techniques.push("T1110".to_string()); // Brute Force
        }
    }
    
    // LSASS access attempt (mimikatz)
    if raw.contains("lsass") || raw.contains("lsass.exe") {
        score += 0.9;
        techniques.push("T1003".to_string()); // OS Credential Dumping
    }
    
    // SAM database access
    if raw.contains("sam") && (raw.contains("dump") || raw.contains("read")) {
        score += 0.8;
        techniques.push("T1003".to_string());
    }
    
    // Credential dumping tool signatures
    if raw.contains("mimikatz") || raw.contains("lazagne") || raw.contains("procdump") {
        score += 0.9;
        techniques.push("T1003".to_string());
    }
    
    // GitHub secret exposure
    if raw.contains("github") && (raw.contains("api_key") || raw.contains("token")) {
        score += 0.5;
        techniques.push("T1552".to_string()); // Unsecured Credentials
    }
    
    // Memory dump attempt
    if raw.contains("minidump") || raw.contains("process_dump") {
        score += 0.7;
        techniques.push("T1003".to_string());
    }
    
    NodeResult {
        node: "NODE-3: CREDS".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 {
            format!("Credential theft detected (score: {:.2})", score)
        } else {
            "No credential theft detected".to_string()
        },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// NODE 4: PAYLOAD/EXECUTION DETECTOR
// MITRE ATT&CK: TA0002
// Sources: msfvenom, Shellter, Donut, macro_pack, Chimera
// ═══════════════════════════════════════════════════════════════════════════════════════

/// Detect payload execution patterns
pub fn detect_payload_execution(event: &KalpixkEvent) -> NodeResult {
    let mut score = 0.0;
    let mut techniques = Vec::new();
    let raw = event.raw.to_lowercase();
    let metadata = &event.metadata;
    
    // PowerShell encoded command
    if raw.contains("encodedcommand") || raw.contains("-enc ") || raw.contains("encoded") {
        score += 0.4;
        techniques.push("T1059".to_string()); // Command and Scripting Interpreter
    }
    
    // PowerShell download cradle
    if raw.contains("downloadstring") || raw.contains("iex") || raw.contains("invoke-expression") {
        score += 0.5;
        techniques.push("T1059".to_string());
    }
    
    // In-memory assembly (Donut)
    if raw.contains("assembly") && raw.contains("load") {
        score += 0.6;
        techniques.push("T1620".to_string()); // Reflective Code Loading
    }
    
    // Obfuscated PowerShell
    let entropy_score = raw.chars()
        .filter(|c| !c.is_ascii_alphanumeric() && !c.is_whitespace())
        .count() as f64 / raw.len().max(1) as f64;
    if entropy_score > 0.3 {
        score += 0.3;
        techniques.push("T1027".to_string()); // Obfuscated Files
    }
    
    // VBA macro execution
    if raw.contains("vba") && (raw.contains("macro") || raw.contains("automation")) {
        score += 0.5;
        techniques.push("T1059".to_string());
    }
    
    // Shellcode injection
    if raw.contains("shellcode") || raw.contains("virtualalloc") {
        score += 0.7;
        techniques.push("T1055".to_string()); // Process Injection
    }
    
    // WMI event subscription
    if raw.contains("wmi") && (raw.contains("consumer") || raw.contains("filter")) {
        score += 0.6;
        techniques.push("T1047".to_string()); // Windows Management Instrumentation
    }
    
    // Service creation
    if raw.contains("create") && raw.contains("service") {
        score += 0.4;
        techniques.push("T1543".to_string()); // Create Service
    }
    
    NodeResult {
        node: "NODE-4: PAYLOAD".to_string(),
        score,
        level: SeverityScore::new(score).as_level(),
        mitre_techniques: techniques,
        description: if score > 0.0 {
            format!("Payload execution detected (score: {:.2})", score)
        } else {
            "No payload execution detected".to_string()
        },
    }
}

// ═══════════════════════════════════════════════════════════════════════════════════════
// COMPLETE ANALYSIS — Run all 4 nodes
// ═══════════════════════════════════════════════════════════════════════════════════════

/// Run all 4 defense nodes on an event
pub fn analyze_all_nodes(event: &KalpixkEvent) -> Vec<NodeResult> {
    vec![
        detect_reconnaissance(event),
        detect_lateral_movement(event),
        detect_credential_theft(event),
        detect_payload_execution(event),
    ]
}

/// Get the highest severity from all nodes
pub fn get_max_severity(event: &KalpixkEvent) -> NodeResult {
    let results = analyze_all_nodes(event);
    let max = results.iter().max_by(|a, b| a.score.partial_cmp(&b.score).unwrap()).unwrap();
    max.clone()
}

/// Check if WASM_LOCKDOWN should be triggered
pub fn should_lockdown(event: &KalpixkEvent) -> bool {
    get_max_severity(event).score >= 0.7
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::{EventType, KalpixkEvent};
    use std::collections::HashMap;
    
    fn create_test_event(raw: &str) -> KalpixkEvent {
        KalpixkEvent {
            timestamp_ms: 0,
            event_type: EventType::Unknown,
            local_severity: 0.0,
            source: "192.168.1.100".to_string(),
            destination: None,
            user: None,
            process: None,
            metadata: HashMap::new(),
            raw: raw.to_string(),
            source_type: "test".to_string(),
            fingerprint: "test".to_string(),
        }
    }
    
    #[test]
    fn test_recon_detection() {
        let event = create_test_event("DNS enumeration detected from attacker");
        let result = detect_reconnaissance(&event);
        assert!(result.score > 0.0);
    }
    
    #[test]
    fn test_lateral_movement() {
        let event = create_test_event("SMB connection from 192.168.1.50 via port 445");
        let result = detect_lateral_movement(&event);
        assert!(result.score > 0.0);
    }
    
    #[test]
    fn test_credential_theft() {
        let event = create_test_event("mimikatz lsass.exe access attempt");
        let result = detect_credential_theft(&event);
        assert!(result.score >= 0.7); // High score for mimikatz
    }
    
    #[test]
    fn test_payload_execution() {
        let event = create_test_event("PowerShell -EncodedCommand base64payload");
        let result = detect_payload_execution(&event);
        assert!(result.score > 0.0);
    }
    
    #[test]
    fn test_lockdown_trigger() {
        let event = create_test_event("mimikatz lsass.exe");
        assert!(should_lockdown(&event));
    }
}
