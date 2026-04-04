//! Extracción de features para el modelo de detección AMD ROCm
//!
//! Produce un vector de 32 features numéricas normalizadas [0.0, 1.0]
//! compatible con los modelos IsolationForest y Autoencoder entrenados en Python.

use crate::event::{EventType, KalpixkEvent, EventFeatures, UebaSessionFeatures};

/// Número de features en el vector (CONTRATO con el modelo Python — no cambiar sin re-entrenar)
pub const FEATURE_DIM: usize = 32;

/// Nombres de las 32 features (para interpretabilidad)
pub const FEATURE_NAMES: &[&str; FEATURE_DIM] = &[
    "event_type_encoded",     // 0: tipo de evento normalizado
    "local_severity",         // 1: severidad calculada por heurísticas
    "hour_of_day",            // 2: hora del día normalizada [0,1]
    "day_of_week",            // 3: día de semana normalizado [0,1]
    "is_weekend",             // 4: 1.0 si fin de semana
    "is_off_hours",           // 5: 1.0 si fuera de horario laboral (8am-6pm)
    "source_is_internal",     // 6: 1.0 si IP interna (10.x / 192.168.x / 172.16.x)
    "destination_exists",     // 7: 1.0 si hay destino
    "has_user",               // 8: 1.0 si hay usuario
    "source_entropy",         // 9: entropía del string de source [0,1]
    "user_entropy",           // 10: entropía del username [0,1]
    "metadata_field_count",   // 11: número de campos en metadata normalizado
    "is_privileged_port",     // 12: puerto destino < 1024
    "dst_port_normalized",    // 13: puerto destino / 65535
    "bytes_log10_normalized", // 14: log10(bytes) / 10
    "has_db_keyword",         // 15: contiene keyword SQL
    "has_destructive_op",     // 16: DROP/TRUNCATE/DELETE
    "is_sensitive_table",     // 17: tabla sensible WMS
    "has_bulk_operation",     // 18: IMPORT/EXPORT/LOAD
    "has_network_scan_sig",   // 19: firma de escaneo de red
    "is_privileged_account",  // 20: root/admin/administrator
    "process_is_known",       // 21: proceso en lista de confianza
    "has_lateral_movement",   // 22: indicador de movimiento lateral
    "source_is_cloud",        // 23: origen desde IP cloud conocida
    "raw_length_normalized",  // 24: longitud del log normalizada
    "has_base64_payload",     // 25: indicador de payload base64
    "has_powershell_sig",     // 26: firma PowerShell
    "windows_event_risk",     // 27: riesgo del Event ID de Windows
    "db2_operation_risk",     // 28: riesgo de la operación DB2
    "netflow_risk",           // 29: riesgo del flujo de red
    "composite_risk_1",       // 30: (severity * is_off_hours)
    "composite_risk_2",       // 31: (has_destructive_op * has_user)
];

