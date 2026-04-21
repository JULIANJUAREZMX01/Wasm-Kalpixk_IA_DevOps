//! crates/kalpixk-core/src/security.rs
//! ─────────────────────────────────────
//! ATLATL-ORDNANCE — Security hardening for the WASM engine.
//!
//! Implements:
//!   1. Input validation + injection pattern detection
//!   2. Per-source rate limiting (prevents log flood DoS)
//!   3. SharedArrayBuffer atomic guards (prevents SAB race conditions)
//!   4. Build-hash-based memory offset obfuscation
//!   5. Required security headers documentation
//!
//! All public functions are called by parsers.rs BEFORE any parsing occurs.
//! This is the first gate — if validation fails, the log is rejected.
#![allow(dead_code)]
//! [ATLATL-ORDNANCE] Security Guards
//! Input validation and memory protection for the WASM engine.

use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::Arc;

// ── Constants ─────────────────────────────────────────────────────────────────

/// Maximum allowed log line size (64 KB).
/// Prevents memory exhaustion via crafted oversized logs.
pub const MAX_LOG_LINE_BYTES: usize = 65_536;

/// Maximum events per second per source IP / identifier.
/// Prevents the WASM engine from being flooded by a single source.
pub const MAX_EVENTS_PER_SEC_PER_SOURCE: u32 = 1_000;

/// Maximum metadata fields per event.
/// Prevents unbounded HashMap growth.
pub const MAX_METADATA_FIELDS: usize = 64;

