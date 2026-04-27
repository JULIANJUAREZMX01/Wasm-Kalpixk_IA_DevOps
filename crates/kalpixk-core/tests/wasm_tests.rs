// crates/kalpixk-core/tests/wasm_tests.rs
// ──────────────────────────────────────────
// WAST-style tests for the Kalpixk WASM engine.
// Run with: wasm-pack test crates/kalpixk-core --node --headless
//
// These tests verify:
//   1. Each parser produces structurally valid KalpixkEvent JSON
//   2. Feature vectors are exactly 32-dimensional and all in [0, 1]
//   3. Security validation rejects injection patterns
//   4. Anomaly hints are within [0, 1]
//   5. Batch processing handles edge cases without panics

use wasm_bindgen_test::*;
wasm_bindgen_test_configure!(run_in_browser);

// ── Helper: parse JSON result from parse_log_line ─────────────────────────────

fn parse_event(raw: &str, source: &str) -> serde_json::Value {
    let result = kalpixk_core::parse_log_line(raw, source).unwrap_or_else(|| {
        panic!("parse_log_line should succeed for source={}", source)
    });
    serde_json::from_str(&result).expect("result should be valid JSON")
}

fn parse_batch(logs: &[&str], source: &str) -> serde_json::Value {
    let json = serde_json::to_string(logs).unwrap();
    let result = kalpixk_core::process_batch(&json, source);
    serde_json::from_str(&result).expect("batch result should be valid JSON")
}

// ── SYSLOG PARSER ─────────────────────────────────────────────────────────────

#[wasm_bindgen_test]
fn syslog_brute_force_produces_login_failure() {
    let raw = "Apr 04 03:22:11 cedis-01 sshd[1234]: Failed password for root from 185.220.101.42 port 44321 ssh2";
    let event = parse_event(raw, "syslog");

    assert_eq!(
        event["event_type"], "login_failure",
        "SSH brute force must be classified as login_failure"
    );
    assert!(
        event["local_severity"].as_f64().unwrap() > 0.4,
        "SSH brute force severity should be > 0.4"
    );
    assert_eq!(event["source_type"], "syslog");
    assert!(!event["fingerprint"].as_str().unwrap().is_empty());
}

#[wasm_bindgen_test]
fn syslog_successful_login_low_severity() {
    let raw = "Apr 04 09:00:00 cedis-01 sshd[5678]: Accepted publickey for admin from 192.168.1.50 port 42312 ssh2";
    let event = parse_event(raw, "syslog");

    assert_eq!(event["event_type"], "login_success");
    assert!(
        event["local_severity"].as_f64().unwrap() < 0.4,
        "Normal login should have low severity"
    );
}

#[wasm_bindgen_test]
fn syslog_sudo_command_elevated_severity() {
    let raw = "Apr 04 02:45:12 cedis-01 sudo[13000]: www-data : COMMAND=/bin/bash";
    let event = parse_event(raw, "syslog");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.4,
        "sudo command should have elevated severity"
    );
}

#[wasm_bindgen_test]
fn syslog_user_creation_high_severity() {
    let raw = "Apr 04 02:00:00 cedis-01 useradd[999]: new user: name=backdoor";
    let event = parse_event(raw, "syslog");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.6,
        "User creation should have high severity"
    );
}

// ── DB2 PARSER ────────────────────────────────────────────────────────────────

#[wasm_bindgen_test]
fn db2_drop_table_critical_severity() {
    let raw = "TIMESTAMP=2026-04-08-02.17.00.000000 AUTHID=ROOT HOSTNAME=cedis_427 SQL=DROP TABLE WMS_USER SQLCODE=0 ROWS=0";
    let event = parse_event(raw, "db2");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.8,
        "DROP TABLE must have critical severity (got {})",
        event["local_severity"]
    );
    assert_eq!(event["source_type"], "db2");
}

#[wasm_bindgen_test]
fn db2_bulk_export_high_severity() {
    let raw = "TIMESTAMP=2026-04-08-02.17.00.000000 AUTHID=WMS_OPS HOSTNAME=cedis_427 SQL=EXPORT TO /tmp/data.csv OF DEL SELECT * FROM ORDER_HEADER SQLCODE=0 ROWS=24891";
    let event = parse_event(raw, "db2");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.6,
        "Bulk EXPORT should have high severity"
    );
}

