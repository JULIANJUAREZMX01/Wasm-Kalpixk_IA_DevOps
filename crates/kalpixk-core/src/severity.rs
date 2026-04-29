#![allow(dead_code)]
//! severity.rs — Niveles de escalación ofensiva y mapeo de RedTeam
//!
//! ATLATL-ORDNANCE: Define la respuesta táctica basada en el riesgo.

use serde::{Deserialize, Serialize};

/// Niveles de respuesta ofensiva de Kalpixk
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, PartialOrd)]
pub enum OffenseLevel {
    /// 0.0 - 0.29: Tráfico normal. Solo registro.
    Clean = 0,
    /// 0.30 - 0.49: Actividad inusual. Alerta y limitación de tasa.
    Suspicious = 1,
    /// 0.50 - 0.69: Patrón de ataque confirmado. Bloqueo inmediato.
    Anomaly = 2,
    /// 0.70 - 0.89: Intento de compromiso grave. Inicio de contramedidas.
    Critical = 3,
    /// 0.90 - 1.0: Exfiltración o Ransomware detectado. Exterminio de infraestructura.
    Exterminio = 4,
}

impl From<f64> for OffenseLevel {
    fn from(score: f64) -> Self {
        if score >= 0.90 {
            OffenseLevel::Exterminio
        } else if score >= 0.70 {
            OffenseLevel::Critical
        } else if score >= 0.50 {
            OffenseLevel::Anomaly
        } else if score >= 0.30 {
            OffenseLevel::Suspicious
        } else {
            OffenseLevel::Clean
        }
    }
}

/// Mapeo de herramientas de RedTeam a técnicas MITRE ATT&CK
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RedTeamMapping {
    pub tool_name: String,
    pub mitre_id: String,
    pub description: String,
    pub recommended_retaliation: RetaliationType,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RetaliationType {
    None,
    RateLimit,
    Block,
    PoisonPointers,
    GarbageInjection,
    RecursiveZipBomb,
    C2Corruption,
    V5Strike,
}

pub fn get_redteam_mapping(raw_log: &str) -> Option<RedTeamMapping> {
    let lower = raw_log.to_lowercase();

    // NODE-1: Recon
    if lower.contains("nmap") || lower.contains("nuclei") || lower.contains("gobuster") {
        return Some(RedTeamMapping {
            tool_name: "Scanner".to_string(),
            mitre_id: "T1595".to_string(),
            description: "Active Scanning detected".to_string(),
            recommended_retaliation: RetaliationType::GarbageInjection,
        });
    }

    // NODE-2: Lateral
    if lower.contains("evil-winrm") || lower.contains("impacket") || lower.contains("responder") {
        return Some(RedTeamMapping {
            tool_name: "LateralMovementTool".to_string(),
            mitre_id: "T1021".to_string(),
            description: "Remote Services / Relay attack".to_string(),
            recommended_retaliation: RetaliationType::PoisonPointers,
        });
    }

    // NODE-3: Credentials
    if lower.contains("mimikatz") || lower.contains("rubeus") || lower.contains("secretsdump") {
        return Some(RedTeamMapping {
            tool_name: "CredsStealer".to_string(),
            mitre_id: "T1003".to_string(),
            description: "OS Credential Dumping".to_string(),
            recommended_retaliation: RetaliationType::Block,
        });
    }

    // NODE-4: Payload
    if lower.contains("msfvenom") || lower.contains("donut") || lower.contains("shellter") {
        return Some(RedTeamMapping {
            tool_name: "PayloadGenerator".to_string(),
            mitre_id: "T1587".to_string(),
            description: "Malware payload execution".to_string(),
            recommended_retaliation: RetaliationType::RecursiveZipBomb,
        });
    }

    None
}