/// Extraer vector de features de un evento normalizado
pub fn extract(event: &KalpixkEvent) -> Vec<f64> {
    let mut f = vec![0.0f64; FEATURE_DIM];
    
    // F0: tipo de evento como número normalizado
    f[0] = encode_event_type(&event.event_type);
    
    // F1: severidad local
    f[1] = event.local_severity.clamp(0.0, 1.0);
    
    // F2-F5: temporales (usando timestamp actual como proxy)
    let now = chrono::DateTime::from_timestamp_millis(event.timestamp_ms)
        .unwrap_or_else(chrono::Utc::now);
    f[2] = now.hour() as f64 / 23.0;
    f[3] = now.weekday().num_days_from_monday() as f64 / 6.0;
    f[4] = if now.weekday().num_days_from_monday() >= 5 { 1.0 } else { 0.0 };
    let hour = now.hour();
    f[5] = if hour < 8 || hour >= 18 { 1.0 } else { 0.0 };
    
    // F6: IP interna
    f[6] = if is_internal_ip(&event.source) { 1.0 } else { 0.0 };
    
    // F7: tiene destino
    f[7] = if event.destination.is_some() { 1.0 } else { 0.0 };
    
    // F8: tiene usuario
    f[8] = if event.user.is_some() { 1.0 } else { 0.0 };
    
    // F9-F10: entropías
    f[9] = string_entropy(&event.source).min(1.0);
    f[10] = event.user.as_deref().map(|u| string_entropy(u)).unwrap_or(0.0).min(1.0);
    
    // F11: número de campos metadata
    f[11] = (event.metadata.len() as f64 / 20.0).min(1.0);
    
    // F12-F13: puertos (desde metadata)
    if let Some(port) = get_metadata_u64(event, "dst_port") {
        f[12] = if port < 1024 { 1.0 } else { 0.0 };
        f[13] = port as f64 / 65535.0;
    }
    
    // F14: bytes (transferencia)
    if let Some(bytes) = get_metadata_u64(event, "bytes")
        .or(get_metadata_u64(event, "large_transfer_bytes")) 
    {
        f[14] = if bytes > 0 { (bytes as f64).log10() / 10.0 } else { 0.0 };
    }
    
    // F15-F19: DB features
    let raw_lower = event.raw.to_lowercase();
    f[15] = if has_sql_keyword(&raw_lower) { 1.0 } else { 0.0 };
    f[16] = if has_destructive_op(&raw_lower) { 1.0 } else { 0.0 };
    f[17] = if get_metadata_bool(event, "sensitive_table") { 1.0 } else { 0.0 };
    f[18] = if get_metadata_bool(event, "bulk_data_operation") { 1.0 } else { 0.0 };
    
    // F19: firma de escaneo
    f[19] = if event.event_type == EventType::NetworkScan { 1.0 } else { 0.0 };
    
    // F20: cuenta privilegiada
    f[20] = if is_privileged_account(event.user.as_deref()) { 1.0 } else { 0.0 };
    
    // F21: proceso conocido/confiable
    f[21] = if is_known_process(event.process.as_deref()) { 1.0 } else { 0.0 };
    
    // F22: movimiento lateral (heurística: destino interno diferente al origen)
    f[22] = if has_lateral_movement_sig(event) { 1.0 } else { 0.0 };
    
    // F23: IP cloud conocida
    f[23] = if is_cloud_ip(&event.source) { 1.0 } else { 0.0 };
    
    // F24: longitud del log
    f[24] = (event.raw.len() as f64 / 5000.0).min(1.0);
    
    // F25: indicador base64
    f[25] = if has_base64_pattern(&event.raw) { 1.0 } else { 0.0 };
    
    // F26: firma PowerShell
    f[26] = if has_powershell_signature(&raw_lower) { 1.0 } else { 0.0 };
    
    // F27: riesgo Event ID Windows
    f[27] = get_windows_event_risk(event);
    
    // F28: riesgo operación DB2
    f[28] = get_db2_operation_risk(&raw_lower);
    
    // F29: riesgo netflow
    f[29] = if event.source_type == "netflow" { f[13] * f[14] } else { 0.0 };
    
    // F30-F31: features compuestas (interacciones)
    f[30] = f[1] * f[5];   // severity × off_hours
    f[31] = f[16] * f[8];  // destructive × has_user
    
    f
}

/// Calcular features UEBA de una sesión completa de usuario
pub fn compute_ueba_session(events: &[KalpixkEvent]) -> UebaSessionFeatures {
    if events.is_empty() {
        return UebaSessionFeatures::default();
    }

    let user = events[0].user.clone().unwrap_or_else(|| "unknown".to_string());
    
    let timestamps: Vec<i64> = events.iter().map(|e| e.timestamp_ms).collect();
    let min_ts = *timestamps.iter().min().unwrap_or(&0);
    let max_ts = *timestamps.iter().max().unwrap_or(&0);
    let session_duration_ms = max_ts - min_ts;
    
    let total = events.len();
    let failed_auth = events.iter().filter(|e| e.event_type == EventType::LoginFailure).count();
    let off_hours_count = events.iter().filter(|e| {
        let hour = chrono::DateTime::from_timestamp_millis(e.timestamp_ms)
            .map(|dt| dt.hour())
            .unwrap_or(12);
        hour < 8 || hour >= 18
    }).count();
    
    let unique_sources: std::collections::HashSet<&str> = events.iter()
        .map(|e| e.source.as_str()).collect();
    let unique_dests: std::collections::HashSet<&str> = events.iter()
        .filter_map(|e| e.destination.as_deref()).collect();

    let db_queries = events.iter().filter(|e| 
        e.event_type == EventType::DbQuery || e.event_type == EventType::DbAnomalousQuery
    ).count();
    
    let priv_esc = events.iter().filter(|e| 
        e.event_type == EventType::PrivilegeEscalation
    ).count();

    let feature_vector = vec![
        session_duration_ms as f64 / 86_400_000.0,  // Normalizado a 24h
        total as f64 / 1000.0,
        unique_sources.len() as f64 / 50.0,
        if total > 0 { failed_auth as f64 / total as f64 } else { 0.0 },
        if total > 0 { off_hours_count as f64 / total as f64 } else { 0.0 },
        unique_dests.len() as f64 / 100.0,
        priv_esc as f64 / 10.0,
        db_queries as f64 / 1000.0,
    ];

    UebaSessionFeatures {
        user,
        session_duration_ms,
        event_count: total,
        unique_resources: unique_sources.len(),
        failed_auth_ratio: if total > 0 { failed_auth as f64 / total as f64 } else { 0.0 },
        off_hours_ratio: if total > 0 { off_hours_count as f64 / total as f64 } else { 0.0 },
        data_transfer_bytes: 0, // TODO: sumar desde metadata
        unique_destinations: unique_dests.len(),
        privilege_escalation_attempts: priv_esc,
        db_query_volume: db_queries,
        db_unusual_tables: 0, // TODO: implementar baseline de tablas
        lateral_movement_score: if unique_dests.len() > 5 { 0.7 } else { 0.1 },
        feature_vector,
    }
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
        || ip.starts_with("172.17.")
        || ip.starts_with("172.31.")
        || ip == "localhost"
        || ip == "127.0.0.1"
}