#[wasm_bindgen_test]
fn db2_grant_elevated_severity() {
    let raw = "TIMESTAMP=2026-04-08-10.30.00.000000 AUTHID=WMS_OPS HOSTNAME=cedis_427 SQL=GRANT SELECT ON INVENTORY TO PUBLIC SQLCODE=0 ROWS=0";
    let event = parse_event(raw, "db2");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.6,
        "GRANT should have elevated severity"
    );
}

#[wasm_bindgen_test]
fn db2_normal_select_low_severity() {
    let raw = "TIMESTAMP=2026-04-08-10.30.00.000000 AUTHID=WMS_OPS HOSTNAME=cedis_427 SQL=SELECT LOC_ID, QTY FROM INVENTORY WHERE LOC_ID='A-01' SQLCODE=0 ROWS=5";
    let event = parse_event(raw, "db2");

    assert!(
        event["local_severity"].as_f64().unwrap() < 0.5,
        "Normal SELECT should have low severity"
    );
}

// ── WINDOWS EVENT LOG PARSER ──────────────────────────────────────────────────

#[wasm_bindgen_test]
fn windows_login_failure_4625() {
    let raw = "EventID: 4625 Account Name: administrator Computer: CEDIS-DC01";
    let event = parse_event(raw, "windows");

    assert!(event["local_severity"].as_f64().unwrap() > 0.4);
    assert_eq!(event["source_type"], "windows");
}

#[wasm_bindgen_test]
fn windows_privilege_escalation_4672() {
    let raw = "EventID: 4672 Account Name: svc_backdoor Computer: CEDIS-DC01";
    let event = parse_event(raw, "windows");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.7,
        "EventID 4672 (privilege escalation) should have high severity"
    );
}

#[wasm_bindgen_test]
fn windows_malicious_service_7045() {
    let raw = "EventID: 7045 Service Name: svc_backdoor Computer: CEDIS-DC01";
    let event = parse_event(raw, "windows");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.8,
        "New malicious service (7045) should have critical severity"
    );
}

// ── NETFLOW PARSER ────────────────────────────────────────────────────────────

#[wasm_bindgen_test]
fn netflow_high_risk_port_elevated() {
    // SSH port 22
    let raw = "185.220.101.42 10.0.0.1 54321 22 TCP 4096 12";
    let event = parse_event(raw, "netflow");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.4,
        "Netflow to port 22 should have elevated severity"
    );
}

#[wasm_bindgen_test]
fn netflow_large_transfer_anomalous() {
    // >100MB transfer — potential exfiltration
    let raw = "10.0.0.45 52.89.214.238 12345 443 TCP 200000000 5000";
    let event = parse_event(raw, "netflow");

    assert!(
        event["local_severity"].as_f64().unwrap() > 0.4,
        "Large data transfer should have elevated severity"
    );
}

// ── JSON STRUCTURED PARSER ────────────────────────────────────────────────────

#[wasm_bindgen_test]
fn json_login_failure_parsed() {
    let raw =
        r#"{"event_type":"login_failure","src_ip":"10.0.3.99","user":"admin","severity":0.7}"#;
    let event = parse_event(raw, "json");

    assert_eq!(event["event_type"], "login_failure");
    assert_eq!(event["source_type"], "json");
}

// ── FEATURE VECTOR CONTRACT ───────────────────────────────────────────────────

#[wasm_bindgen_test]
fn batch_produces_exactly_32_features() {
    let logs = &["Apr 04 03:22:11 cedis sshd[1234]: Failed password for root from 185.220.101.42"];
    let batch = parse_batch(logs, "syslog");

    let features = batch["feature_matrix"][0]
        .as_array()
        .expect("feature_matrix[0] should be an array");
    assert_eq!(
        features.len(),
        32,
        "Feature vector must be exactly 32-dimensional (contract with Python model)"
    );
}

