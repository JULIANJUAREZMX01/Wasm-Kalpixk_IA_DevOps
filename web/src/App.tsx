import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import { useAlertStore, type KalpixkAlert } from "./stores/alertStore";
import { useMetricsStore } from "./stores/metricsStore";

// ── Demo data ────────────────────────────────────────────────────────────────
const THREAT_POOL: Omit<KalpixkAlert, "id" | "ts">[] = [
  { ip: "185.220.101.42", geo: "RU", msg: "SSH Brute Force — 847 attempts/min → CEDIS-SSH-01", score: 0.91, src: "syslog", eventType: "LoginFailure" },
  { ip: "45.142.212.15",  geo: "CN", msg: "SQL Injection — WMS_USER payload UNION SELECT detected", score: 0.95, src: "db2",    eventType: "DbAnomalousQuery" },
  { ip: "10.0.0.105",     geo: "LAN", msg: "Lateral movement — CEDIS Floor 2 → Server Room", score: 0.78, src: "netflow", eventType: "LateralMovement" },
  { ip: "103.21.244.0",   geo: "TH",  msg: "SYN scan — 1,024 ports in 3 seconds", score: 0.67, src: "netflow", eventType: "NetworkScan" },
  { ip: "10.0.0.45",      geo: "LAN", msg: "DB2 EXPORT — ORDER_HEADER 2.4 GB — 02:17 off-hours", score: 0.86, src: "db2",    eventType: "BulkDataOp" },
  { ip: "52.89.214.238",  geo: "AWS", msg: "C2 Beacon — exact 300s interval, low entropy", score: 0.88, src: "netflow", eventType: "C2Beacon" },
  { ip: "91.108.4.0",     geo: "NL",  msg: "Credential stuffing — 2,300 WMS accounts in 8 min", score: 0.74, src: "syslog",  eventType: "CredStuffing" },
  { ip: "172.16.3.201",   geo: "LAN", msg: "sudo -i from WMS operator — 03:45 — unauthorized", score: 0.92, src: "syslog",  eventType: "PrivEsc" },
  { ip: "10.10.1.88",     geo: "LAN", msg: "GRANT SELECT ON INVENTORY TO PUBLIC", score: 0.82, src: "db2",    eventType: "PolicyChange" },
  { ip: "178.62.21.7",    geo: "UK",  msg: "RDP timing attack — EventID 4625 × 340 attempts", score: 0.69, src: "windows", eventType: "BruteForce" },
  { ip: "10.0.3.77",      geo: "LAN", msg: "New service installed — EventID 7045 — svc_backdoor", score: 0.97, src: "windows", eventType: "ServiceInstall" },
  { ip: "104.21.44.11",   geo: "CF",  msg: "HTTP recon — admin path enumeration", score: 0.58, src: "json",   eventType: "Recon" },
  { ip: "192.168.1.200",  geo: "LAN", msg: "MI300X Tensor Poisoning — malicious weight injection", score: 0.99, src: "rocm",    eventType: "ModelTampering" },
  { ip: "10.0.5.15",      geo: "LAN", msg: "WASM SharedBuffer Tampering — race condition detected", score: 0.96, src: "wasm",    eventType: "MemoryExploit" },
];

let _idCounter = 0;

export default function App() {
  const addAlert       = useAlertStore((s) => s.addAlert);
  const updateMetrics  = useMetricsStore((s) => s.updateMetrics);

  // Seed initial alerts
  useEffect(() => {
    const initial = [...THREAT_POOL]
      .sort(() => Math.random() - 0.5)
      .slice(0, 10)
      .map((t) => ({
        ...t,
        id:    ++_idCounter,
        ts:    new Date(Date.now() - _idCounter * 8000),
        score: Math.min(0.99, t.score + (Math.random() - 0.5) * 0.05),
      }));
    initial.forEach((a) => addAlert(a));
  }, []); // eslint-disable-line

  // Live simulation
  useEffect(() => {
    const interval = setInterval(() => {
      const tmpl  = THREAT_POOL[Math.floor(Math.random() * THREAT_POOL.length)];
      const score = Math.min(0.99, tmpl.score + (Math.random() - 0.5) * 0.1);
      addAlert({ ...tmpl, id: ++_idCounter, ts: new Date(), score });
      updateMetrics({
        gpuLatencyMs: Math.floor(Math.random() * 18) + 26,
        gpuLoadPct:   Math.floor(Math.random() * 30) + 25,
        fpRate:       +(Math.random() * 1.5 + 1.5).toFixed(1),
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []); // eslint-disable-line

  return <Dashboard />;
}