fn is_cloud_ip(ip: &str) -> bool {
    // Rangos conocidos de AWS, Azure, GCP (simplificado)
    ip.starts_with("54.") || ip.starts_with("52.") || ip.starts_with("34.")
}

fn string_entropy(s: &str) -> f64 {
    if s.is_empty() { return 0.0; }
    let mut freq = [0u32; 256];
    for b in s.bytes() { freq[b as usize] += 1; }
    let len = s.len() as f64;
    -freq.iter()
        .filter(|&&c| c > 0)
        .map(|&c| { let p = c as f64 / len; p * p.log2() })
        .sum::<f64>() / 8.0  // Normalizar a [0,1]
}

fn has_sql_keyword(lower: &str) -> bool {
    lower.contains("select") || lower.contains("insert") 
        || lower.contains("update") || lower.contains("delete")
}

fn has_destructive_op(lower: &str) -> bool {
    lower.contains("drop ") || lower.contains("truncate ") 
        || lower.contains("delete from") || lower.contains("format ")
}

fn is_privileged_account(user: Option<&str>) -> bool {
    match user {
        Some(u) => {
            let u = u.to_lowercase();
            u == "root" || u == "admin" || u == "administrator" 
                || u == "system" || u.contains("service") || u.contains("svc")
        }
        None => false,
    }
}

fn is_known_process(process: Option<&str>) -> bool {
    let safe_processes = [
        "sshd", "cron", "systemd", "init", "bash", "sh", "sudo",
        "db2sysc", "db2agent", "java", "python3",
    ];
    match process {
        Some(p) => safe_processes.iter().any(|&sp| p.contains(sp)),
        None => false,
    }
}

fn has_lateral_movement_sig(event: &KalpixkEvent) -> bool {
    if let Some(dest) = &event.destination {
        is_internal_ip(&event.source) 
            && is_internal_ip(dest) 
            && event.source != *dest
    } else {
        false
    }
}

fn has_base64_pattern(raw: &str) -> bool {
    // Buscar secuencias base64 largas (potencial payload)
    let b64_chars: std::collections::HashSet<char> = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=".chars().collect();
    let mut consecutive = 0usize;
    let mut max_consecutive = 0usize;
    for c in raw.chars() {
        if b64_chars.contains(&c) {
            consecutive += 1;
            max_consecutive = max_consecutive.max(consecutive);
        } else {
            consecutive = 0;
        }
    }
    max_consecutive > 60  // Secuencia b64 >60 chars es sospechosa
}

fn has_powershell_signature(lower: &str) -> bool {
    lower.contains("powershell") || lower.contains("-encodedcommand") 
        || lower.contains("-nop") || lower.contains("-windowstyle hidden")
        || lower.contains("invoke-expression") || lower.contains("iex ")
}

fn get_windows_event_risk(event: &KalpixkEvent) -> f64 {
    let event_id = event.metadata.get("windows_event_id")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);
    
    match event_id {
        4625 => 0.50, // Login fallido
        4648 => 0.60, // Logon con creds explícitas
        4672 => 0.80, // Admin logon
        4698 | 4699 | 4700 => 0.85, // Scheduled task
        4720 => 0.70, // User creado
        4726 => 0.75, // User eliminado
        7045 => 0.90, // Servicio instalado
        _ => 0.20,
    }
}

fn get_db2_operation_risk(lower: &str) -> f64 {
    if lower.contains("drop") || lower.contains("truncate") { return 0.90; }
    if lower.contains("grant") || lower.contains("revoke") { return 0.80; }
    if lower.contains("create user") { return 0.85; }
    if lower.contains("export") || lower.contains("import") { return 0.70; }
    if lower.contains("delete") { return 0.60; }
    0.15
}

fn get_metadata_u64(event: &KalpixkEvent, key: &str) -> Option<u64> {
    event.metadata.get(key)?.as_u64()
}

fn get_metadata_bool(event: &KalpixkEvent, key: &str) -> bool {
    event.metadata.get(key)
        .and_then(|v| v.as_bool())
        .unwrap_or(false)
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

use crate::event::UebaSessionFeatures;
use chrono::{Datelike, Timelike};