#[wasm_bindgen_test]
fn all_features_in_unit_interval() {
    let logs = &[
        "Apr 04 03:22:11 cedis sshd[1234]: Failed password for root from 185.220.101.42",
        "TIMESTAMP=2026-04-08 AUTHID=ROOT HOSTNAME=cedis_427 SQL=DROP TABLE WMS_USER SQLCODE=0 ROWS=0",
        "EventID: 4672 Account Name: svc_backdoor Computer: CEDIS-DC01",
    ];

    for (log, source) in logs.iter().zip(&["syslog", "db2", "windows"]) {
        let batch = parse_batch(&[log], source);
        let features = batch["feature_matrix"][0].as_array().unwrap();

        for (i, f) in features.iter().enumerate() {
            let v = f.as_f64().expect("feature must be f64");
            assert!(
                (0.0..=1.0).contains(&v),
                "Feature[{}]={} out of [0,1] for log '{}' (source={})",
                i,
                v,
                log,
                source
            );
        }
    }
}

#[wasm_bindgen_test]
fn anomaly_hints_in_unit_interval() {
    let logs = &["Apr 04 03:22:11 cedis sshd[1234]: Failed password for root from 185.220.101.42"];
    let batch = parse_batch(logs, "syslog");

    let hints = batch["anomaly_hints"].as_array().unwrap();
    for h in hints {
        let v = h.as_f64().unwrap();
        assert!(
            (0.0..=1.0).contains(&v),
            "anomaly_hint={} must be in [0, 1]",
            v
        );
    }
}

// ── BATCH EDGE CASES ─────────────────────────────────────────────────────────

#[wasm_bindgen_test]
fn empty_batch_returns_zero_events() {
    let batch = parse_batch(&[], "syslog");
    assert_eq!(batch["parsed_count"].as_u64().unwrap(), 0);
    assert_eq!(batch["total_count"].as_u64().unwrap(), 0);
}

#[wasm_bindgen_test]
fn batch_with_empty_lines_skips_gracefully() {
    let logs = &[
        "",
        "   ",
        "Apr 04 09:00:00 host sshd[1]: Accepted publickey for user from 192.168.1.1",
    ];
    let batch = parse_batch(logs, "syslog");

    // Should parse 1 valid event, skip 2 empty lines
    let parsed = batch["parsed_count"].as_u64().unwrap();
    assert!(parsed <= 1, "Empty lines should be skipped");
}

#[wasm_bindgen_test]
fn batch_counts_match() {
    let logs = &[
        "Apr 04 09:00:00 host sshd[1]: Accepted publickey for admin from 192.168.1.50",
        "Apr 04 09:00:01 host sshd[2]: Failed password for root from 185.220.101.42",
        "Apr 04 09:00:02 host sshd[3]: Failed password for root from 185.220.101.42",
    ];
    let batch = parse_batch(logs, "syslog");

    assert_eq!(batch["total_count"].as_u64().unwrap(), 3);
    let parsed = batch["parsed_count"].as_u64().unwrap();
    assert!((1..=3).contains(&parsed));
}

// ── SECURITY VALIDATION ───────────────────────────────────────────────────────

#[wasm_bindgen_test]
fn null_byte_injection_does_not_panic() {
    // Must not panic — may return None or a sanitized event
    let result = std::panic::catch_unwind(|| {
        kalpixk_core::parse_log_line("normal log\x00injected", "syslog")
    });
    assert!(result.is_ok(), "null byte injection must not cause panic");
}

#[wasm_bindgen_test]
fn oversized_log_does_not_panic() {
    let huge = "a".repeat(100_000);
    let result = std::panic::catch_unwind(|| kalpixk_core::parse_log_line(&huge, "syslog"));
    assert!(result.is_ok(), "oversized log must not cause panic");
    // Should return None (rejected) rather than crashing
    let parsed = kalpixk_core::parse_log_line(&huge, "syslog");
    assert!(parsed.is_none(), "oversized log should be rejected (None)");
}

// ── VERSION ───────────────────────────────────────────────────────────────────

#[wasm_bindgen_test]
fn version_returns_semver_string() {
    let v = kalpixk_core::version();
    assert!(!v.is_empty());
    // Should look like "0.1.0"
    let parts: Vec<&str> = v.split('.').collect();
    assert_eq!(parts.len(), 3, "Version should be semver: {}", v);
}
