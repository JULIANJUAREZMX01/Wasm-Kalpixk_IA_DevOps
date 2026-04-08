//! Parsers de logs — convierten texto crudo a KalpixkEvent
//!
//! Cada parser implementa el trait LogParser y se registra con su source_type.

use crate::event::{EventType, KalpixkEvent};
use std::collections::HashMap;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ParseError {
    #[error("Línea vacía o solo espacios")]
    EmptyLine,
    #[error("Formato desconocido: {0}")]
    UnknownFormat(String),
    #[error("Campo requerido faltante: {0}")]
    MissingField(String),
    #[error("Error de parsing: {0}")]
    ParseFailed(String),
}

/// Trait que deben implementar todos los parsers
pub trait LogParser: Send + Sync {
    fn parse(&self, raw: &str) -> Result<KalpixkEvent, ParseError>;
    fn source_type(&self) -> &'static str;
}

/// Factory: obtener parser por nombre de fuente
pub fn get_parser(source_type: &str) -> Option<Box<dyn LogParser>> {
    match source_type {
        "syslog" => Some(Box::new(SyslogParser::new())),
        "json" => Some(Box::new(JsonStructuredParser::new())),
        "windows" => Some(Box::new(WindowsEventParser::new())),
        "db2" => Some(Box::new(Db2AuditParser::new())),
        "netflow" => Some(Box::new(NetflowParser::new())),
        _ => None,
    }
}

// ─── Parser Syslog RFC 5424 / RFC 3164 ────────────────────────────────────────

pub struct SyslogParser;

impl Default for SyslogParser {
    fn default() -> Self {
        Self::new()
    }
}

impl SyslogParser {
    pub fn new() -> Self {
        SyslogParser
    }

    fn fingerprint(raw: &str) -> String {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let mut hasher = DefaultHasher::new();
        raw.hash(&mut hasher);
        format!("{:x}", hasher.finish())
    }
}

impl LogParser for SyslogParser {
    fn source_type(&self) -> &'static str {
        "syslog"
    }

    fn parse(&self, raw: &str) -> Result<KalpixkEvent, ParseError> {
        let raw = raw.trim();
        if raw.is_empty() {
            return Err(ParseError::EmptyLine);
        }

        let mut metadata = HashMap::new();
        let mut event_type = EventType::Unknown;
        let mut user: Option<String> = None;
        let mut process: Option<String> = None;
        let mut source = "unknown".to_string();
        let mut local_severity: f64 = 0.30_f64;

        // Detectar patrones comunes de syslog
        let lower = raw.to_lowercase();

        if lower.contains("failed password") || lower.contains("authentication failure") {
            event_type = EventType::LoginFailure;
            local_severity = 0.45_f64;

            if let Some(u) = extract_syslog_user(raw) {
                user = Some(u.clone());
                metadata.insert("auth_user".to_string(), serde_json::json!(u));
            }
            if let Some(ip) = extract_syslog_ip(raw) {
                source = ip.clone();
                metadata.insert("src_ip".to_string(), serde_json::json!(ip));
            }
        } else if lower.contains("accepted password") || lower.contains("accepted publickey") {
            event_type = EventType::LoginSuccess;
            local_severity = 0.15_f64;
            if let Some(u) = extract_syslog_user(raw) {
                user = Some(u);
            }
        } else if lower.contains("sudo") && lower.contains("command") {
            event_type = EventType::ProcessExecution;
            local_severity = 0.50_f64;
            metadata.insert("sudo_cmd".to_string(), serde_json::json!(raw));
        } else if lower.contains("useradd") || lower.contains("adduser") {
            event_type = EventType::UserCreation;
            local_severity = 0.70_f64;
        } else if lower.contains("userdel") || lower.contains("deluser") {
            event_type = EventType::UserDeletion;
            local_severity = 0.75_f64;
        } else if lower.contains("iptables") || lower.contains("ufw") {
            event_type = EventType::NetworkConnection;
            metadata.insert("firewall_event".to_string(), serde_json::json!(true));
        }

        // Extraer proceso del formato syslog: "hostname process[pid]: message"
        if let Some(proc_name) = extract_syslog_process(raw) {
            process = Some(proc_name.clone());
            metadata.insert("process".to_string(), serde_json::json!(proc_name));
        }

        // Extraer hostname
        if let Some(host) = extract_syslog_hostname(raw) {
            if source == "unknown" {
                source = host.clone();
            }
            metadata.insert("hostname".to_string(), serde_json::json!(host));
        }

        Ok(KalpixkEvent {
            timestamp_ms: chrono::Utc::now().timestamp_millis(),
            event_type,
            local_severity,
            source,
            destination: None,
            user,
            process,
            metadata,
            raw: raw.to_string(),
            source_type: "syslog".to_string(),
            fingerprint: Self::fingerprint(raw),
        })
    }
}

