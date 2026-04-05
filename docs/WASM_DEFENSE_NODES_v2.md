# 🛡️ Kalpixk — WASM Defense Nodes v2
## RedTeam-Tools Integration Map

> Fuente: A-poc/RedTeam-Tools (150+ técnicas) → mapeadas a nodos de detección WASM  
> Arquitectura: 4 nodos de defensa + tabla de severidad + protocolo WASM_LOCKDOWN  
> Motor: AnomalyDetector v2.1 — IsolationForest(0.45) + Autoencoder(0.55) — F1=0.999

---

## Node Architecture

```
EDGE LAYER (WASM — corre en browser)
┌─────────────────────────────────────────────────────┐
│  NODE-1: Reconnaissance Detector                    │
│  NODE-2: Lateral Movement Detector                  │
│  NODE-3: Credential Theft Detector                  │
│  NODE-4: Payload/Execution Detector                 │
│          ↓ MessagePack WebSocket (95% < JSON)       │
└─────────────────────────────────────────────────────┘
          ↓
CLOUD LAYER (Python + AMD MI300X)
┌─────────────────────────────────────────────────────┐
│  AnomalyDetector v2.1                               │
│  4,216,327 eventos/seg — 3.6x vs CPU                │
│  F1=0.999 — ROC-AUC=0.9998                         │
└─────────────────────────────────────────────────────┘
```

---

## NODE-1: Reconnaissance Detector
**MITRE ATT&CK:** TA0043  
**RedTeam Sources:** spiderfoot, reconftw, subzy, nuclei, gobuster, feroxbuster, Shodan, dnsrecon, enum4linux

### Signatures (Rust WASM — features to detect)
```rust
// features.rs additions
pub fn detect_recon(event: &Event) -> SeverityScore {
    let mut score = 0.0f32;
    
    // DNS enumeration burst (dnsrecon pattern)
    if event.dns_queries_per_second > 50.0 { score += 0.3; }
    
    // Subdomain enumeration (reconftw/subzy)
    if event.unique_subdomains_probed > 100 { score += 0.4; }
    
    // Port scan signature (skanuvaty pattern)
    if event.ports_probed_per_second > 1000.0 { score += 0.5; }
    
    // Certificate transparency abuse
    if event.cert_transparency_queries > 20 { score += 0.2; }
    
    // OSINT tool signatures (user-agent patterns)
    if event.user_agent_matches_scanner { score += 0.6; }
    
    SeverityScore::from(score)
}
```

### Severity Mapping
| Score | Severity | Action |
|-------|----------|--------|
| < 0.3 | CLEAN | Log only |
| 0.3-0.5 | SUSPICIOUS | Alert + rate-limit |
| 0.5-0.7 | ANOMALY | Block + Telegram alert |
| > 0.7 | CRITICAL | WASM_LOCKDOWN |

---

## NODE-2: Lateral Movement Detector
**MITRE ATT&CK:** TA0008  
**RedTeam Sources:** evil-winrm, secretsdump, Responder, Rubeus, PowerSploit, impacket

### Signatures
```rust
pub fn detect_lateral_movement(event: &Event) -> SeverityScore {
    let mut score = 0.0f32;
    
    // WinRM activity (evil-winrm)
    if event.port == 5985 || event.port == 5986 { score += 0.4; }
    
    // NTLM hash relay (Responder)
    if event.protocol == "LLMNR" || event.protocol == "NBT-NS" { score += 0.7; }
    
    // Kerberos ticket abuse (Rubeus)
    if event.kerberos_anomaly { score += 0.8; }
    
    // SMB lateral movement
    if event.smb_new_connections_burst > 10 { score += 0.5; }
    
    // Remote code execution patterns (secretsdump)
    if event.registry_remote_access { score += 0.6; }
    
    SeverityScore::from(score)
}
```

---

## NODE-3: Credential Theft Detector  
**MITRE ATT&CK:** TA0006  
**RedTeam Sources:** mimikatz, LaZagne, CredMaster, TREVORspray, WordSteal, truffleHog

### Signatures
```rust
pub fn detect_credential_theft(event: &Event) -> SeverityScore {
    let mut score = 0.0f32;
    
    // Password spraying (CredMaster/TREVORspray)
    if event.failed_auth_attempts_per_account > 3 
       && event.unique_accounts_targeted > 10 { score += 0.7; }
    
    // LSASS memory access (mimikatz pattern)
    if event.lsass_memory_access { score += 0.9; }
    
    // GitHub secret exposure (truffleHog pattern)
    if event.high_entropy_string_in_commit { score += 0.5; }
    
    // OAuth/QR phishing (SquarePhish)
    if event.oauth_unusual_app_grant { score += 0.6; }
    
    // NTLM hash theft via Word doc (WordSteal)
    if event.smb_triggered_by_office_doc { score += 0.8; }
    
    SeverityScore::from(score)
}
```

