//! defense_nodes.rs — Los 4 nodos de defensa ofensiva WASM
//!
//! Implementación estructural basada en RedTeam-Tools.
//! ATLATL-ORDNANCE: Si el atacante entra, su infraestructura muere.

use crate::event::KalpixkEvent;
use crate::severity::OffenseLevel;

/// NODE-1: Reconnaissance Detector (T1595)
/// Detecta escaneos activos y herramientas de OSINT.
pub fn detect_recon(event: &KalpixkEvent) -> f64 {
    let mut score: f64 = 0.0;
    let lower = event.raw.to_lowercase();

    // Firmas de herramientas comunes
    let tools = [
        "nmap",
        "nuclei",
        "gobuster",
        "feroxbuster",
        "shodan",
        "dnsrecon",
        "enum4linux",
    ];
    for tool in &tools {
        if lower.contains(tool) {
            score += 0.50;
        }
    }

    // Burst de peticiones (simulado por metadata si el parser lo detecta)
    if let Some(burst) = event
        .metadata
        .get("dns_queries_per_second")
        .and_then(|v| v.as_f64())
    {
        if burst > 50.0 {
            score += 0.30;
        }
    }

    if let Some(ports) = event.metadata.get("ports_probed").and_then(|v| v.as_u64()) {
        if ports > 100 {
            score += 0.40;
        }
    }

    score.min(1.0)
}

/// NODE-2: Lateral Movement Detector (T1021)
/// Detecta movimientos laterales vía WinRM, SMB, Kerberos.
pub fn detect_lateral_movement(event: &KalpixkEvent) -> f64 {
    let mut score: f64 = 0.0;
    let lower = event.raw.to_lowercase();

    // Protocolos y herramientas de relay
    if lower.contains("evil-winrm") || lower.contains("impacket") || lower.contains("responder") {
        score += 0.70;
    }

    if let Some(port) = event.metadata.get("dst_port").and_then(|v| v.as_u64()) {
        if port == 5985 || port == 5986 {
            score += 0.40;
        } // WinRM
        if port == 445 || port == 139 {
            score += 0.30;
        } // SMB
    }

    if event.metadata.contains_key("kerberos_anomaly") {
        score += 0.80;
    }

    score.min(1.0)
}

/// NODE-3: Credential Theft Detector (T1003)
/// Detecta dumping de LSASS, Password Spraying, Secret Exposure.
pub fn detect_credential_theft(event: &KalpixkEvent) -> f64 {
    let mut score: f64 = 0.0;
    let lower = event.raw.to_lowercase();

    if lower.contains("mimikatz") || lower.contains("secretsdump") || lower.contains("rubeus") {
        score += 0.90;
    }

    if let Some(failed_ratio) = event
        .metadata
        .get("failed_auth_ratio")
        .and_then(|v| v.as_f64())
    {
        if failed_ratio > 0.8 {
            score += 0.60;
        }
    }

    if event.metadata.contains_key("lsass_memory_access") {
        score += 0.95;
    }

    score.min(1.0)
}

/// NODE-4: Payload/Execution Detector (T1587)
/// Detecta generación de shellcode, ofuscación y ejecución en memoria.
pub fn detect_payload_execution(event: &KalpixkEvent) -> f64 {
    let mut score: f64 = 0.0;
    let lower = event.raw.to_lowercase();

    if lower.contains("msfvenom")
        || lower.contains("donut")
        || lower.contains("shellter")
        || lower.contains("freeze")
    {
        score += 0.90;
    }

    // Ofuscación PowerShell (basado en entropía de la línea raw)
    let entropy = crate::features::string_entropy(&event.raw);
    if entropy > 0.7 && lower.contains("powershell") {
        score += 0.60;
    }

    if event.metadata.contains_key("in_memory_assembly_load") {
        score += 0.85;
    }

    score.min(1.0)
}

/// Orquesta la evaluación de todos los nodos y retorna el nivel ofensivo
pub fn evaluate_offense_level(event: &KalpixkEvent) -> (OffenseLevel, f64, &'static str) {
    let recon = detect_recon(event);
    let lateral = detect_lateral_movement(event);
    let creds = detect_credential_theft(event);
    let payload = detect_payload_execution(event);

    let scores = [
        (recon, "recon"),
        (lateral, "lateral"),
        (creds, "credential"),
        (payload, "payload"),
    ];

    let (max_score, node) = scores
        .iter()
        .max_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal))
        .cloned()
        .unwrap_or((0.0, "unknown"));

    (OffenseLevel::from(max_score), max_score, node)
}
