use kalpixk_core::defense_nodes::{analyze_all_nodes, set_expected_binary_hash};
use kalpixk_core::event::{KalpixkEvent, EventType};
use std::collections::HashMap;

#[test]
fn test_node_9_mesh_auth_fail() {
    let mut metadata = HashMap::new();
    metadata.insert("challenge".to_string(), serde_json::json!(12345));
    metadata.insert("response".to_string(), serde_json::json!(67890)); // Wrong response

    let event = KalpixkEvent {
        source_type: "mesh_sync".to_string(),
        source: "malicious_node".to_string(),
        metadata,
        ..Default::default()
    };

    let results = analyze_all_nodes(&event);
    let n9 = results.iter().find(|r| r.node == "NODE-9: MESH_AUTH").unwrap();
    assert_eq!(n9.score, 1.0);
}

#[test]
fn test_node_10_integrity_fail() {
    set_expected_binary_hash(0xABCDEF);

    let mut metadata = HashMap::new();
    metadata.insert("binary_hash".to_string(), serde_json::json!(0x123456)); // Mismatch

    let event = KalpixkEvent {
        source_type: "integrity_check".to_string(),
        source: "wasm_self".to_string(),
        metadata,
        ..Default::default()
    };

    let results = analyze_all_nodes(&event);
    let n10 = results.iter().find(|r| r.node == "NODE-10: INTEGRITY").unwrap();
    assert_eq!(n10.score, 1.0);
}