/// Build hash injected by CI — used to rotate memory layout per build.
/// Set via: BUILD_HASH=$(git rev-parse --short HEAD) wasm-pack build
const BUILD_HASH: &str = match option_env!("BUILD_HASH") {
    Some(h) => h,
    None => "dev-000000",
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

// ── Input validation ──────────────────────────────────────────────────────────

/// Validate and sanitize a raw log string before parsing.
///
/// Rejects:
/// - Lines exceeding `MAX_LOG_LINE_BYTES`
/// - Null bytes (would corrupt C-style string handling)
/// - ANSI escape sequences (terminal injection)
/// - Template injection patterns (`{{`, `${`)
/// - HTML/script injection (if logs reach the dashboard unsanitized)
/// - HTTP header injection (`\r\n\r\n`)
///
/// Returns the original `raw` slice if validation passes,
/// or `SecurityError` if any check fails.
pub fn validate_raw_log(raw: &str) -> Result<&str, SecurityError> {
    // 1. Size limit (stricter limit from ATLATL-ORDNANCE)
    if raw.len() > 8192 {
        return Err(SecurityError::InputTooLarge(raw.len(), 8192));
    }

    // 2. Injection pattern detection
    //    Each entry: (pattern_bytes, human_readable_name)
    const INJECTION_PATTERNS: &[(&[u8], &str)] = &[
        (b"\x00", "null_byte"),
        (b"\r\n\r\n", "http_header_injection"),
        (b"{{", "template_injection"),
        (b"${", "shell_expansion"),
        (b"<script", "xss_script_tag"),
        (b"<iframe", "xss_iframe"),
        (b"<!--", "html_comment"),
        (b"\x1b", "ansi_escape"),
        (b"../", "path_traversal"),
        (b"..\\", "path_traversal_win"),
        (b"\\x90\\x90\\x90", "nop_sled"),
        (b"0xEB0xFE", "jmp_self"),
        (b"/bin/sh", "unix_shell"),
        (b"powershell.exe", "windows_shell"),
        (b"eval(", "dynamic_exec"),
        (b"system(", "system_call"),
        (b"base64", "obfuscation_marker"),
        (b"${jndi:", "log4shell"),
    ];

    let bytes = raw.as_bytes();
    for (pattern, name) in INJECTION_PATTERNS {
        if let Some(pos) = bytes.windows(pattern.len()).position(|w| w == *pattern) {
            return Err(SecurityError::InjectionPattern(pos, name.to_string()));
        }
    }

    Ok(raw)
}

/// Validate a metadata key — only alphanumeric, underscore, hyphen allowed.
/// Keys longer than 64 chars are also rejected.
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

// ── Rate limiter ──────────────────────────────────────────────────────────────

/// Per-source sliding-window rate limiter.
///
/// Uses 1-second windows. When a source exceeds `MAX_EVENTS_PER_SEC_PER_SOURCE`
/// events within the current window, subsequent events are rejected until the
/// window resets.
pub struct SourceRateLimiter {
    /// Map: source_id → (count_in_window, window_start_ms)
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

    pub fn with_limit(max_eps: u32) -> Self {
        Self {
            counts: HashMap::new(),
            max_eps,
        }
    }

    /// Check if the source is within rate limit, and increment its counter.
    ///
    /// # Arguments
    /// * `source`  - IP address, hostname, or any string identifier
    /// * `now_ms`  - Current timestamp in milliseconds
    ///
    /// # Returns
    /// `Ok(())` if within limit, `Err(RateLimitExceeded)` if over.
    pub fn check_and_increment(&mut self, source: &str, now_ms: u64) -> Result<(), SecurityError> {
        const WINDOW_MS: u64 = 1_000;

        let entry = self.counts.entry(source.to_string()).or_insert((0, now_ms));

        // New window
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

    /// Remove stale entries older than 60 seconds.
    /// Call periodically to prevent unbounded HashMap growth.
    pub fn gc(&mut self, now_ms: u64) {
        self.counts
            .retain(|_, (_, ts)| now_ms.saturating_sub(*ts) < 60_000);
    }

    pub fn source_count(&self) -> usize {
        self.counts.len()
    }
}

impl Default for SourceRateLimiter {
    fn default() -> Self {
        Self::new()
    }
}

// ── SharedArrayBuffer atomic guard ───────────────────────────────────────────
//
// When the WASM engine writes feature vectors into a SharedArrayBuffer (SAB)
// shared with the main React thread, there is a risk of the JS thread reading
// a partially-written vector. We use an atomic version stamp to detect this.
//
// Protocol:
//   1. WASM acquires lock (CAS false→true)
//   2. Increments version stamp
//   3. Writes feature data
//   4. Drops lock (sets to false)
//   5. JS reads version stamp before and after reading data — if they differ,
//      the data was modified mid-read and must be discarded.

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

    /// Attempt to acquire the write lock.
    ///
    /// Spins up to `max_retries` times before giving up.
    /// In WebAssembly, spinning is acceptable for short critical sections.
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

/// RAII guard — releases the lock when dropped.
pub struct BufferWriteGuard {
    locked: Arc<AtomicBool>,
    version: Arc<AtomicU32>,
    ver_at_lock: u32,
}

impl BufferWriteGuard {
    /// Verify the buffer was not concurrently modified.
    /// Call after writing data to confirm integrity.
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
//
// Each build uses a different offset seed derived from BUILD_HASH.
// An exploit that hardcodes memory offsets from one build will fail on the next.
// NOT a security boundary — provides friction against static analysis.

/// Get the build fingerprint (unique per CI run).
pub fn build_fingerprint() -> &'static str {
    BUILD_HASH
}

/// Obfuscate a memory offset using the build hash as XOR seed.
pub fn obfuscate_offset(base: usize) -> usize {
    let seed = BUILD_HASH.bytes().take(8).fold(0usize, |acc, b| {
        acc.wrapping_mul(31).wrapping_add(b as usize)
    });
    base ^ (seed & 0xFF)
}

// ── Required security headers (documentation) ────────────────────────────────

/// CSP header value required to load WASM in the browser.
/// The server (Netlify / GitHub Pages + COI SW) MUST set these.
pub const CSP_HEADER: &str = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; \
     connect-src 'self' ws:; worker-src 'self' blob:;";

/// Headers required for SharedArrayBuffer (WASM multithreading).
pub const REQUIRED_SECURITY_HEADERS: &[(&str, &str)] = &[
    ("Cross-Origin-Opener-Policy", "same-origin"),
    ("Cross-Origin-Embedder-Policy", "require-corp"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "no-referrer"),
];

// ── Unit tests ────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    // ── validate_raw_log ──────────────────────────────────────────────────────

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

    // ── validate_metadata_key ─────────────────────────────────────────────────

    #[test]
    fn accepts_valid_keys() {
        assert!(validate_metadata_key("src_ip").is_ok());
        assert!(validate_metadata_key("windows-event-id").is_ok());
        assert!(validate_metadata_key("field01").is_ok());
    }

    #[test]
    fn rejects_key_with_spaces() {
        assert!(validate_metadata_key("key with spaces").is_err());
    }

    #[test]
    fn rejects_key_with_semicolon() {
        assert!(validate_metadata_key("key;inject").is_err());
    }

    #[test]
    fn rejects_empty_key() {
        assert!(validate_metadata_key("").is_err());
    }

    // ── SourceRateLimiter ─────────────────────────────────────────────────────

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
        // One more should be blocked
        assert!(matches!(
            rl.check_and_increment(src, now_ms),
            Err(SecurityError::RateLimitExceeded(_, _, _))
        ));
    }

    #[test]
    fn rate_limiter_resets_after_window() {
        let mut rl = SourceRateLimiter::new();
        let src = "10.0.0.1";
        let now_ms = 1_000_000u64;

        // Fill window
        for _ in 0..MAX_EVENTS_PER_SEC_PER_SOURCE {
            let _ = rl.check_and_increment(src, now_ms);
        }
        // 1 second later — should reset
        assert!(rl.check_and_increment(src, now_ms + 1_001).is_ok());
    }

    #[test]
    fn rate_limiter_gc_removes_stale() {
        let mut rl = SourceRateLimiter::new();
        let _ = rl.check_and_increment("old_source", 1_000_000);
        assert_eq!(rl.source_count(), 1);

        rl.gc(1_000_000 + 61_000); // 61 seconds later
        assert_eq!(rl.source_count(), 0);
    }

    // ── SharedBufferGuard ─────────────────────────────────────────────────────

    #[test]
    fn atomic_guard_locks_and_releases() {
        let guard = SharedBufferGuard::new();
        {
            let lock = guard.try_lock(10).expect("should acquire lock");
            assert!(lock.verify_integrity());
        } // lock dropped here — releases
          // Should be able to lock again
        let _ = guard.try_lock(10).expect("should re-acquire after release");
    }

    #[test]
    fn atomic_guard_increments_version() {
        let guard = SharedBufferGuard::new();
        assert_eq!(guard.current_version(), 0);
        {
            let _ = guard.try_lock(10);
        }
        assert_eq!(guard.current_version(), 1);
    }

    // ── Offset obfuscation ────────────────────────────────────────────────────

    #[test]
    fn obfuscate_offset_is_deterministic() {
        let a = obfuscate_offset(100);
        let b = obfuscate_offset(100);
        assert_eq!(a, b);
    }

    #[test]
    fn build_fingerprint_not_empty() {
        assert!(!build_fingerprint().is_empty());
    }
}
