//! features.rs — Extracción de 32 features para el modelo AMD MI300X
//!
//! ATLATL-ORDNANCE: Vincula la extracción con los nodos de defensa ofensiva.

use crate::event::{EventType, KalpixkEvent, UebaSessionFeatures};
use chrono::Timelike;

pub const FEATURE_DIM: usize = 32;
pub const FEATURE_NAMES: &[&str] = &[
    "event_type_encoded",
    "local_severity",
    "is_internal_source",
    "is_cloud_source",
    "has_user",
    "is_off_hours",
    "has_destination",
    "is_lateral_potential",
    "raw_length_norm",
    "shannon_entropy",
    "failed_auth_flag",
    "privileged_user_flag",
    "known_process_flag",
    "dst_port_risk",
    "bytes_transfer_norm",
    "sql_keyword_flag",
    "destructive_op_flag",
    "base64_pattern_flag",
    "powershell_sig_flag",
    "windows_event_risk",
    "db2_op_risk",
    "netflow_risk",
    "recon_node_score",
    "lateral_node_score",
    "credential_node_score",
    "payload_node_score",
    "combined_offense_score",
    "threat_density",
    "user_risk_historical",
    "source_reputation",
    "comp_severity_offhours",
    "comp_destructive_user",
];

/// Extrae el vector de 32 features desde un evento
pub fn extract(event: &KalpixkEvent) -> Vec<f64> {
    let mut f = vec![0.0; FEATURE_DIM];
    let raw_lower = event.raw.to_lowercase();

    // F0-F7: Features básicas
    f[0] = encode_event_type(&event.event_type);
    f[1] = event.local_severity;
    f[2] = if is_internal_ip(&event.source) {
        1.0
    } else {
        0.0
    };
    f[3] = if is_cloud_ip(&event.source) { 1.0 } else { 0.0 };
    f[4] = if event.user.is_some() { 1.0 } else { 0.0 };

    let hour = chrono::Utc::now().hour();
    f[5] = if !(8..18).contains(&hour) { 1.0 } else { 0.0 };
    f[6] = if event.destination.is_some() {
        1.0
    } else {
        0.0
    };
    f[7] = if has_lateral_movement_sig(event) {
        1.0
    } else {
        0.0
    };

    // F8-F15: Features de contenido y red
    f[8] = (event.raw.len() as f64 / 1000.0).min(1.0);
    f[9] = string_entropy(&event.raw);
    f[10] = if event.event_type == EventType::LoginFailure {
        1.0
    } else {
        0.0
    };
    f[11] = if is_privileged_account(event.user.as_deref()) {
        1.0
    } else {
        0.0
    };
    f[12] = if is_known_process(event.process.as_deref()) {
        1.0
    } else {
        0.0
    };

    let dst_port = event
        .metadata
        .get("dst_port")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);
    f[13] = if [22, 3389, 445].contains(&dst_port) {
        0.8
    } else {
        0.1
    };

    let bytes = event
        .metadata
        .get("bytes")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);
    f[14] = (bytes as f64 / 1_000_000.0).min(1.0);
    f[15] = if has_sql_keyword(&raw_lower) {
        1.0
    } else {
        0.0
    };

    // F16-F21: Riesgos específicos
    f[16] = if has_destructive_op(&raw_lower) {
        1.0
    } else {
        0.0
    };
    f[17] = if has_base64_pattern(&event.raw) {
        1.0
    } else {
        0.0
    };
    f[18] = if has_powershell_signature(&raw_lower) {
        1.0
    } else {
        0.0
    };
    f[19] = get_windows_event_risk(event);
    f[20] = get_db2_operation_risk(&raw_lower);
    f[21] = if event.source_type == "netflow" {
        f[13] * f[14]
    } else {
        0.0
    };

    // F22-F26: [ATLATL-ORDNANCE] Offensive Node Scores
    // Prepara las versiones lowercase una sola vez para los 4 nodos
    let raw_lower_dn = event.raw.to_lowercase();
    let user_lower_dn = event.user.as_deref().unwrap_or("").to_lowercase();
    let src_lower_dn = event.source.as_deref().unwrap_or("").to_lowercase();
    f[22] = crate::defense_nodes::detect_reconnaissance(
        event,
        &raw_lower_dn,
        &user_lower_dn,
        &src_lower_dn,
    )
    .score;
    f[23] = crate::defense_nodes::detect_lateral_movement(
        event,
        &raw_lower_dn,
        &user_lower_dn,
        &src_lower_dn,
    )
    .score;
    f[24] = crate::defense_nodes::detect_credential_theft(
        event,
        &raw_lower_dn,
        &user_lower_dn,
        &src_lower_dn,
    )
    .score;
    f[25] = crate::defense_nodes::detect_payload_execution(
        event,
        &raw_lower_dn,
        &user_lower_dn,
        &src_lower_dn,
    )
    .score;
    f[26] = (f[22] + f[23] + f[24] + f[25]) / 4.0;

    // F27-F31: Features avanzadas
    f[27] = f[9] * f[8]; // Densidad de entropía
    f[28] = 0.0; // Placeholder para historial
    f[29] = if f[3] > 0.5 { 0.8 } else { 0.2 };
    f[30] = f[1] * f[5]; // Severidad x fuera de horario
    f[31] = f[16] * f[4]; // Operación destructiva x usuario identificado

    f
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

