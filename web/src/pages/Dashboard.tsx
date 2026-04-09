import React, { useEffect, useState } from 'react';
import { useAlertStore, ParsedEvent } from '../stores/alertStore';
import { AlertFeed } from '../components/AlertFeed';

const DEMO_LOGS = [
  { raw: "Apr  5 02:14:22 cancun-srv01 sshd[1234]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:23 cancun-srv01 sshd[1235]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:24 cancun-srv01 sshd[1236]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:25 cancun-srv01 sshd[1237]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "TIMESTAMP=2026-04-05-02.15.00 AUTHID=CEDIS_USR HOSTNAME=185.220.101.35 OPERATION=DDL STATEMENT=DROP TABLE NOMINAS", type: "db2" },
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

  const avgSev = events.length ? events.reduce((acc, e) => acc + e.local_severity, 0) / events.length : 0;

  return (
    <div style={{ background: "#080808", minHeight: "100vh", fontFamily: "'Courier New', monospace", color: "#e2e8f0", padding: "20px" }}>
      <header style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px", borderBottom: "1px solid #1a1a1a", paddingBottom: "10px" }}>
        <div>
          <h1 style={{ color: "#ff1a1a", letterSpacing: "3px" }}>██ KALPIXK SIEM</h1>
          <span style={{ fontSize: "10px", color: "#444" }}>WebAssembly · Zero Install · React</span>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ color: wasmReady ? "#32ff32" : "#ff1a1a", fontSize: "12px" }}>{wasmReady ? "CONECTADO" : "CARGANDO..."}</div>
          <div style={{ fontSize: "10px", color: "#444" }}>Motor: {wasmVersion}</div>
        </div>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "20px" }}>
        <StatCard title="EVENTOS" value={events.length} color="#00c8ff" />
        <StatCard title="CRÍTICOS" value={events.filter(e => e.local_severity >= 0.8).length} color="#ff1a1a" />
        <StatCard title="ALERTAS" value={events.filter(e => e.local_severity >= 0.5 && e.local_severity < 0.8).length} color="#ff6400" />
        <StatCard title="PROMEDIO" value={`${(avgSev * 100).toFixed(0)}%`} color="#32ff32" />
      </div>

      <div style={{ marginBottom: "20px" }}>
        <button onClick={simulate} style={btnStyle}>▶ SIMULAR ATAQUE</button>
        <button onClick={clearEvents} style={{ ...btnStyle, background: "#1a1a1a", color: "#555", marginLeft: "10px" }}>⟳ LIMPIAR</button>
      </div>

      <AlertFeed />

      <div style={{ marginTop: "20px", background: "#050505", border: "1px solid #1a1a1a", padding: "12px", borderRadius: "6px" }}>
        <div style={{ color: "#32ff32", fontSize: "11px", marginBottom: "8px" }}>▌ CONSOLA WASM</div>
        {wasmLog.map((l, i) => (
          <div key={i} style={{ fontSize: "10px", color: l.color, marginBottom: "4px" }}>
            <span style={{ color: "#444" }}>[{new Date().toLocaleTimeString()}]</span> {l.msg}
          </div>
        ))}
      </div>
    </div>
  );
};

const StatCard = ({ title, value, color }: { title: string, value: any, color: string }) => (
  <div style={{ background: "#0a0c10", border: "1px solid #1a1a1a", borderRadius: "6px", padding: "16px" }}>
    <div style={{ color: "#555", fontSize: "10px", marginBottom: "6px" }}>{title}</div>
    <div style={{ color, fontSize: "28px", fontWeight: "bold" }}>{value}</div>
  </div>
);

const btnStyle: React.CSSProperties = {
  background: "#ff1a1a18",
  border: "1px solid #ff1a1a44",
  color: "#ff1a1a",
  padding: "8px 16px",
  borderRadius: "4px",
  cursor: "pointer",
  fontFamily: "monospace",
  fontSize: "11px"
};
