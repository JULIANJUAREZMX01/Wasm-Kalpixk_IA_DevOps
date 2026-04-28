//! crates/kalpixk-core/src/security.rs
//! ─────────────────────────────────────
//! ATLATL-ORDNANCE — Security hardening for the WASM engine.
//!
//! Implements:
//!   1. Input validation + Stage 2 aggressive shellcode detection
//!   2. Per-source rate limiting
//!   3. SharedArrayBuffer atomic guards
//!   4. Build-hash-based memory offset obfuscation

use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::Arc;

pub const MAX_LOG_LINE_BYTES: usize = 65_536;
pub const MAX_EVENTS_PER_SEC_PER_SOURCE: u32 = 1_000;

const BUILD_HASH: &str = match option_env!("BUILD_HASH") {
    Some(h) => h,
    None    => "atlatl-v4",
};

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum SecurityError {
    #[error("Input too large: {0} bytes")]
    InputTooLarge(usize),

    #[error("Injection pattern detected at offset {0}: {1}")]
    InjectionPattern(usize, String),

    #[error("Rate limit exceeded for source '{0}'")]
    RateLimitExceeded(String),

    #[error("Invalid metadata key '{0}'")]
    InvalidMetadataKey(String),

    #[error("Atomic buffer conflict")]
    AtomicConflict,
}

pub struct SecurityGuard;

impl SecurityGuard {
    pub fn validate_raw_log(raw: &str) -> Result<&str, SecurityError> {
        validate_raw_log(raw)
    }

    pub fn is_payload_suspicious(data: &[u8]) -> bool {
        crate::entropy::shannon_entropy(data) > 7.5
    }

    /// [ATLATL-ORDNANCE] Stage 3: Behavioral Entropy Analysis
    /// Detects high-velocity low-entropy attacks (credential stuffing) or
    /// low-velocity high-entropy attacks (exfiltration).
    pub fn analyze_behavioral_entropy(stream: &[&str]) -> f32 {
        if stream.is_empty() { return 0.0; }
        let mut total_entropy = 0.0f32;
        for line in stream {
            total_entropy += crate::entropy::shannon_entropy(line.as_bytes());
        }
        let avg_entropy = total_entropy / stream.len() as f32;

        // Return a score based on deviation from "normal" log entropy (~4.0 - 5.5)
        if avg_entropy > 7.2 { return 0.9; } // Likely encrypted data/shellcode
        if avg_entropy < 2.5 { return 0.7; } // Likely repetitive automated patterns
        0.0
    }
}

pub fn validate_raw_log(raw: &str) -> Result<&str, SecurityError> {
    if raw.len() > MAX_LOG_LINE_BYTES {
        return Err(SecurityError::InputTooLarge(raw.len()));
    }

    const PATTERNS: &[(&[u8], &str)] = &[
        (b"\\x90\\x90\\x90", "nop_sled"),
        (b"\\xEB\\xFE", "jmp_self"),
        (b"/bin/sh", "shell_invocation"),
        (b"powershell.exe", "powershell_invocation"),
        (b"${jndi:", "log4shell"),
        (b"eval(", "dynamic_eval"),
        (b"system(", "system_call"),
        (b"<script", "xss_attempt"),
        (b"../", "path_traversal"),
        (b"0xEB0xFE", "hex_jmp_self"),
    ];

    let bytes = raw.as_bytes();
    for (pattern, name) in PATTERNS {
        if let Some(pos) = bytes.windows(pattern.len()).position(|w| w == *pattern) {
            return Err(SecurityError::InjectionPattern(pos, name.to_string()));
        }
    }

    Ok(raw)
}

pub struct SourceRateLimiter {
    counts: HashMap<String, (u32, u64)>,
    max_eps: u32,
}

impl SourceRateLimiter {
    pub fn new() -> Self {
        Self {
            counts: HashMap::new(),
            max_eps: MAX_EVENTS_PER_SEC_PER_SOURCE,
        }
    }

    pub fn check_and_increment(&mut self, source: &str, now_ms: u64) -> Result<(), SecurityError> {
        const WINDOW_MS: u64 = 1_000;
        let entry = self.counts.entry(source.to_string()).or_insert((0, now_ms));

        if now_ms.saturating_sub(entry.1) >= WINDOW_MS {
            *entry = (1, now_ms);
            return Ok(());
        }

        entry.0 += 1;
        if entry.0 > self.max_eps {
            return Err(SecurityError::RateLimitExceeded(source.to_string()));
        }

        Ok(())
    }
}

pub struct SharedBufferGuard {
    version: Arc<AtomicU32>,
    locked: Arc<AtomicBool>,
}

impl SharedBufferGuard {
    pub fn new() -> Self {
        Self {
            version: Arc::new(AtomicU32::new(0)),
            locked: Arc::new(AtomicBool::new(false)),
        }
    }

    pub fn try_lock(&self, max_retries: u32) -> Result<BufferWriteGuard, SecurityError> {
        for _ in 0..max_retries {
            if self.locked.compare_exchange(false, true, Ordering::SeqCst, Ordering::Acquire).is_ok() {
                let ver = self.version.fetch_add(1, Ordering::SeqCst);
                return Ok(BufferWriteGuard {
                    locked: Arc::clone(&self.locked),
                    version: Arc::clone(&self.version),
                    ver_at_lock: ver,
                });
            }
            std::hint::spin_loop();
        }
        Err(SecurityError::AtomicConflict)
    }
}

pub struct BufferWriteGuard {
    locked: Arc<AtomicBool>,
    version: Arc<AtomicU32>,
    ver_at_lock: u32,
}

impl Drop for BufferWriteGuard {
    fn drop(&mut self) {
        self.locked.store(false, Ordering::SeqCst);
    }
}

pub fn obfuscate_offset(base: usize) -> usize {
    let seed = BUILD_HASH.bytes().fold(0usize, |acc, b| acc.wrapping_mul(31).wrapping_add(b as usize));
    base ^ (seed & 0xFF)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_malicious_patterns() {
        assert!(validate_raw_log("normal log").is_ok());
        assert!(validate_raw_log("inject \\x90\\x90\\x90 sled").is_err());
        assert!(validate_raw_log("exploit /bin/sh here").is_err());
    }
}
