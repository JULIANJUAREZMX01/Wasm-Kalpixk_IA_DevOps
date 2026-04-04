//! Tipos canónicos de eventos Kalpixk
//!
//! Todos los parsers normalizan sus salidas a KalpixkEvent.
//! Este formato es el contrato entre el motor WASM y el backend GPU.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Evento de seguridad normalizado — formato canónico de Kalpixk
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KalpixkEvent {
    /// Timestamp en millisegundos epoch UTC
    pub timestamp_ms: i64,

    /// Tipo de evento (login, file_access, network_conn, db_query, process_exec)
    pub event_type: EventType,

    /// Severidad calculada por heurísticas locales (0.0 - 1.0)
    pub local_severity: f64,

    /// IP o hostname de origen
    pub source: String,

    /// IP o hostname de destino (si aplica)
    pub destination: Option<String>,

    /// Usuario asociado al evento
    pub user: Option<String>,

    /// Proceso que generó el evento
    pub process: Option<String>,

    /// Campos adicionales específicos del tipo de log (key→value)
    pub metadata: HashMap<String, serde_json::Value>,

    /// Log original sin procesar (para forensics)
    pub raw: String,

    /// Fuente del log (syslog, windows_event, db2_audit, netflow)
    pub source_type: String,

    /// Hash del evento para deduplicación
    pub fingerprint: String,
}

/// Tipos de evento soportados por Kalpixk
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum EventType {
    LoginSuccess,
    LoginFailure,
    LoginBruteForce,
    FileAccess,
    FileModification,
    FileDeletion,
    NetworkConnection,
    NetworkScan,
    ProcessExecution,
    PrivilegeEscalation,
    ServiceChange,
    DbQuery,
    DbAnomalousQuery,
    UserCreation,
    UserDeletion,
    PolicyChange,
    /// Evento que no calza en ninguna categoría conocida
    Unknown,
}

impl EventType {
    pub fn base_severity(&self) -> f64 {
        match self {
            EventType::LoginBruteForce => 0.85,
            EventType::PrivilegeEscalation => 0.90,
            EventType::DbAnomalousQuery => 0.80,
            EventType::NetworkScan => 0.75,
            EventType::FileDeletion => 0.65,
            EventType::UserCreation | EventType::UserDeletion => 0.70,
            EventType::PolicyChange => 0.75,
            EventType::FileModification => 0.40,
            EventType::LoginFailure => 0.35,
            EventType::ProcessExecution => 0.30,
            EventType::NetworkConnection => 0.20,
            EventType::LoginSuccess | EventType::FileAccess | EventType::DbQuery => 0.10,
            EventType::ServiceChange => 0.45,
            EventType::Unknown => 0.50,
        }
    }
}

/// Features numéricas extraídas de un KalpixkEvent para el modelo GPU
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventFeatures {
    /// 32 features numéricas — el contrato con el modelo PyTorch
    pub vector: Vec<f64>,

    /// Nombre de cada feature (para interpretabilidad)
    pub names: Vec<String>,
}

/// Features de sesión UEBA (User and Entity Behavior Analytics)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UebaSessionFeatures {
    pub user: String,
    pub session_duration_ms: i64,
    pub event_count: usize,
    pub unique_resources: usize,
    pub failed_auth_ratio: f64,
    pub off_hours_ratio: f64, // Ratio de eventos fuera de horario laboral
    pub data_transfer_bytes: i64,
    pub unique_destinations: usize,
    pub privilege_escalation_attempts: usize,
    pub db_query_volume: usize,
    pub db_unusual_tables: usize, // Tablas poco consultadas por este usuario
    pub lateral_movement_score: f64, // Heurística de movimiento lateral
    /// Vector completo para el modelo
    pub feature_vector: Vec<f64>,
}
