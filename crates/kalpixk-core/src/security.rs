//! crates/kalpixk-core/src/security.rs
//! ─────────────────────────────────────
//! ATLATL-ORDNANCE — Security hardening for the WASM engine.
//! Version: 4.0.0-atlatl (GuerrillaMesh)

use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::Arc;

// ── Constants ─────────────────────────────────────────────────────────────────

pub const MAX_LOG_LINE_BYTES: usize = 65_536;
pub const MAX_EVENTS_PER_SEC_PER_SOURCE: u32 = 1_000;
pub const MAX_METADATA_FIELDS: usize = 64;

const BUILD_HASH: &str = match option_env!("BUILD_HASH") {
    Some(h) => h,
    None    => "atlatl-v4-prod",
};

// ── Error types ───────────────────────────────────────────────────────────────

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum SecurityError {
    #[error("Input too large: {0} bytes (max: {1})")]
    InputTooLarge(usize, usize),

    #[error("Injection pattern detected at byte offset {0}: pattern='{1}'")]
    InjectionPattern(usize, String),

    #[error("Rate limit exceeded for source '{0}': {1} events/sec (max: {2})")]
    RateLimitExceeded(String, u32, u32),

    #[error("Invalid metadata key '{0}': only alphanumeric, '_', '-' allowed")]
    InvalidMetadataKey(String),

    #[error("Atomic buffer conflict: concurrent write detected")]
    AtomicConflict,
}

// ── Security Guard Implementation ─────────────────────────────────────────────

pub struct SecurityGuard;

impl SecurityGuard {
    /// Validate and sanitize a raw log string before parsing.
    /// [ATLATL-ORDNANCE] v4.0: Added Stage 2 aggressive shellcode detection.
    pub fn validate_raw_log(raw: &str) -> Result<&str, SecurityError> {
        if raw.len() > MAX_LOG_LINE_BYTES {
            return Err(SecurityError::InputTooLarge(raw.len(), MAX_LOG_LINE_BYTES));
        }

        const INJECTION_PATTERNS: &[(&[u8], &str)] = &[
            (b"\x00",       "null_byte"),
            (b"\r\n\r\n",   "http_header_injection"),
            (b"{{",         "template_injection"),
            (b"${",         "shell_expansion"),
            (b"<script",    "xss_script_tag"),
            (b"<iframe",    "xss_iframe"),
            (b"\x1b[",      "ansi_escape"),
            (b"../",        "path_traversal"),
            (b"\\x90\\x90", "nop_sled"),
            (b"\\xEB\\xFE", "jmp_self_loop"),
            (b"/bin/sh",    "unix_shell_exec"),
            (b"powershell", "win_shell_exec"),
            (b"${jndi:",    "log4shell_injection"),
            (b"base64",     "obfuscation_attempt"),
        ];

        let bytes = raw.as_bytes();
        for (pattern, name) in INJECTION_PATTERNS {
            if let Some(pos) = bytes
                .windows(pattern.len())
                .position(|w| w == *pattern)
            {
                return Err(SecurityError::InjectionPattern(pos, name.to_string()));
            }
        }

        Ok(raw)
    }

    pub fn is_payload_suspicious(data: &[u8]) -> bool {
        let entropy = crate::entropy::shannon_entropy(data);
        entropy > 7.8 // Hardened threshold for v4.0
    }
}

pub fn validate_raw_log(raw: &str) -> Result<&str, SecurityError> {
    SecurityGuard::validate_raw_log(raw)
}

pub fn validate_metadata_key(key: &str) -> Result<(), SecurityError> {
    if key.len() > 64 || key.is_empty() {
        return Err(SecurityError::InvalidMetadataKey(key.to_string()));
    }
    if !key.chars().all(|c| c.is_alphanumeric() || c == '_' || c == '-') {
        return Err(SecurityError::InvalidMetadataKey(key.to_string()));
    }
    Ok(())
}

// ── Rate limiter ──────────────────────────────────────────────────────────────

pub struct SourceRateLimiter {
    counts:  HashMap<String, (u32, u64)>,
    max_eps: u32,
}

impl SourceRateLimiter {
    pub fn new() -> Self {
        Self {
            counts:  HashMap::new(),
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
            return Err(SecurityError::RateLimitExceeded(source.to_string(), entry.0, self.max_eps));
        }
        Ok(())
    }

    pub fn gc(&mut self, now_ms: u64) {
        self.counts.retain(|_, (_, ts)| now_ms.saturating_sub(*ts) < 60_000);
    }
}

// ── SharedArrayBuffer atomic guard ───────────────────────────────────────────

pub struct SharedBufferGuard {
    version: Arc<AtomicU32>,
    locked:  Arc<AtomicBool>,
}

impl SharedBufferGuard {
    pub fn new() -> Self {
        Self {
            version: Arc::new(AtomicU32::new(0)),
            locked:  Arc::new(AtomicBool::new(false)),
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
    locked:      Arc<AtomicBool>,
    version:     Arc<AtomicU32>,
    ver_at_lock: u32,
}

impl Drop for BufferWriteGuard {
    fn drop(&mut self) {
        self.locked.store(false, Ordering::SeqCst);
    }
}

// ── Unit tests ────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_valid_log() {
        assert!(validate_raw_log("User login successful").is_ok());
    }

    #[test]
    fn rejects_nop_sled() {
        assert!(validate_raw_log("malicious\\x90\\x90sled").is_err());
    }

    #[test]
    fn rejects_jmp_self() {
        assert!(validate_raw_log("poison\\xEB\\xFEloop").is_err());
    }
}
