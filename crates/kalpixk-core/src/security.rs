//! crates/kalpixk-core/src/security.rs
//! ────────────────────────────────────────────────────────────────────────────
//! ATLATL-ORDNANCE — Security hardening and forensic validation for the Kalpixk WASM engine.
//!
//! This module implements the "Blue Phase" (Hardening) of the ATLATL cycle,
//! providing multi-layered protection against common offensive techniques:
//! - Input size validation (DoS mitigation)
//! - Binary/Injection pattern matching (Shellcode, XSS, Path Traversal)
//! - Per-source Rate Limiting (Flood protection)
//! - Atomic state synchronization for SharedArrayBuffers
//! - Memory fingerprinting for build integrity

use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::Arc;

// ── Constants ─────────────────────────────────────────────────────────────────

/// Maximum allowed size for a single log line (64 KB). Prevents memory exhaustion.
pub const MAX_LOG_LINE_BYTES: usize = 65_536;

/// Default rate limit: 1000 events per second per source.
pub const MAX_EVENTS_PER_SEC_PER_SOURCE: u32 = 1_000;

/// Maximum number of metadata fields allowed per event.
pub const MAX_METADATA_FIELDS: usize = 64;

/// Unique build identifier used for memory obfuscation seeds.
const BUILD_HASH: &str = match option_env!("BUILD_HASH") {
    Some(h) => h,
    None => "dev-000000",
};

// ── Error types ───────────────────────────────────────────────────────────────

/// Security violation categories for forensic logging and retaliation triggers.
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

// ── Input validation ──────────────────────────────────────────────────────────

/// Validates raw log data against a matrix of known attack signatures.
/// Returns Ok(raw) if clean, or Err(SecurityError) if a threat is detected.
pub fn validate_raw_log(raw: &str) -> Result<&str, SecurityError> {
    if raw.len() > MAX_LOG_LINE_BYTES {
        return Err(SecurityError::InputTooLarge(raw.len(), MAX_LOG_LINE_BYTES));
    }

    /// Forensic pattern matrix for Stage 2 Aggressive Detection.
    const INJECTION_PATTERNS: &[(&[u8], &str)] = &[
        (b"\x00", "null_byte"),                     // C-style string termination
        (b"\r\n\r\n", "http_header_injection"),     // HTTP splitting
        (b"{{", "template_injection"),              // SSTI (Server Side Template Injection)
        (b"${", "shell_expansion"),                 // Log4Shell / OS Command Injection
        (b"<script", "xss_script_tag"),             // Cross-Site Scripting
        (b"<iframe", "xss_iframe"),                 // UI Redressing
        (b"<!--", "html_comment"),                  // HTML Obfuscation
        (b"\x1b[", "ansi_escape"),                  // Terminal escape sequences
        (b"\x1b(", "ansi_charset"),                 // Character set manipulation
        (b"../", "path_traversal"),                 // LFI/Directory traversal
        (b"..\\", "path_traversal_win"),            // Windows traversal
        (b"\\x90\\x90", "nop_sled"),                // Buffer overflow preparation
        (b"0xEB0xFE", "jmp_self"),                  // Infinite loop shellcode
    ];

    let bytes = raw.as_bytes();
    for (pattern, name) in INJECTION_PATTERNS {
        if let Some(pos) = bytes.windows(pattern.len()).position(|w| w == *pattern) {
            return Err(SecurityError::InjectionPattern(pos, name.to_string()));
        }
    }

    Ok(raw)
}

/// Enforces naming conventions for event metadata to prevent injection into downstream DBs.
pub fn validate_metadata_key(key: &str) -> Result<(), SecurityError> {
    if key.len() > 64 || key.is_empty() {
        return Err(SecurityError::InvalidMetadataKey(key.to_string()));
    }
    if !key
        .chars()
        .all(|c| c.is_alphanumeric() || c == '_' || c == '-')
    {
        return Err(SecurityError::InvalidMetadataKey(key.to_string()));
    }
    Ok(())
}

/// Unified security context for WASM runtime.
pub struct SecurityGuard;

impl SecurityGuard {
    /// Public boolean check for quick-reject paths.
    pub fn validate_raw_log(raw: &str) -> bool {
        validate_raw_log(raw).is_ok()
    }

    /// Analyzes payload entropy to detect encrypted/compressed exfiltration streams.
    pub fn is_payload_suspicious(data: &[u8]) -> bool {
        let entropy = crate::entropy::shannon_entropy(data);
        entropy > 7.5 // Threshold for high-randomness/encrypted data
    }
}

// ── Rate limiter ──────────────────────────────────────────────────────────────

/// Sliding-window rate limiter for multi-tenant log ingestion.
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

    /// Increments and checks the rate for a given source IP/ID.
    pub fn check_and_increment(&mut self, source: &str, now_ms: u64) -> Result<(), SecurityError> {
        const WINDOW_MS: u64 = 1_000; // 1 second window

        let entry = self.counts.entry(source.to_string()).or_insert((0, now_ms));

        // Reset if window passed
        if now_ms.saturating_sub(entry.1) >= WINDOW_MS {
            *entry = (1, now_ms);
            return Ok(());
        }

        entry.0 += 1;
        if entry.0 > self.max_eps {
            return Err(SecurityError::RateLimitExceeded(
                source.to_string(),
                entry.0,
                self.max_eps,
            ));
        }

        Ok(())
    }

    /// Garbage collection for stale rate limit entries.
    pub fn gc(&mut self, now_ms: u64) {
        self.counts
            .retain(|_, (_, ts)| now_ms.saturating_sub(*ts) < 60_000);
    }

    pub fn source_count(&self) -> usize {
        self.counts.len()
    }

    /// Stub for rate checking (reserved for global policy integration).
    pub fn check_rate(_source: &str) -> bool {
        true
    }
}

