# WASM Defense Protocols — Kalpixk Zero Trust Architecture

## Severity Classification

| Level    | Score Range | Action                              |
|----------|-------------|-------------------------------------|
| CLEAN    | 0 – 10      | Pass — normal WASM execution        |
| SUSPICIOUS | 10 – 50   | Flag + log — continuous monitoring  |
| ANOMALY  | 50 – 100    | Quarantine + Blue Team alert        |
| CRITICAL | 100+        | SYSTEM_LOCKDOWN — block + full report |

## Defense Nodes

### Node Alpha — Static Analysis
- Bytecode signature validation
- Import/export table inspection
- Memory layout anomaly detection
- Source: Rust parser → wasm32-wasip1

### Node Beta — Dynamic Feature Extraction
10-vector feature space per WASM module:
1. instruction_entropy
2. memory_access_density
3. import_count_normalized
4. export_count_normalized
5. control_flow_complexity
6. call_depth_max
7. data_segment_ratio
8. linear_memory_size
9. table_element_count
10. custom_section_presence

### Node Gamma — AMD ROCm ML Engine
- Primary: Autoencoder (reconstruction error = anomaly score)
- Baseline: Isolation Forest
- Temporal: LSTM for sequential log analysis
- Hardware: AMD MI300X — 205.8GB HBM3 VRAM — ROCm 7.0

### Node Delta — Response Orchestration
- FastAPI /analyze endpoint
- Real-time Streamlit dashboard
- Alert pipeline → email/webhook
- SAC/Manhattan WMS integration

## Protocol: WASM_LOCKDOWN

Triggered when anomaly_score > 100:
```
1. Block WASM module execution
2. Capture full bytecode snapshot
3. Generate forensic report
4. Alert Blue Team via API
5. Log to persistent store (Supabase)
6. Flag source IP/origin
```

## Real-World Integration: SAC/Manhattan WMS

WMS system generates WASM-adjacent log patterns that map to the 10-vector space:
- Transaction anomalies → instruction_entropy spike
- Auth violations → import_count_normalized outlier
- Data exfiltration patterns → memory_access_density surge

This is the production use case no other hackathon team has.

## Benchmark Target (Week 1)

| Method           | Time/batch | Speedup |
|------------------|------------|---------|
| CPU Python pure  | TBD        | 1x      |
| AMD MI300X ROCm  | TBD        | **?x**  |

*First run confirmed: Anomaly score 102.3110 on cuda:0*