// ─── Parser JSON estructurado (Filebeat, Logstash, etc.) ──────────────────────

pub struct JsonStructuredParser;

impl Default for JsonStructuredParser {
    fn default() -> Self {
        Self::new()
    }
}

impl JsonStructuredParser {
    pub fn new() -> Self {
        JsonStructuredParser
    }
}

impl LogParser for JsonStructuredParser {
    fn source_type(&self) -> &'static str {
        "json"
    }

    fn parse(&self, raw: &str) -> Result<KalpixkEvent, ParseError> {
        let raw = raw.trim();
        if raw.is_empty() {
            return Err(ParseError::EmptyLine);
        }

        let value: serde_json::Value =
            serde_json::from_str(raw).map_err(|e| ParseError::ParseFailed(e.to_string()))?;

        let source = value
            .get("src_ip")
            .or(value.get("source"))
            .or(value.get("host"))
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string();

        let user = value
            .get("user")
            .or(value.get("username"))
            .and_then(|v| v.as_str())
            .map(String::from);

        let event_type_str = value
            .get("event_type")
            .or(value.get("action"))
            .and_then(|v| v.as_str())
            .unwrap_or("unknown");

        let event_type = match event_type_str {
            "login_success" | "authentication_success" => EventType::LoginSuccess,
            "login_failure" | "authentication_failure" => EventType::LoginFailure,
            "file_access" | "file_read" => EventType::FileAccess,
            "file_write" | "file_modify" => EventType::FileModification,
            "file_delete" => EventType::FileDeletion,
            "network_connection" | "connection" => EventType::NetworkConnection,
            "process_exec" | "process_start" => EventType::ProcessExecution,
            "db_query" | "sql_query" => EventType::DbQuery,
            _ => EventType::Unknown,
        };

        let local_severity = value
            .get("severity")
            .and_then(|v| v.as_f64())
            .unwrap_or(event_type.base_severity());

        let mut metadata: HashMap<String, serde_json::Value> = HashMap::new();
        if let Some(obj) = value.as_object() {
            for (k, v) in obj {
                metadata.insert(k.clone(), v.clone());
            }
        }

        Ok(KalpixkEvent {
            timestamp_ms: chrono::Utc::now().timestamp_millis(),
            event_type,
            local_severity,
            source,
            destination: value
                .get("dst_ip")
                .and_then(|v| v.as_str())
                .map(String::from),
            user,
            process: value
                .get("process")
                .and_then(|v| v.as_str())
                .map(String::from),
            metadata,
            raw: raw.to_string(),
            source_type: "json".to_string(),
            fingerprint: format!("{:x}", raw.len()), // Simplified
        })
    }
}

// ─── Parser Windows Event Log ─────────────────────────────────────────────────

pub struct WindowsEventParser;

impl Default for WindowsEventParser {
    fn default() -> Self {
        Self::new()
    }
}

impl WindowsEventParser {
    pub fn new() -> Self {
        WindowsEventParser
    }
}

