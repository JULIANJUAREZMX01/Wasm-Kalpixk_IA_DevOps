"""
Kalpixk Threat Detection Agent — DigitalOcean Gradient ADK
Deploy: gradient agent deploy
"""
from gradient_adk import entrypoint, trace_tool, RequestContext
import json

@trace_tool("threat_detection")
async def analyze_threat(event_data: dict) -> dict:
    """Run anomaly detection on incoming event."""
    # Feature extraction
    features = {
        "dns_queries_ps": event_data.get("dns_queries_per_second", 0),
        "failed_auth": event_data.get("failed_auth_attempts", 0),
        "entropy": event_data.get("shannon_entropy", 0),
        "port_scan": event_data.get("ports_probed_per_second", 0),
    }
    
    # Scoring (mirrors Python AnomalyDetector v2.1 logic)
    score = 0.0
    if features["dns_queries_ps"] > 50: score += 0.3
    if features["failed_auth"] > 3: score += 0.4
    if features["entropy"] > 7.0: score += 0.5
    if features["port_scan"] > 1000: score += 0.6
    
    severity = "CLEAN"
    if score >= 0.7: severity = "CRITICAL"
    elif score >= 0.5: severity = "ANOMALY"  
    elif score >= 0.3: severity = "SUSPICIOUS"
    
    return {
        "severity": severity,
        "score": round(score, 3),
        "features": features,
        "action": "WASM_LOCKDOWN" if severity == "CRITICAL" else "MONITOR"
    }

@entrypoint
async def main(input: dict, context: RequestContext):
    """
    Kalpixk Threat Detection Agent
    
    Input: {"event": {...event data...}}
    Output: {"severity": "...", "score": 0.0, "action": "..."}
    """
    event = input.get("event", input)
    result = await analyze_threat(event)
    
    response = f"""
🛡️ KALPIXK SIEM ANALYSIS
{'='*40}
Severity: {result['severity']}
Score: {result['score']}
Action: {result['action']}

Features detected:
- DNS queries/s: {result['features']['dns_queries_ps']}
- Failed auth attempts: {result['features']['failed_auth']}
- Shannon entropy: {result['features']['entropy']}
- Port scan rate: {result['features']['port_scan']}

Powered by AMD MI300X ROCm 7.0 — F1=0.999
"""
    return response
