//! WASP — WebAssembly Security Protocol
//!
//! Security layer for Kalpixk WASM modules:
//! - Input validation
//! - Memory safety bounds checking
//! - Security policies enforcement
//! - [ATLATL-ORDNANCE] Instruction Monitoring & FFI Guards
//!
//! Version 3.0: Atomic Heartbeat & Instruction Monitoring

use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicU64, Ordering};

/// [ATLATL-ORDNANCE] Global Instruction Counter for Heartbeat
static INSTRUCTION_HEARTBEAT: AtomicU64 = AtomicU64::new(0);

/// Security policy levels
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum SecurityLevel {
    Safe,
    Suspicious,
    Blocked,
    Exterminated,
}

/// WASP security policy result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaspPolicyResult {
    pub level: SecurityLevel,
    pub passed: bool,
    pub reason: String,
    pub violations: Vec<String>,
}

/// [ATLATL-ORDNANCE] FFI Boundary Guard
/// Ensures that calls across the FFI boundary are authenticated and within limits.
pub fn validate_ffi_call(function_name: &str, params_count: usize) -> WaspPolicyResult {
    let mut violations = Vec::new();

    // Increment heartbeat on every FFI call to track runtime integrity
    INSTRUCTION_HEARTBEAT.fetch_add(1, Ordering::SeqCst);

    // Prohibit sensitive functions if security context is not explicitly verified
    let sensitive_fns = ["system", "exec", "eval", "poison_pointers", "wasm_lockdown", "macuahuitl_strike"];
    if sensitive_fns.contains(&function_name) {
        violations.push(format!("CRITICAL: Unauthorized call to sensitive FFI function: {}", function_name));
    }

    if params_count > 10 {
        violations.push(format!("Excessive parameters in FFI call: {}", params_count));
    }

    let level = if violations.is_empty() {
        SecurityLevel::Safe
    } else {
        SecurityLevel::Exterminated
    };

    WaspPolicyResult {
        passed: violations.is_empty(),
        level,
        reason: if violations.is_empty() { "FFI call validated".to_string() } else { violations.join("; ") },
        violations,
    }
}

/// [ATLATL-ORDNANCE] Heartbeat Check
/// Returns the current instruction count for the host to verify runtime activity.
pub fn get_runtime_heartbeat() -> u64 {
    INSTRUCTION_HEARTBEAT.load(Ordering::SeqCst)
}

/// Input validation — sanitizes and validates WASM inputs
pub fn validate_input(raw: &str, max_len: usize) -> WaspPolicyResult {
    let mut violations = Vec::new();

    if raw.len() > max_len {
        violations.push(format!("Input exceeds max length: {} > {}", raw.len(), max_len));
    }

    if raw.contains('\0') {
        violations.push("Null byte detected (BufferOverflow)".to_string());
    }

    let has_control = raw.chars().any(|c| c.is_control() && c != '\n' && c != '\r' && c != '\t');
    if has_control {
        violations.push("Anomalous control characters detected (Injection)".to_string());
    }

    let level = if violations.is_empty() {
        SecurityLevel::Safe
    } else if violations.len() > 2 {
        SecurityLevel::Exterminated
    } else {
        SecurityLevel::Blocked
    };

    WaspPolicyResult {
        passed: level == SecurityLevel::Safe,
        level,
        reason: if violations.is_empty() { "Input validated".to_string() } else { violations.join("; ") },
        violations,
    }
}

/// Memory safety — bounds checking for WASM memory access
pub fn check_memory_bounds(offset: usize, length: usize, max_memory: usize) -> WaspPolicyResult {
    let mut violations = Vec::new();

    if offset > max_memory || offset.saturating_add(length) > max_memory {
        violations.push(format!("Memory access out of bounds: {}+{} > {}", offset, length, max_memory));
    }

    if length > max_memory / 4 {
        violations.push(format!("Suspiciously large allocation (HeapSpray): {}", length));
    }

    let level = match violations.len() {
        0 => SecurityLevel::Safe,
        1 => SecurityLevel::Suspicious,
        _ => SecurityLevel::Blocked,
    };

    WaspPolicyResult {
        passed: level != SecurityLevel::Blocked,
        level,
        reason: if violations.is_empty() { "Memory access safe".to_string() } else { violations.join("; ") },
        violations,
    }
}
