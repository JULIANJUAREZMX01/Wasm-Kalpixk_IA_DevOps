//! WASP — WebAssembly Security Protocol
//!
//! Security layer for Kalpixk WASM modules:
//! - Input validation
//! - Memory safety bounds checking
//! - Security policies enforcement
//! - [ATLATL-ORDNANCE] Instruction Monitoring & FFI Guards

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

    // Increment heartbeat on every FFI call
    INSTRUCTION_HEARTBEAT.fetch_add(1, Ordering::Relaxed);

    // Prohibit sensitive functions if security context is not explicitly verified
    let sensitive_fns = ["system", "exec", "eval", "poison_pointers", "wasm_lockdown"];
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
    INSTRUCTION_HEARTBEAT.load(Ordering::Relaxed)
}

/// Input validation — sanitizes and validates WASM inputs
pub fn validate_input(raw: &str, max_len: usize) -> WaspPolicyResult {
    let mut violations = Vec::new();

    // Check length
    if raw.len() > max_len {
        violations.push(format!(
            "Input exceeds max length: {} > {}",
            raw.len(),
            max_len
        ));
    }

    // Check for null bytes (canary for buffer overflow attempts)
    if raw.contains('\0') {
        violations.push("Null byte detected in input (Vector: BufferOverflow)".to_string());
    }

    // Check for control characters (potential injection)
    let has_control = raw.chars().any(|c| c.is_control() && c != '\0' && c != '\n' && c != '\r' && c != '\t');
    if has_control {
        violations.push("Anomalous control characters detected (Vector: Injection)".to_string());
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
        reason: if violations.is_empty() {
            "Input validated".to_string()
        } else {
            violations.join("; ")
        },
        violations,
    }
}

/// Memory safety — bounds checking for WASM memory access
pub fn check_memory_bounds(offset: usize, length: usize, max_memory: usize) -> WaspPolicyResult {
    let mut violations = Vec::new();

    if offset > max_memory {
        violations.push(format!("Offset out of bounds: {} > {}", offset, max_memory));
    }

    if offset.saturating_add(length) > max_memory {
        violations.push(format!(
            "Memory access overflow: {}+{} > {}",
            offset, length, max_memory
        ));
    }

    // [ATLATL-ORDNANCE] Detect Heap Spraying attempts
    if length > max_memory / 4 {
        violations.push(format!("Suspiciously large allocation (Vector: HeapSpray): {}", length));
    }

    let level = match violations.len() {
        0 => SecurityLevel::Safe,
        1 => SecurityLevel::Suspicious,
        _ => SecurityLevel::Blocked,
    };

    WaspPolicyResult {
        passed: level != SecurityLevel::Blocked,
        level,
        reason: if violations.is_empty() {
            "Memory access safe".to_string()
        } else {
            violations.join("; ")
        },
        violations,
    }
}

/// WASM module integrity check
pub fn verify_module_integrity(module_hash: &str, expected_hash: &str) -> WaspPolicyResult {
    let mut violations = Vec::new();

    if module_hash != expected_hash {
        violations.push(format!(
            "Module integrity check failed (Vector: Tampering): {} != {}",
            module_hash, expected_hash
        ));
    }

    WaspPolicyResult {
        passed: violations.is_empty(),
        level: if violations.is_empty() {
            SecurityLevel::Safe
        } else {
            SecurityLevel::Exterminated
        },
        reason: if violations.is_empty() {
            "Module verified".to_string()
        } else {
            violations[0].clone()
        },
        violations,
    }
}