---

## NODE-4: Payload/Execution Detector
**MITRE ATT&CK:** TA0002  
**RedTeam Sources:** msfvenom, Shellter, Freeze, Donut, macro_pack, Chimera, StarFighters

### Signatures
```rust
pub fn detect_payload_execution(event: &Event) -> SeverityScore {
    let mut score = 0.0f32;
    
    // In-memory .NET execution (Donut)
    if event.in_memory_assembly_load { score += 0.8; }
    
    // PowerShell obfuscation (Chimera)
    if event.powershell_entropy > 5.5 { score += 0.6; }
    
    // Shellcode injection (Shellter/Freeze)
    if event.process_memory_write_to_foreign_process { score += 0.9; }
    
    // HTML smuggling (mouse-move eventlistener)
    if event.html_blob_download_on_mouse_event { score += 0.7; }
    
    // AppLocker bypass patterns
    if event.applocker_bypass_technique_detected { score += 0.85; }
    
    // VBA macro with network activity (OffensiveVBA)
    if event.office_macro_network_call { score += 0.75; }
    
    SeverityScore::from(score)
}
```

---

## WASM_LOCKDOWN Protocol
**Trigger:** Any node score > 0.7 (CRITICAL)

```rust
// lib.rs — exposed to JavaScript via wasm-bindgen
#[wasm_bindgen]
pub fn wasm_lockdown(node_id: u8, score: f32, event_json: &str) -> LockdownResponse {
    LockdownResponse {
        action: "BLOCK",
        notify_channel: "telegram",  // → @KalpixkAI_bot
        mitre_technique: map_to_mitre(node_id, score),
        severity: Severity::Critical,
        timestamp_unix: js_sys::Date::now() as u64,
        event_fingerprint: sha256_first8(event_json),
    }
}
```

### Response Chain
```
WASM_LOCKDOWN triggered
    ↓
MessagePack WebSocket → FastAPI (Python)
    ↓
AnomalyDetector v2.1 (AMD MI300X) — deep validation
    ↓
Telegram alert → @KalpixkAI_bot
    ↓ (if confirmed)
Block rule pushed to edge
```

---

## Severity Table (consolidated — all 4 nodes)

| Level | Score | Color | Response | SLA |
|-------|-------|-------|----------|-----|
| CLEAN | 0.0-0.29 | 🟢 | Log | none |
| SUSPICIOUS | 0.30-0.49 | 🟡 | Alert + rate-limit | 60s |
| ANOMALY | 0.50-0.69 | 🔴 | Block + Telegram | 10s |
| CRITICAL | 0.70-1.0 | ⚫ | WASM_LOCKDOWN | immediate |

---

## Integration into Existing Rust Crate

Add to `crates/kalpixk-core/src/lib.rs`:
```rust
mod defense_nodes;
use defense_nodes::{detect_recon, detect_lateral_movement, detect_credential_theft, detect_payload_execution};

#[wasm_bindgen]
pub fn analyze_event(event_json: &str) -> JsValue {
    let event: Event = serde_json::from_str(event_json).unwrap_or_default();
    
    let scores = [
        ("recon", detect_recon(&event)),
        ("lateral", detect_lateral_movement(&event)),
        ("credential", detect_credential_theft(&event)),
        ("payload", detect_payload_execution(&event)),
    ];
    
    let max_score = scores.iter().map(|(_, s)| s.value).fold(0.0f32, f32::max);
    let triggered_node = scores.iter().max_by(|a, b| a.1.value.partial_cmp(&b.1.value).unwrap());
    
    if max_score > 0.7 {
        let lockdown = wasm_lockdown(triggered_node.unwrap().0, max_score, event_json);
        return serde_wasm_bindgen::to_value(&lockdown).unwrap();
    }
    
    serde_wasm_bindgen::to_value(&AnalysisResult { 
        severity: Severity::from_score(max_score),
        scores,
        timestamp: js_sys::Date::now() as u64,
    }).unwrap()
}
```

---

## Files to create in repo

```
crates/kalpixk-core/src/
├── lib.rs          (update: add analyze_event, wasm_lockdown)  
├── parsers.rs      (existing — parse raw events)
├── features.rs     (existing — Shannon entropy, etc.)
├── defense_nodes.rs  ← NEW — the 4 node functions above
└── severity.rs     ← NEW — SeverityScore, Severity enum, MITRE mapping
```

---

*v2.0 — April 5, 2026 — Kalpixk × RedTeam-Tools integration*  
*RedTeam source: https://github.com/A-poc/RedTeam-Tools (150+ techniques catalogued)*