impl LogParser for WindowsEventParser {
    fn source_type(&self) -> &'static str {
        "windows"
    }

    fn parse(&self, raw: &str) -> Result<KalpixkEvent, ParseError> {
        let raw = raw.trim();
        if raw.is_empty() {
            return Err(ParseError::EmptyLine);
        }

        let mut metadata = HashMap::new();
        let mut event_type = EventType::Unknown;
        let mut local_severity: f64 = 0.30_f64;
        let mut user: Option<String> = None;
        let mut source = "windows_host".to_string();

        // Windows Event IDs críticos para Blue Team
        let event_id = extract_windows_event_id(raw).unwrap_or(0);

        match event_id {
            4624 => {
                event_type = EventType::LoginSuccess;
                local_severity = 0.15;
            }
            4625 => {
                event_type = EventType::LoginFailure;
                local_severity = 0.50;
            }
            4634 => {
                event_type = EventType::LoginSuccess;
                local_severity = 0.10;
            } // Logoff
            4648 => {
                event_type = EventType::LoginSuccess;
                local_severity = 0.40;
            } // Logon con creds explícitas
            4672 => {
                event_type = EventType::PrivilegeEscalation;
                local_severity = 0.75;
            }
            4698 | 4699 | 4700 | 4702 => {
                // Scheduled task creada/modificada/habilitada
                event_type = EventType::ServiceChange;
                local_severity = 0.80_f64;
            }
            4720 => {
                event_type = EventType::UserCreation;
                local_severity = 0.70;
            }
            4726 => {
                event_type = EventType::UserDeletion;
                local_severity = 0.75;
            }
            4732 | 4733 => {
                // Usuario agregado/removido de grupo
                event_type = EventType::PolicyChange;
                local_severity = 0.65_f64;
            }
            4776 => {
                event_type = EventType::LoginFailure;
                local_severity = 0.60_f64;
                metadata.insert("dc_auth_failure".to_string(), serde_json::json!(true));
            }
            7045 => {
                // Nuevo servicio instalado
                event_type = EventType::ServiceChange;
                local_severity = 0.85_f64;
            }
            _ => {}
        }

        metadata.insert("windows_event_id".to_string(), serde_json::json!(event_id));

        if let Some(u) = extract_windows_user(raw) {
            user = Some(u.clone());
            metadata.insert("windows_user".to_string(), serde_json::json!(u));
        }
        if let Some(computer) = extract_windows_computer(raw) {
            source = computer.clone();
            metadata.insert("computer_name".to_string(), serde_json::json!(computer));
        }

        Ok(KalpixkEvent {
            timestamp_ms: chrono::Utc::now().timestamp_millis(),
            event_type,
            local_severity,
            source,
            destination: None,
            user,
            process: None,
            metadata,
            raw: raw.to_string(),
            source_type: "windows".to_string(),
            fingerprint: format!("{:x}_{}", event_id, raw.len()),
        })
    }
}

// ─── Parser DB2 Audit (IBM DB2 — Manhattan WMS) ───────────────────────────────

pub struct Db2AuditParser;

impl Default for Db2AuditParser {
    fn default() -> Self {
        Self::new()
    }
}

impl Db2AuditParser {
    pub fn new() -> Self {
        Db2AuditParser
    }
}

