use wasm_bindgen_test::*;
wasm_bindgen_test_configure!(run_in_browser);

fn parse_event(raw: &str, source: &str) -> serde_json::Value {
    let result = kalpixk_core::parse_log_line(raw, source)
        .unwrap_or_else(|| panic!("parse_log_line should succeed for source={}", source));
    serde_json::from_str(&result).expect("result should be valid JSON")
}

fn parse_batch(logs: &[&str], source: &str) -> serde_json::Value {
    let logs_json = serde_json::to_string(logs).unwrap();
    let result = kalpixk_core::process_batch(&logs_json, source);
    serde_json::from_str(&result).expect("batch result should be valid JSON")
}

#[wasm_bindgen_test]
fn syslog_brute_force_parsed() {
    let raw = "Apr 04 03:22:11 cedis-01 sshd[1234]: Failed password for root from 185.220.101.42 port 44321 ssh2";
    let event = parse_event(raw, "syslog");
    assert_eq!(event["event_type"], "login_failure");
    assert!(event["local_severity"].as_f64().unwrap() > 0.4);
    assert_eq!(event["source_type"], "syslog");
}

#[wasm_bindgen_test]
fn syslog_login_success_parsed() {
    let raw = "Apr 04 03:22:11 cedis-01 sshd[1234]: Accepted password for root from 192.168.1.100 port 44321 ssh2";
    let event = parse_event(raw, "syslog");
    assert_eq!(event["event_type"], "login_success");
    assert!(event["local_severity"].as_f64().unwrap() < 0.4);
}

#[wasm_bindgen_test]
fn batch_processing_works() {
    let logs = &["Apr 04 03:22:11 cedis sshd[1234]: Failed password for root from 185.220.101.42"];
    let batch = parse_batch(logs, "syslog");
    let features = batch["feature_matrix"][0]
        .as_array()
        .expect("feature_matrix[0] should be an array");
    assert_eq!(features.len(), 32);
}

#[wasm_bindgen_test]
fn features_in_range() {
    let sources = ["syslog", "db2", "windows", "netflow"];
    for &source in &sources {
        let logs = match source {
            "syslog" => vec!["Apr 04 03:22:11 host sshd[1]: Failed password for root from 1.1.1.1"],
            "db2" => vec!["TIMESTAMP=2026-04-01-00.00.00.000000 AUTHID=ADMIN HOSTNAME=H SQL=SELECT * FROM T SQLCODE=0 ROWS=1"],
            "windows" => vec!["EventID: 4624 Account Name: user Computer: C"],
            "netflow" => vec!["1.1.1.1 2.2.2.2 123 456 TCP 100 1"],
            _ => unreachable!(),
        };
        let batch = parse_batch(&logs, source);
        for row in batch["feature_matrix"].as_array().unwrap() {
            for v_val in row.as_array().unwrap() {
                let v = v_val.as_f64().unwrap();
                assert!((0.0..=1.0).contains(&v));
            }
        }
    }
}
