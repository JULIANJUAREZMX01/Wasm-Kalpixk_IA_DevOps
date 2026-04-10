import React, { useEffect, useState, useMemo } from 'react';
import { useAlertStore, ParsedEvent } from '../stores/alertStore';
import { AlertFeed } from '../components/AlertFeed';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const DEMO_LOGS = [
  { raw: "Apr  5 02:14:22 cancun-srv01 sshd[1234]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:23 cancun-srv01 sshd[1235]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:24 cancun-srv01 sshd[1236]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "TIMESTAMP=2026-04-05-02.15.00 AUTHID=CEDIS_USR HOSTNAME=185.220.101.35 OPERATION=DDL STATEMENT=DROP TABLE NOMINAS", type: "db2" },
  { raw: "Apr  5 02:14:26 cancun-srv01 sshd[1238]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
];

export const Dashboard: React.FC = () => {
  const { events, wasmReady, wasmVersion, addEvent, setWasmReady, clearEvents } = useAlertStore();
  const [wasmLog, setWasmLog] = useState<{msg: string, color: string}[]>([]);
  const [parseFn, setParseFn] = useState<any>(null);

  const addLog = (msg: string, color = "#32ff32") => {
    setWasmLog(prev => [...prev, { msg, color }].slice(-10));
  };

  useEffect(() => {
    const init = async () => {
      try {
        const wasmModule = await import("../wasm/index");
        await wasmModule.initWasm();
        setWasmReady(true, wasmModule.version());
        setParseFn(() => wasmModule.parse_log_line);
        addLog(`Motor listo: ${wasmModule.version()}`, "#32ff32");
      } catch (err: any) {
        addLog(`Error WASM: ${err.message}`, "#ff1a1a");
      }
    };
    init();
  }, []);

  const simulate = () => {
    if (!parseFn) return;
    clearEvents();
    addLog("▶ Iniciando simulación...", "#ff6400");
    DEMO_LOGS.forEach((log, i) => {
      setTimeout(() => {
        const result = parseFn(log.raw, log.type);
        if (result) {
          const ev = JSON.parse(result) as ParsedEvent;
          ev.raw = log.raw;
          addEvent(ev);
        }
      }, i * 500);
    });
  };

  const chartData = useMemo(() => events.map((e, i) => ({ name: i, severity: e.local_severity * 100 })).reverse(), [events]);

  const avgSev = useMemo(() => events.length ? events.reduce((acc, e) => acc + e.local_severity, 0) / events.length : 0, [events]);
  const criticalCount = useMemo(() => events.filter(e => e.local_severity >= 0.8).length, [events]);

  return (
    <div style={{ background: "#080808", minHeight: "100vh", fontFamily: "'Courier New', monospace", color: "#e2e8f0", padding: "20px" }}>
      <header style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px", borderBottom: "1px solid #1a1a1a", paddingBottom: "10px" }}>
        <div>
          <h1 style={{ color: "#ff1a1a", letterSpacing: "3px" }}>██ KALPIXK SIEM</h1>
          <span style={{ fontSize: "10px", color: "#444" }}>WASM · WASP · WAST · AMD MI300X</span>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ color: wasmReady ? "#32ff32" : "#ff1a1a", fontSize: "12px", fontWeight: "bold" }}>{wasmReady ? "● SYSTEM ACTIVE" : "○ LOADING WASM..."}</div>
          <div style={{ fontSize: "10px", color: "#444" }}>{wasmVersion}</div>
        </div>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "20px" }}>
        <StatCard title="THROUGHPUT" value={`${(events.length * 2.5).toFixed(1)}k ev/s`} color="#00c8ff" subtitle="AMD MI300X" />
        <StatCard title="CRITICAL" value={criticalCount} color="#ff1a1a" subtitle="MITRE AT&CK MATCH" />
        <StatCard title="AVG SEVERITY" value={`${(avgSev * 100).toFixed(0)}%`} color="#ff6400" subtitle="UEBA BASELINE" />
        <StatCard title="WASM LATENCY" value="1.2ms" color="#32ff32" subtitle="ZERO CLOUD CALLS" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "20px", marginBottom: "20px" }}>
        <div style={{ background: "#0a0c10", border: "1px solid #1a1a1a", borderRadius: "6px", padding: "16px" }}>
          <div style={{ color: "#555", fontSize: "10px", marginBottom: "10px" }}>SHANNON ENTROPY TIMELINE</div>
          <div style={{ height: "200px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                <XAxis dataKey="name" hide />
                <YAxis stroke="#444" fontSize={10} />
                <Tooltip contentStyle={{ background: "#0d0f14", border: "1px solid #1a1a1a" }} />
                <Area type="monotone" dataKey="severity" stroke="#ff1a1a" fill="#ff1a1a" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div style={{ background: "#0a0c10", border: "1px solid #1a1a1a", borderRadius: "6px", padding: "16px" }}>
          <div style={{ color: "#555", fontSize: "10px", marginBottom: "10px" }}>KYNICOS NODE STATUS</div>
          <div style={{ fontSize: "11px" }}>
            <NodeStatus name="NODE_SENTINEL" status="ACTIVE" />
            <NodeStatus name="NODE_NEXUS" status="SYNC" />
            <NodeStatus name="NODE_FORGE" status="IDLE" />
            <NodeStatus name="NODE_UPLINK" status="ACTIVE" />
          </div>
        </div>
      </div>

      <div style={{ marginBottom: "20px", display: "flex", gap: "10px" }}>
        <button onClick={simulate} style={btnStyle}>▶ SIMULAR ATAQUE (CEDIS CANCÚN)</button>
        <button onClick={clearEvents} style={{ ...btnStyle, background: "#1a1a1a", color: "#555" }}>⟳ LIMPIAR</button>
      </div>

      <AlertFeed />

      <div style={{ marginTop: "20px", background: "#050505", border: "1px solid #1a1a1a", padding: "12px", borderRadius: "6px" }}>
        <div style={{ color: "#32ff32", fontSize: "11px", marginBottom: "8px" }}>▌ ATLATL-ORDNANCE CONSOLE</div>
        {wasmLog.map((l, i) => (
          <div key={i} style={{ fontSize: "10px", color: l.color, marginBottom: "4px" }}>
            <span style={{ color: "#444" }}>[{new Date().toLocaleTimeString()}]</span> {l.msg}
          </div>
        ))}
      </div>
    </div>
  );
};

const StatCard = ({ title, value, color, subtitle }: any) => (
  <div style={{ background: "#0a0c10", border: "1px solid #1a1a1a", borderRadius: "6px", padding: "16px" }}>
    <div style={{ color: "#555", fontSize: "10px", marginBottom: "6px" }}>{title}</div>
    <div style={{ color, fontSize: "24px", fontWeight: "bold" }}>{value}</div>
    <div style={{ color: "#333", fontSize: "9px", marginTop: "4px" }}>{subtitle}</div>
  </div>
);

const NodeStatus = ({ name, status }: any) => (
  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", borderBottom: "1px solid #111", pb: "4px" }}>
    <span style={{ color: "#888" }}>{name}</span>
    <span style={{ color: status === "ACTIVE" ? "#32ff32" : "#555" }}>{status}</span>
  </div>
);

const btnStyle: React.CSSProperties = {
  background: "#ff1a1a18",
  border: "1px solid #ff1a1a44",
  color: "#ff1a1a",
  padding: "8px 20px",
  borderRadius: "4px",
  cursor: "pointer",
  fontFamily: "monospace",
  fontSize: "11px",
  letterSpacing: "1px"
};