impl LogParser for Db2AuditParser {
    fn source_type(&self) -> &'static str {
        "db2"
    }

    fn parse(&self, raw: &str) -> Result<KalpixkEvent, ParseError> {
        let raw = raw.trim();
        if raw.is_empty() {
            return Err(ParseError::EmptyLine);
        }

        let mut metadata = HashMap::new();
        let lower = raw.to_lowercase();
        let mut event_type = EventType::DbQuery;
        let mut local_severity: f64 = 0.15_f64;

        // Detectar operaciones anómalas en DB2
        if lower.contains("drop") || lower.contains("truncate") {
            event_type = EventType::DbAnomalousQuery;
            local_severity = 0.85_f64;
            metadata.insert("destructive_query".to_string(), serde_json::json!(true));
        } else if lower.contains("grant") || lower.contains("revoke") {
            event_type = EventType::PolicyChange;
            local_severity = 0.75_f64;
        } else if lower.contains("create user") || lower.contains("alter user") {
            event_type = EventType::UserCreation;
            local_severity = 0.80_f64;
        } else if lower.contains("export") || lower.contains("load") || lower.contains("import") {
            // Operaciones de volumen de datos — potencial exfiltración
            event_type = EventType::DbAnomalousQuery;
            local_severity = 0.70_f64;
            metadata.insert("bulk_data_operation".to_string(), serde_json::json!(true));
        }

        // Tablas sensibles del Manhattan WMS
        let sensitive_tables = [
            "inventory",
            "shipment",
            "employee",
            "salary",
            "wms_user",
            "order_header",
            "billing",
            "vendor",
        ];
        for table in &sensitive_tables {
            if lower.contains(table) {
                local_severity = (local_severity + 0.20_f64).min(1.0_f64);
                metadata.insert("sensitive_table".to_string(), serde_json::json!(table));
                break;
            }
        }

        let user = extract_db2_user(raw);
        let source = extract_db2_apphost(raw).unwrap_or_else(|| "db2_server".to_string());

        Ok(KalpixkEvent {
            timestamp_ms: chrono::Utc::now().timestamp_millis(),
            event_type,
            local_severity,
            source,
            destination: Some("ibm_db2".to_string()),
            user,
            process: Some("db2sysc".to_string()),
            metadata,
            raw: raw.to_string(),
            source_type: "db2".to_string(),
            fingerprint: format!("{:x}", raw.len()),
        })
    }
}

// ─── Parser NetFlow v9 / IPFIX (simplificado) ─────────────────────────────────

pub struct NetflowParser;

impl Default for NetflowParser {
    fn default() -> Self {
        Self::new()
    }
}

impl NetflowParser {
    pub fn new() -> Self {
        NetflowParser
    }
}

impl LogParser for NetflowParser {
    fn source_type(&self) -> &'static str {
        "netflow"
    }

    fn parse(&self, raw: &str) -> Result<KalpixkEvent, ParseError> {
        let raw = raw.trim();
        if raw.is_empty() {
            return Err(ParseError::EmptyLine);
        }

        // Formato esperado: "src_ip dst_ip src_port dst_port proto bytes packets"
        let parts: Vec<&str> = raw.split_whitespace().collect();
        if parts.len() < 5 {
            return Err(ParseError::ParseFailed(
                "NetFlow requiere al menos 5 campos".to_string(),
            ));
        }

        let source = parts[0].to_string();
        let destination = parts.get(1).map(|s| s.to_string());
        let dst_port: u16 = parts.get(3).and_then(|s| s.parse().ok()).unwrap_or(0);
        let bytes: u64 = parts.get(5).and_then(|s| s.parse().ok()).unwrap_or(0);

        let mut local_severity: f64 = 0.20_f64;
        let mut event_type = EventType::NetworkConnection;
        let mut metadata = HashMap::new();

        // Puertos de alto riesgo
        let high_risk_ports = [22, 23, 3389, 445, 135, 139, 3306, 5432, 6379, 27017];
        if high_risk_ports.contains(&dst_port) {
            local_severity = 0.50_f64;
            metadata.insert("high_risk_port".to_string(), serde_json::json!(dst_port));
        }

        // Transferencia masiva de datos — potencial exfiltración
        if bytes > 100_000_000 {
            // >100MB
            local_severity = (local_severity + 0.30_f64).min(1.0_f64);
            event_type = EventType::DbAnomalousQuery; // Reutilizamos este tipo
            metadata.insert("large_transfer_bytes".to_string(), serde_json::json!(bytes));
        }

        metadata.insert("dst_port".to_string(), serde_json::json!(dst_port));
        metadata.insert("bytes".to_string(), serde_json::json!(bytes));
        if let Some(proto) = parts.get(4) {
            metadata.insert("protocol".to_string(), serde_json::json!(proto));
        }

        Ok(KalpixkEvent {
            timestamp_ms: chrono::Utc::now().timestamp_millis(),
            event_type,
            local_severity,
            source,
            destination,
            user: None,
            process: None,
            metadata,
            raw: raw.to_string(),
            source_type: "netflow".to_string(),
            fingerprint: format!("{:x}", raw.len()),
        })
    }
}

