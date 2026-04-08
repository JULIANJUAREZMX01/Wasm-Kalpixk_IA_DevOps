//! WASP — WebAssembly Security Protocol
//!
//! Security layer for Kalpixk WASM modules:
//! - Input validation
//! - Memory safety bounds checking
//! - Security policies enforcement

use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;

/// Security policy levels
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum SecurityLevel {
    Safe,
    Suspicious,
    Blocked,
}

/// WASP security policy result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaspPolicyResult {
    pub level: SecurityLevel,
    pub passed: bool,
    pub reason: String,
    pub violations: Vec<String>,
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

    // Check for null bytes
    if raw.contains('\0') {
        violations.push("Null byte detected in input".to_string());
    }

    // Check for control characters (potential injection)
    // Note: \x00 is caught by both null byte and control character checks
    let has_control = raw.chars().any(|c| c.is_control() && c != '\0');
    if has_control {
        violations.push("Control characters detected".to_string());
    }

    let level = match violations.len() {
        0 => SecurityLevel::Safe,
        1..=2 => SecurityLevel::Blocked, // any validation violation should be blocked
        _ => SecurityLevel::Blocked,
    };

    WaspPolicyResult {
        passed: level != SecurityLevel::Blocked,
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

    // Check for negative offset (should never happen with unsigned, but safety first)
    if offset > max_memory {
        violations.push(format!("Offset out of bounds: {} > {}", offset, max_memory));
    }

    // Check for overflow
    if offset.saturating_add(length) > max_memory {
        violations.push(format!(
            "Memory access overflow: {}+{} > {}",
            offset, length, max_memory
        ));
    }

    // Check for suspiciously large allocations
    if length > max_memory / 2 {
        violations.push(format!("Suspiciously large allocation: {}", length));
    }

    let level = match violations.len() {
        0 => SecurityLevel::Safe,
        1..=2 => SecurityLevel::Suspicious,
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

/// Rate limiting — prevent DoS via request flooding
#[derive(Debug)]
pub struct RateLimiter {
    pub max_requests: usize,
    pub window_ms: u64,
    requests: Vec<u64>,
}

impl RateLimiter {
    pub fn new(max_requests: usize, window_ms: u64) -> Self {
        Self {
            max_requests,
            window_ms,
            requests: Vec::new(),
        }
    }

    pub fn check(&mut self, timestamp_ms: u64) -> WaspPolicyResult {
        // Remove old requests outside window
        self.requests
            .retain(|&t| timestamp_ms.saturating_sub(t) < self.window_ms);

        let count = self.requests.len();
        let mut violations = Vec::new();

        if count >= self.max_requests {
            violations.push(format!(
                "Rate limit exceeded: {}/{} in {}ms",
                count, self.max_requests, self.window_ms
            ));
        }

        self.requests.push(timestamp_ms);

        let level = match violations.len() {
            0 => SecurityLevel::Safe,
            _ => SecurityLevel::Blocked,
        };

        WaspPolicyResult {
            passed: level != SecurityLevel::Blocked,
            level,
            reason: if violations.is_empty() {
                format!("Rate OK: {}/{}", count, self.max_requests)
            } else {
                violations[0].clone()
            },
            violations,
        }
    }
}

/// WASM module integrity check
pub fn verify_module_integrity(module_hash: &str, expected_hash: &str) -> WaspPolicyResult {
    let mut violations = Vec::new();

    if module_hash != expected_hash {
        violations.push(format!(
            "Module integrity check failed: {} != {}",
            module_hash, expected_hash
        ));
    }

    WaspPolicyResult {
        passed: violations.is_empty(),
        level: if violations.is_empty() {
            SecurityLevel::Safe
        } else {
            SecurityLevel::Blocked
        },
        reason: if violations.is_empty() {
            "Module verified".to_string()
        } else {
            violations[0].clone()
        },
        violations,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_input_ok() {
        let result = validate_input("normal input string", 1000);
        assert!(result.passed);
        assert_eq!(result.level, SecurityLevel::Safe);
    }

    #[test]
    fn test_validate_input_too_long() {
        let result = validate_input(&"x".repeat(2000), 1000);
        assert!(!result.passed);
        assert_eq!(result.level, SecurityLevel::Blocked);
    }

    #[test]
    fn test_validate_input_null_byte() {
        let result = validate_input("input\x00with null", 1000);
        assert!(!result.passed);
    }

    #[test]
    fn test_rate_limiter() {
        let mut rl = RateLimiter::new(3, 1000);

        // First 3 requests should pass
        assert!(rl.check(1000).passed);
        assert!(rl.check(1001).passed);
        assert!(rl.check(1002).passed);

        // 4th should fail
        let result = rl.check(1003);
        assert!(!result.passed);
    }
}