impl Default for SourceRateLimiter {
    fn default() -> Self {
        Self::new()
    }
}

// ── SharedArrayBuffer atomic guard ───────────────────────────────────────────

/// Synchronizes access to SharedArrayBuffers across WebWorkers to prevent race conditions.
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

    /// Attempts to acquire an atomic lock for writing.
    pub fn try_lock(&self, max_retries: u32) -> Result<BufferWriteGuard, SecurityError> {
        for _ in 0..max_retries {
            match self
                .locked
                .compare_exchange(false, true, Ordering::SeqCst, Ordering::Acquire)
            {
                Ok(_) => {
                    let ver = self.version.fetch_add(1, Ordering::SeqCst);
                    return Ok(BufferWriteGuard {
                        locked: Arc::clone(&self.locked),
                        version: Arc::clone(&self.version),
                        ver_at_lock: ver,
                    });
                }
                Err(_) => std::hint::spin_loop(),
            }
        }
        Err(SecurityError::AtomicConflict)
    }

    pub fn current_version(&self) -> u32 {
        self.version.load(Ordering::SeqCst)
    }
}

impl Default for SharedBufferGuard {
    fn default() -> Self {
        Self::new()
    }
}

/// RAII guard for buffer write operations.
pub struct BufferWriteGuard {
    locked: Arc<AtomicBool>,
    version: Arc<AtomicU32>,
    ver_at_lock: u32,
}

impl BufferWriteGuard {
    /// Validates that no concurrent modifications occurred during the guard's lifetime.
    pub fn verify_integrity(&self) -> bool {
        self.version.load(Ordering::SeqCst) == self.ver_at_lock + 1
    }
}

impl Drop for BufferWriteGuard {
    fn drop(&mut self) {
        self.locked.store(false, Ordering::SeqCst);
    }
}

// ── Memory offset obfuscation ─────────────────────────────────────────────────

/// Returns the build-specific fingerprint for client identification.
pub fn build_fingerprint() -> &'static str {
    BUILD_HASH
}

/// Applies a build-deterministic XOR mask to memory offsets.
/// Used to thwart fixed-offset memory exploits (e.g. ROP chains).
pub fn obfuscate_offset(base: usize) -> usize {
    let seed = BUILD_HASH.bytes().take(8).fold(0usize, |acc, b| {
        acc.wrapping_mul(31).wrapping_add(b as usize)
    });
    base ^ (seed & 0xFF)
}

// ── Unit tests ────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_valid_syslog() {
        let log = "Apr 04 03:22:11 cedis sshd[1234]: Failed password for root from 185.220.101.42";
        assert!(validate_raw_log(log).is_ok());
    }

    #[test]
    fn rejects_null_byte() {
        assert!(matches!(
            validate_raw_log("normal\x00injected"),
            Err(SecurityError::InjectionPattern(6, _))
        ));
    }

    #[test]
    fn rejects_oversized_log() {
        let huge = "a".repeat(MAX_LOG_LINE_BYTES + 1);
        assert!(matches!(
            validate_raw_log(&huge),
            Err(SecurityError::InputTooLarge(_, _))
        ));
    }

    #[test]
    fn rejects_ansi_escape() {
        assert!(validate_raw_log("log with \x1b[31mred\x1b[0m text").is_err());
    }

    #[test]
    fn rejects_template_injection() {
        assert!(validate_raw_log("{{config.secret}}").is_err());
        assert!(validate_raw_log("${HOME}").is_err());
    }

    #[test]
    fn rejects_xss_payload() {
        assert!(validate_raw_log("<script>alert(1)</script>").is_err());
    }

    #[test]
    fn accepts_valid_keys() {
        assert!(validate_metadata_key("src_ip").is_ok());
        assert!(validate_metadata_key("windows-event-id").is_ok());
    }

    #[test]
    fn rejects_key_with_spaces() {
        assert!(validate_metadata_key("key with spaces").is_err());
    }

    #[test]
    fn rate_limiter_allows_within_limit() {
        let mut rl = SourceRateLimiter::new();
        let src = "185.220.101.42";
        let now_ms = 1_000_000u64;

        for _ in 0..MAX_EVENTS_PER_SEC_PER_SOURCE {
            assert!(rl.check_and_increment(src, now_ms).is_ok());
        }
    }

    #[test]
    fn rate_limiter_blocks_flood() {
        let mut rl = SourceRateLimiter::new();
        let src = "185.220.101.42";
        let now_ms = 1_000_000u64;

        for _ in 0..MAX_EVENTS_PER_SEC_PER_SOURCE {
            let _ = rl.check_and_increment(src, now_ms);
        }
        assert!(matches!(
            rl.check_and_increment(src, now_ms),
            Err(SecurityError::RateLimitExceeded(_, _, _))
        ));
    }

    #[test]
    fn atomic_guard_locks_and_releases() {
        let guard = SharedBufferGuard::new();
        {
            let lock = guard.try_lock(10).expect("should acquire lock");
            assert!(lock.verify_integrity());
        }
        let _ = guard.try_lock(10).expect("should re-acquire after release");
    }

    #[test]
    fn build_fingerprint_not_empty() {
        assert!(!build_fingerprint().is_empty());
    }
}