fn encode_event_type(et: &EventType) -> f64 {
    match et {
        EventType::LoginSuccess => 0.05,
        EventType::LoginFailure => 0.35,
        EventType::LoginBruteForce => 0.85,
        EventType::FileAccess => 0.10,
        EventType::FileModification => 0.40,
        EventType::FileDeletion => 0.65,
        EventType::NetworkConnection => 0.20,
        EventType::NetworkScan => 0.75,
        EventType::ProcessExecution => 0.30,
        EventType::PrivilegeEscalation => 0.90,
        EventType::ServiceChange => 0.45,
        EventType::DbQuery => 0.15,
        EventType::DbAnomalousQuery => 0.80,
        EventType::UserCreation | EventType::UserDeletion => 0.70,
        EventType::PolicyChange => 0.75,
        EventType::Unknown => 0.50,
    }
}

fn is_internal_ip(ip: &str) -> bool {
    ip.starts_with("10.")
        || ip.starts_with("192.168.")
        || ip.starts_with("172.16.")
        || ip == "localhost"
        || ip == "127.0.0.1"
}

fn is_cloud_ip(ip: &str) -> bool {
    ip.starts_with("54.") || ip.starts_with("52.") || ip.starts_with("34.")
}

pub fn string_entropy(s: &str) -> f64 {
    if s.is_empty() {
        return 0.0;
    }
    let mut freq = [0u32; 256];
    for b in s.bytes() {
        freq[b as usize] += 1;
    }
    let len = s.len() as f64;
    -freq
        .iter()
        .filter(|&&c| c > 0)
        .map(|&c| {
            let p = c as f64 / len;
            p * p.log2()
        })
        .sum::<f64>()
        / 8.0
}

fn has_sql_keyword(lower: &str) -> bool {
    lower.contains("select")
        || lower.contains("insert")
        || lower.contains("update")
        || lower.contains("delete")
}

fn has_destructive_op(lower: &str) -> bool {
    lower.contains("drop ") || lower.contains("truncate ") || lower.contains("delete from")
}

fn is_privileged_account(user: Option<&str>) -> bool {
    match user {
        Some(u) => {
            let u = u.to_lowercase();
            u == "root" || u == "admin" || u == "administrator" || u == "system"
        }
        None => false,
    }
}

fn is_known_process(process: Option<&str>) -> bool {
    let safe = ["sshd", "cron", "systemd", "db2sysc", "bash", "python3"];
    match process {
        Some(p) => safe.iter().any(|&s| p.contains(s)),
        None => false,
    }
}

fn has_lateral_movement_sig(event: &KalpixkEvent) -> bool {
    if let Some(dest) = &event.destination {
        is_internal_ip(&event.source) && is_internal_ip(dest) && event.source != *dest
    } else {
        false
    }
}

fn has_base64_pattern(raw: &str) -> bool {
    let b64_chars: std::collections::HashSet<char> =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
            .chars()
            .collect();
    let mut max_consecutive = 0;
    let mut current = 0;
    for c in raw.chars() {
        if b64_chars.contains(&c) {
            current += 1;
        } else {
            current = 0;
        }
        max_consecutive = max_consecutive.max(current);
    }
    max_consecutive > 60
}

fn has_powershell_signature(lower: &str) -> bool {
    lower.contains("powershell")
        || lower.contains("-encodedcommand")
        || lower.contains("invoke-expression")
}

fn get_windows_event_risk(event: &KalpixkEvent) -> f64 {
    let id = event
        .metadata
        .get("windows_event_id")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);

    match id {
        4625 => 0.50,        // Login fallido
        4648 => 0.60,        // Logon con creds explícitas
        4672 => 0.80,        // Admin logon
        4698..=4700 => 0.85, // Scheduled task
        4720 => 0.70,        // User creado
        4726 => 0.75,        // User eliminado
        7045 => 0.90,        // Servicio instalado
        _ => 0.20,
    }
}

fn get_db2_operation_risk(lower: &str) -> f64 {
    if lower.contains("drop") {
        0.9
    } else if lower.contains("grant") {
        0.8
    } else {
        0.15
    }
}

impl Default for UebaSessionFeatures {
    fn default() -> Self {
        UebaSessionFeatures {
            user: "unknown".to_string(),
            session_duration_ms: 0,
            event_count: 0,
            unique_resources: 0,
            failed_auth_ratio: 0.0,
            off_hours_ratio: 0.0,
            data_transfer_bytes: 0,
            unique_destinations: 0,
            privilege_escalation_attempts: 0,
            db_query_volume: 0,
            db_unusual_tables: 0,
            lateral_movement_score: 0.0,
            feature_vector: vec![0.0; 8],
        }
    }
}