// ─── Helpers de extracción ────────────────────────────────────────────────────

fn extract_syslog_user(raw: &str) -> Option<String> {
    // Buscar "user=xxxx" o "for user xxxx"
    for pattern in &["user=", "for user ", "for invalid user "] {
        if let Some(pos) = raw.find(pattern) {
            let rest = &raw[pos + pattern.len()..];
            let end = rest
                .find(|c: char| c.is_whitespace() || c == ',' || c == ';')
                .unwrap_or(rest.len());
            return Some(rest[..end].to_string());
        }
    }
    None
}

fn extract_syslog_ip(raw: &str) -> Option<String> {
    // Buscar "from x.x.x.x"
    if let Some(pos) = raw.find("from ") {
        let rest = &raw[pos + 5..];
        let end = rest
            .find(|c: char| c.is_whitespace() || c == ':')
            .unwrap_or(rest.len());
        let candidate = &rest[..end];
        // Validar que parece una IP
        if candidate.chars().filter(|c| *c == '.').count() == 3 {
            return Some(candidate.to_string());
        }
    }
    None
}

fn extract_syslog_process(raw: &str) -> Option<String> {
    // Formato: "hostname process[pid]: ..."
    // Buscar el patrón "word[" o "word:"
    let parts: Vec<&str> = raw.splitn(4, ' ').collect();
    if parts.len() >= 3 {
        let proc_field = parts[2];
        if let Some(bracket) = proc_field.find('[') {
            return Some(proc_field[..bracket].to_string());
        }
        if proc_field.ends_with(':') {
            return Some(proc_field.trim_end_matches(':').to_string());
        }
    }
    None
}

fn extract_syslog_hostname(raw: &str) -> Option<String> {
    // El hostname suele ser el segundo token en syslog
    raw.split_whitespace().nth(1).map(String::from)
}

fn extract_windows_event_id(raw: &str) -> Option<u32> {
    for pattern in &["EventID: ", "EventID=", "<EventID>"] {
        if let Some(pos) = raw.find(pattern) {
            let rest = &raw[pos + pattern.len()..];
            let end = rest
                .find(|c: char| !c.is_ascii_digit())
                .unwrap_or(rest.len());
            return rest[..end].parse().ok();
        }
    }
    None
}

fn extract_windows_user(raw: &str) -> Option<String> {
    for pattern in &["Account Name: ", "SubjectUserName: "] {
        if let Some(pos) = raw.find(pattern) {
            let rest = &raw[pos + pattern.len()..];
            let end = rest
                .find(['\n', '\r'])
                .unwrap_or(rest.len());
            let u = rest[..end].trim().to_string();
            if !u.is_empty() && u != "-" {
                return Some(u);
            }
        }
    }
    None
}

fn extract_windows_computer(raw: &str) -> Option<String> {
    if let Some(pos) = raw.find("Computer: ") {
        let rest = &raw[pos + 10..];
        let end = rest
            .find(['\n', '\r'])
            .unwrap_or(rest.len());
        return Some(rest[..end].trim().to_string());
    }
    None
}

fn extract_db2_user(raw: &str) -> Option<String> {
    for pattern in &["AUTHID=", "UserID=", "user_id="] {
        if let Some(pos) = raw.find(pattern) {
            let rest = &raw[pos + pattern.len()..];
            let end = rest
                .find(|c: char| c.is_whitespace() || c == ',')
                .unwrap_or(rest.len());
            return Some(rest[..end].to_string());
        }
    }
    None
}

fn extract_db2_apphost(raw: &str) -> Option<String> {
    if let Some(pos) = raw.find("HOSTNAME=") {
        let rest = &raw[pos + 9..];
        let end = rest
            .find(|c: char| c.is_whitespace() || c == ',')
            .unwrap_or(rest.len());
        return Some(rest[..end].to_string());
    }
    None
}
