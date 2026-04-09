use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WasmEventMetrics {
    pub instruction_count: u64,
    pub memory_pages: u32,
    pub fuel_consumed: u64,
    pub wall_time_ns: u64,
    pub entropy: f32,
    pub call_depth: u32,
    pub import_calls: u32,
    pub export_calls: u32,
}
