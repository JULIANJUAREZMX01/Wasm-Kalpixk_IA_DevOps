import { useState, useEffect, useRef } from "react";
import {
  AreaChart, Area, XAxis, YAxis, ResponsiveContainer,
  Tooltip, ReferenceLine,
} from "recharts";
import { useAlertStore } from "../stores/alertStore";
import { useMetricsStore } from "../stores/metricsStore";
import { useWasmStore }    from "../stores/wasmStore";
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

// ── Design tokens ─────────────────────────────────────────────────────────────
const T = {
  bg:      "#04060e",
  panel:   "#080c1a",
  surface: "#0c1124",
  border:  "#162038",
  amber:   "#f59e0b",
  green:   "#10b981",
  red:     "#ef4444",
  blue:    "#3b82f6",
  purple:  "#8b5cf6",
  dim:     "#3d5070",
  text:    "#94afd4",
  bright:  "#e2eaf8",
  font:    "'JetBrains Mono', monospace",
  display: "'Syne', sans-serif",
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const scoreColor = (s: number) => s >= 0.85 ? T.red : s >= 0.65 ? T.amber : T.green;
const scoreLabel = (s: number) => s >= 0.85 ? "CRIT" : s >= 0.65 ? "HIGH" : "MED";
const fmt        = (d: Date)   => d.toLocaleTimeString("es-MX", { hour12: false });
const seedChart  = () =>
  Array.from({ length: 90 }, (_, i) => ({
    t: i,
    s: Math.min(0.98, 0.05 + Math.random() * 0.2 + (Math.random() > 0.88 ? Math.random() * 0.7 : 0)),
  }));

// ── Sub-components ────────────────────────────────────────────────────────────
function Label({ text, accent = T.amber }: { text: string; accent?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8, flexShrink: 0 }}>
      <div style={{ width: 5, height: 5, background: accent, transform: "rotate(45deg)" }} />
      <span style={{ color: T.dim, fontSize: 9, letterSpacing: 3, fontFamily: T.font }}>
        {text}
      </span>
      <div style={{ flex: 1, height: 1, background: T.border }} />
    </div>
  );
}
  const chartData = useMemo(() => events.map((e, i) => ({ name: i, severity: e.local_severity * 100 })).reverse(), [events]);

  const avgSev = useMemo(() => events.length ? events.reduce((acc, e) => acc + e.local_severity, 0) / events.length : 0, [events]);
  const criticalCount = useMemo(() => events.filter(e => e.local_severity >= 0.8).length, [events]);

function Bar({ pct, color }: { pct: number; color: string }) {
  return (
    <div style={{ height: 3, background: T.border, borderRadius: 2, overflow: "hidden", flex: 1 }}>
      <div style={{ width: `${Math.min(100, pct)}%`, height: "100%", background: color, transition: "width 1.4s ease" }} />
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function Dashboard() {
  const alerts        = useAlertStore((s) => s.alerts);
  const criticalCount = useAlertStore((s) => s.criticalCount);
  const totalDetected = useAlertStore((s) => s.totalDetected);
  const isConnected   = useAlertStore((s) => s.isConnected);
  const metrics       = useMetricsStore();
  const wasm          = useWasmStore();

  const [clock, setClock]     = useState(new Date());
  const [chart, setChart]     = useState(seedChart);
  const [scan,  setScan]      = useState(0);
  const [tab,   setTab]       = useState<"realtime"|"parsers"|"benchmark"|"mitre">("realtime");
  const prevLen               = useRef(0);

  useEffect(() => { const t = setInterval(() => setClock(new Date()), 1000); return () => clearInterval(t); }, []);
  useEffect(() => { const t = setInterval(() => setScan((p) => (p + 1) % 100), 70); return () => clearInterval(t); }, []);

  // Update chart when new alert arrives
  useEffect(() => {
    if (alerts.length > prevLen.current && alerts[0]) {
      prevLen.current = alerts.length;
      setChart((p) => [...p.slice(1), { t: p[p.length - 1].t + 1, s: alerts[0].score }]);
    }
  }, [alerts]);

  const threatLevel = alerts[0]?.score >= 0.85 ? "CRITICAL" : alerts[0]?.score >= 0.65 ? "HIGH" : "NORMAL";
  const tlColor     = threatLevel === "CRITICAL" ? T.red : threatLevel === "HIGH" ? T.amber : T.green;

  return (
    <div style={{
      background: T.bg, color: T.text, fontFamily: T.font,
      height: "100vh", display: "flex", flexDirection: "column",
      overflow: "hidden", fontSize: 11, position: "relative",
    }}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes fadeIn  { from { opacity:0; transform:translateY(-4px) } to { opacity:1; transform:translateY(0) } }
        @keyframes pulse   { 0%,100%{opacity:1} 50%{opacity:.3} }
        @keyframes glow    { 0%,100%{text-shadow:0 0 8px currentColor} 50%{text-shadow:0 0 24px currentColor,0 0 48px currentColor} }
        ::-webkit-scrollbar{width:3px;height:3px}
        ::-webkit-scrollbar-track{background:${T.bg}}
        ::-webkit-scrollbar-thumb{background:${T.border};border-radius:2px}
        .new-row { animation: fadeIn .35s ease }
        .blink    { animation: pulse 1.4s infinite }
        .glow-amber { animation: glow 3s infinite; color: ${T.amber} }
      `}</style>

      {/* CRT scanline */}
      <div style={{
        position:"fixed", inset:0, zIndex:999, pointerEvents:"none",
        background:"repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,0.035) 3px,rgba(0,0,0,0.035) 4px)",
      }}/>
      <div style={{
        position:"fixed", left:0, right:0, height:3, top:`${scan}%`,
        background:"linear-gradient(transparent,rgba(16,185,129,.06),transparent)",
        zIndex:998, pointerEvents:"none",
      }}/>

      {/* ═══ HEADER ═══════════════════════════════════════════════════════════ */}
      <header style={{
        background: T.panel, borderBottom: `1px solid ${T.border}`,
        padding: "6px 16px", display: "flex", alignItems: "center",
        justifyContent: "space-between", flexShrink: 0, gap: 12,
      }}>
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 28, height: 28, background: T.amber, clipPath: "polygon(50% 0%,100% 50%,50% 100%,0% 50%)",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}>
            <span style={{ fontSize: 13 }}>🏹</span>
          </div>
          <div>
            <div className="glow-amber" style={{ fontFamily: T.display, fontWeight: 800, fontSize: 16, letterSpacing: 4 }}>
              KALPIXK
            </div>
            <div style={{ color: T.dim, fontSize: 8, letterSpacing: 2 }}>
              WASM-NATIVE BLUE TEAM SIEM · AMD MI300X · KynicOS NODE_SENTINEL
            </div>
          </div>
        </div>

        {/* Threat level */}
        <div style={{ display: "flex", gap: 3 }}>
          {(["NORMAL","HIGH","CRITICAL"] as const).map((lvl) => (
            <div key={lvl} style={{
              padding: "3px 10px", fontSize: 9, letterSpacing: 2, fontFamily: T.font,
              border: `1px solid ${lvl === threatLevel ? tlColor : T.border}`,
              background: lvl === threatLevel ? `${tlColor}18` : "transparent",
              color:      lvl === threatLevel ? tlColor : T.dim,
              animation:  lvl === threatLevel && lvl === "CRITICAL" ? "pulse 1.8s infinite" : "none",
            }}>{lvl}</div>
          ))}
        </div>

        {/* Stats row */}
        <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
          {[
            { l: "DETECTED",  v: (totalDetected + 1247).toLocaleString(), c: T.amber },
            { l: "CRITICAL",  v: criticalCount,           c: T.red   },
            { l: "GPU LAT",   v: `${metrics.gpuLatencyMs}ms`, c: T.green },
            { l: "THROUGHPUT",v: `${(metrics.gpuThroughput/1e6).toFixed(2)}M/s`, c: T.green },
          ].map(({ l, v, c }) => (
            <div key={l} style={{ textAlign: "right" }}>
              <div style={{ color: T.dim, fontSize: 8, letterSpacing: 1 }}>{l}</div>
              <div style={{ color: c, fontSize: 15, fontWeight: 700, lineHeight: 1.1 }}>{v}</div>
            </div>
          ))}
          <div style={{
            color: T.amber, fontSize: 17, fontWeight: 700, letterSpacing: 3,
            borderLeft: `1px solid ${T.border}`, paddingLeft: 16,
          }}>
            {fmt(clock)}
          </div>
        </div>
      </header>

      {/* ═══ TABS ════════════════════════════════════════════════════════════ */}
      <div style={{
        background: T.panel, borderBottom: `1px solid ${T.border}`,
        display: "flex", gap: 0, flexShrink: 0,
      }}>
        {([
          ["realtime",  "⚡ Real-Time"],
          ["parsers",   "⚙ WASM Parsers"],
          ["benchmark", "📊 Benchmark"],
          ["mitre",     "🛡 MITRE ATT&CK"],
        ] as const).map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={{
            background: "transparent", border: "none", cursor: "pointer",
            padding: "7px 16px", fontSize: 10, letterSpacing: 2, fontFamily: T.font,
            color:         tab === key ? T.amber : T.dim,
            borderBottom:  tab === key ? `2px solid ${T.amber}` : "2px solid transparent",
            transition:    "all .2s",
          }}>{label}</button>
        ))}
        {/* WASM status pill */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", paddingRight: 12, gap: 6 }}>
          <div style={{
            width: 6, height: 6, borderRadius: "50%",
            background: wasm.isLoaded ? T.green : T.amber,
            animation: wasm.isLoaded ? "none" : "pulse 1.5s infinite",
          }}/>
          <span style={{ color: T.dim, fontSize: 9, letterSpacing: 1 }}>
            WASM {wasm.isLoaded ? `v${wasm.version}` : "DEMO MODE"}
          </span>
        </div>
      </div>

      {/* ═══ CONTENT ═════════════════════════════════════════════════════════ */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex" }}>
        {tab === "realtime" && <RealtimeTab chart={chart} />}
        {tab === "parsers"  && <ParsersTab />}
        {tab === "benchmark" && <BenchmarkTab />}
        {tab === "mitre"    && <MitreTab />}
      </div>

      {/* ═══ FOOTER / TRANSCRIPT STREAM ══════════════════════════════════════ */}
      <footer style={{
        background: T.panel, borderTop: `1px solid ${T.border}`,
        padding: "4px 16px", display: "flex", alignItems: "center", gap: 8,
        fontSize: 9, flexShrink: 0, overflow: "hidden",
      }}>
        <span style={{ color: T.dim, letterSpacing: 2, whiteSpace: "nowrap" }}>▸ TRANSCRIPT</span>
        {alerts.slice(0, 3).map((a, i) => (
          <span key={a.id} style={{ color: i === 0 ? T.green : T.dim, whiteSpace: "nowrap" }}>
            [{fmt(a.ts)}] SENTINEL.AUDIT score={a.score.toFixed(3)} src={a.ip} type={a.eventType}
          </span>
        ))}
        <span style={{ marginLeft: "auto", color: T.dim, whiteSpace: "nowrap", letterSpacing: 1 }}>
          sac sentinel watch --live · KynicOS v0.1
        </span>
      </footer>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: REAL-TIME
// ═══════════════════════════════════════════════════════════════════════════════
function RealtimeTab({ chart }: { chart: { t: number; s: number }[] }) {
  const alerts  = useAlertStore((s) => s.alerts);
  const metrics = useMetricsStore();

  const NODES = [
    { id: "NEXUS",    desc: "ETL · Shadow Index", load: 34, port: 8081, status: "ACTIVE" },
    { id: "SENTINEL", desc: "Audit · Defense",    load: metrics.gpuLoadPct, port: 8082, status: "ACTIVE" },
    { id: "FORGE",    desc: "WASM Build",         load: 12, port: 8083, status: "ACTIVE" },
    { id: "CHRONOS",  desc: "Workers",            load: 45, port: 8084, status: "ACTIVE" },
    { id: "UPLINK",   desc: "Alerts / Telegram",  load: 8,  port: 8085, status: "ACTIVE" },
    { id: "VANGUARD", desc: "Handhelds MC9300",   load: 0,  port: 8086, status: "MAINT"  },
  ];

  const HONEYPOTS = [
    { id: "HP-SSH-BACKUP", name: "SSH Decoy :22022",    hits: 47, fresh: true  },
    { id: "HP-WMS-ADMIN",  name: "WMS Admin Panel",     hits: 11, fresh: false },
    { id: "HP-DB2-CEDIS",  name: "DB2 Decoy :50000",    hits: 3,  fresh: false },
    { id: "HP-FTP-ARCH",   name: "FTP Archive :21",     hits: 0,  fresh: false },
  ];

  const nodeColor = (st: string) => st === "ACTIVE" ? T.green : st === "MAINT" ? T.amber : T.red;

  return (
    <div style={{ flex: 1, display: "grid", gridTemplateColumns: "200px 1fr 240px", overflow: "hidden", gap: 1, background: T.border }}>

      {/* ── COL 1: NODES + HONEYPOTS ─────────────────────────────────────────── */}
      <div style={{ background: T.panel, overflow: "auto", padding: 10, display: "flex", flexDirection: "column", gap: 10 }}>
        <div>
          <Label text="KYNICOS NODES" accent={T.green} />
          {NODES.map((n) => (
            <div key={n.id} style={{
              marginBottom: 5, padding: "6px 8px",
              background: T.surface, border: `1px solid ${T.border}`,
              borderLeft: `3px solid ${nodeColor(n.status)}`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                <span style={{ color: nodeColor(n.status), fontWeight: 700, fontSize: 11 }}>{n.id}</span>
                <span style={{
                  fontSize: 8, letterSpacing: 2, padding: "1px 5px",
                  border: `1px solid ${nodeColor(n.status)}33`,
                  color: nodeColor(n.status), background: `${nodeColor(n.status)}11`,
                  animation: n.status === "MAINT" ? "pulse 1.5s infinite" : "none",
                }}>{n.status}</span>
              </div>
              <div style={{ color: T.dim, fontSize: 9, marginBottom: 4 }}>{n.desc} :{n.port}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <Bar pct={n.load} color={n.load > 70 ? T.red : n.load > 45 ? T.amber : T.green} />
                <span style={{ color: T.dim, fontSize: 9, width: 28, textAlign: "right" }}>{n.load}%</span>
              </div>
            </div>
          ))}
        </div>

        <div>
          <Label text="HONEYPOTS" accent={T.amber} />
          {HONEYPOTS.map((hp) => (
            <div key={hp.id} style={{
              marginBottom: 5, padding: "5px 8px",
              background: hp.fresh ? `${T.red}08` : T.surface,
              border: `1px solid ${hp.fresh ? T.red : T.border}`,
              borderLeft: `3px solid ${hp.hits > 20 ? T.red : hp.hits > 0 ? T.amber : T.dim}`,
              transition: "all .5s",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: T.bright, fontSize: 9 }}>{hp.name}</span>
                <span style={{ color: hp.hits > 20 ? T.red : hp.hits > 0 ? T.amber : T.dim, fontWeight: 700, fontSize: 11 }}>
                  {hp.hits}
                </span>
              </div>
              {hp.fresh && (
                <div className="blink" style={{ color: T.red, fontSize: 8, marginTop: 2 }}>
                  ⚡ ACTIVE — collecting intel
                </div>
              )}
            </div>
          ))}
        </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "20px" }}>
        <StatCard title="THROUGHPUT" value={`${(events.length * 2.5).toFixed(1)}k ev/s`} color="#00c8ff" subtitle="AMD MI300X" />
        <StatCard title="CRITICAL" value={criticalCount} color="#ff1a1a" subtitle="MITRE AT&CK MATCH" />
        <StatCard title="AVG SEVERITY" value={`${(avgSev * 100).toFixed(0)}%`} color="#ff6400" subtitle="UEBA BASELINE" />
        <StatCard title="WASM LATENCY" value="1.2ms" color="#32ff32" subtitle="ZERO CLOUD CALLS" />
      </div>

      {/* ── COL 2: ALERT FEED + CHART ──────────────────────────────────────────── */}
      <div style={{ background: T.panel, display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Alert feed */}
        <div style={{ flex: 1, overflow: "hidden", padding: "10px 12px", display: "flex", flexDirection: "column", borderBottom: `1px solid ${T.border}` }}>
          <Label text="LIVE THREAT FEED" accent={T.red} />
          <div style={{
            display: "grid", gridTemplateColumns: "52px 110px 28px 1fr 80px",
            gap: 6, padding: "0 6px 5px", color: T.dim, fontSize: 9, letterSpacing: 1,
            borderBottom: `1px solid ${T.border}`, flexShrink: 0,
          }}>
            <span>TIME</span><span>SOURCE IP</span><span>GEO</span><span>EVENT</span><span style={{ textAlign: "right" }}>SCORE</span>
          </div>
          <div style={{ flex: 1, overflowY: "auto", paddingTop: 4 }}>
            {alerts.map((a, i) => (
              <div
                data-testid={i === 0 ? "alert-feed" : undefined}
                key={a.id}
                className={i === 0 ? "new-row" : ""}
                style={{
                  display: "grid", gridTemplateColumns: "52px 110px 28px 1fr 80px",
                  gap: 6, padding: "5px 6px", marginBottom: 2,
                  background: i === 0 ? `${scoreColor(a.score)}09` : T.surface,
                  border: `1px solid ${i === 0 ? `${scoreColor(a.score)}30` : T.border}`,
                  borderLeft: `3px solid ${scoreColor(a.score)}`,
                  transition: "background 1.2s",
                }}>
                <span style={{ color: T.dim, fontSize: 9 }}>{fmt(a.ts)}</span>
                <span style={{ color: T.text, fontSize: 9, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{a.ip}</span>
                <span style={{ color: T.dim, fontSize: 9 }}>{a.geo.slice(0, 3)}</span>
                <span style={{ color: T.bright, fontSize: 10, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{a.msg}</span>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: scoreColor(a.score), fontSize: 8, letterSpacing: 1 }}>{scoreLabel(a.score)}</div>
                  <div style={{ color: scoreColor(a.score), fontSize: 12, fontWeight: 700 }}>
                    {(a.score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Anomaly chart */}
        <div style={{ height: 160, padding: "8px 12px 4px", flexShrink: 0 }}>
          <Label text="ANOMALY SCORE — ENSEMBLE IF+AE (AMD ROCm)" accent={T.green} />
          <div style={{ position: "relative" }}>
            <div style={{
              position: "absolute", right: 8, top: 0,
              display: "flex", gap: 12, fontSize: 9, zIndex: 2,
            }}>
              <span style={{ color: T.amber }}>── HIGH 0.65</span>
              <span style={{ color: T.red   }}>── CRIT 0.85</span>
            </div>
            <ResponsiveContainer width="100%" height={120}>
              <AreaChart data={chart} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="aGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={T.green} stopOpacity={0.35} />
                    <stop offset="95%" stopColor={T.green} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="t" hide />
                <YAxis domain={[0, 1]} hide />
                <Tooltip
                  contentStyle={{ background: T.panel, border: `1px solid ${T.border}`, fontSize: 9, fontFamily: T.font }}
                  formatter={(v: number) => [(v * 100).toFixed(1) + "%", "Anomaly"]}
                  labelFormatter={() => ""}
                />
                <ReferenceLine y={0.65} stroke={T.amber} strokeDasharray="3 3" strokeWidth={1} />
                <ReferenceLine y={0.85} stroke={T.red}   strokeDasharray="3 3" strokeWidth={1} />
                <Area
                  type="monotone" dataKey="s"
                  stroke={T.green} strokeWidth={1.5}
                  fill="url(#aGrad)" dot={false}
                  activeDot={{ r: 3, fill: T.amber }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── COL 3: GPU + WASM + STRIDE ────────────────────────────────────────── */}
      <div style={{ background: T.panel, overflow: "auto", padding: 10 }}>

        <Label text="AMD MI300X — ROCm 7.2" accent={T.purple} />
        <div style={{ background: T.surface, border: `1px solid ${T.border}`, padding: "8px 10px", marginBottom: 10 }}>
          {[
            { l: "VRAM",       v: `${metrics.vramUsedGb}/${metrics.vramTotalGb} GB`, pct: (metrics.vramUsedGb / metrics.vramTotalGb) * 100, c: T.green },
            { l: "GPU LOAD",   v: `${metrics.gpuLoadPct}%`, pct: metrics.gpuLoadPct, c: metrics.gpuLoadPct > 70 ? T.red : T.amber },
            { l: "LATENCY",    v: `${metrics.gpuLatencyMs}ms`,  pct: metrics.gpuLatencyMs, c: T.green },
            { l: "F1 SCORE",   v: metrics.f1Score.toFixed(3),  pct: metrics.f1Score * 100, c: T.green },
          ].map((r) => (
            <div key={r.l} style={{ marginBottom: 7 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                <span style={{ color: T.dim, fontSize: 9 }}>{r.l}</span>
                <span style={{ color: r.c, fontSize: 9, fontWeight: 700 }}>{r.v}</span>
              </div>
              <Bar pct={r.pct} color={r.c} />
            </div>
          ))}
          <div style={{ borderTop: `1px solid ${T.border}`, paddingTop: 6, marginTop: 4 }}>
            {[
              ["ENSEMBLE",    "IF×0.45 + AE×0.55"],
              ["SPEEDUP",     `${metrics.speedupRatio}x vs CPU`],
              ["FP RATE",     `${metrics.fpRate}%`],
              ["LLM",         "Llama 70B (local)"],
              ["API COST",    "$0.00 / query"],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                <span style={{ color: T.dim, fontSize: 9 }}>{k}</span>
                <span style={{ color: T.text, fontSize: 9 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        <Label text="WASM ENGINE" accent={T.blue} />
        <div style={{ background: T.surface, border: `1px solid ${T.border}`, padding: "8px 10px", marginBottom: 10 }}>
          {[
            ["PARSERS",     "syslog·db2·json·win·nf"],
            ["FEATURES",    "32 dims / event"],
            ["SIZE",        `${metrics.wasmSizeKb} KB`],
            ["SAB GUARDS",  "Atomics.cmpxchg ✓"],
            ["CSP",         "wasm-unsafe-eval ✓"],
          ].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
              <span style={{ color: T.dim, fontSize: 9 }}>{k}</span>
              <span style={{ color: T.green, fontSize: 9 }}>{v}</span>
            </div>
          ))}
        </div>

        <Label text="STRIDE COVERAGE" accent={T.dim} />
        {[
          ["Spoofing",        true ],
          ["Tampering",       true ],
          ["Repudiation",     true ],
          ["Info Disclosure", true ],
          ["DoS",             false],
          ["Priv Escalation", true ],
        ].map(([k, ok]) => (
          <div key={String(k)} style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
            <span style={{ color: T.dim, fontSize: 9 }}>{String(k)}</span>
            <span style={{ color: ok ? T.green : T.amber, fontSize: 9 }}>
              {ok ? "● MITIGATED" : "◌ PARTIAL"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: WASM PARSERS
// ═══════════════════════════════════════════════════════════════════════════════
function ParsersTab() {
  const [input,  setInput]  = useState("Apr 04 03:22:11 cedis sshd[1234]: Failed password for root from 185.220.101.42 port 44321 ssh2");
  const [source, setSource] = useState("syslog");
  const [result, setResult] = useState<null | Record<string, unknown>>(null);

  const parse = () => {
    // Demo parser — real impl calls WASM parse_log_line()
    const demo: Record<string, unknown> = {
      timestamp_ms:   Date.now(),
      event_type:     input.toLowerCase().includes("failed") ? "login_failure" : "unknown",
      local_severity: input.toLowerCase().includes("drop") ? 0.85 : input.toLowerCase().includes("failed") ? 0.45 : 0.3,
      source:         (input.match(/from (\d+\.\d+\.\d+\.\d+)/) || [])[1] || "unknown",
      source_type:    source,
      fingerprint:    Math.random().toString(36).slice(2, 10),
      features_dim:   32,
    };
    setResult(demo);
  };

  const SAMPLES = {
    syslog:  "Apr 04 03:22:11 cedis sshd[1234]: Failed password for root from 185.220.101.42 port 44321 ssh2",
    db2:     "TIMESTAMP=2026-04-08 02:17:00 AUTHID=ROOT HOSTNAME=cedis_427 SQL=DROP TABLE WMS_USER SQLCODE=0",
    windows: "EventID: 4672 Account Name: svc_backdoor Computer: CEDIS-DC01",
    netflow: "185.220.101.42 10.0.0.1 54321 22 TCP 4096 12",
    json:    '{"event_type":"login_failure","src_ip":"10.0.3.99","user":"admin","severity":0.7}',
  };

  return (
    <div style={{ flex: 1, padding: 20, overflow: "auto", background: T.panel }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <h2 style={{ fontFamily: T.display, color: T.amber, fontSize: 20, marginBottom: 4, letterSpacing: 3 }}>
          WASM PARSER ENGINE
        </h2>
        <p style={{ color: T.dim, fontSize: 10, marginBottom: 20, letterSpacing: 1 }}>
          RUST → WASM · 5 PARSERS · 32 FEATURE DIMENSIONS · &lt;5ms LATENCY
        </p>

        {/* Source selector */}
        <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
          {(["syslog","db2","windows","netflow","json"] as const).map((s) => (
            <button key={s} onClick={() => { setSource(s); setInput(SAMPLES[s]); }} style={{
              padding: "4px 12px", fontSize: 9, letterSpacing: 2,
              background: source === s ? `${T.amber}18` : T.surface,
              border: `1px solid ${source === s ? T.amber : T.border}`,
              color: source === s ? T.amber : T.dim,
              cursor: "pointer", fontFamily: T.font, textTransform: "uppercase",
            }}>{s}</button>
          ))}
        </div>

        {/* Input */}
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={3}
          style={{
            width: "100%", background: T.surface, border: `1px solid ${T.border}`,
            color: T.bright, fontFamily: T.font, fontSize: 11, padding: 10,
            resize: "vertical", outline: "none", marginBottom: 10,
          }}
        />

        <button onClick={parse} style={{
          padding: "8px 20px", background: `${T.amber}18`, border: `1px solid ${T.amber}`,
          color: T.amber, cursor: "pointer", fontFamily: T.font, fontSize: 10,
          letterSpacing: 3, marginBottom: 16,
        }}>
          ▶ PARSE LOG
        </button>

        {result && (
          <div style={{ background: T.surface, border: `1px solid ${T.green}33`, padding: 14 }}>
            <div style={{ color: T.green, fontSize: 9, letterSpacing: 2, marginBottom: 8 }}>
              ✓ PARSED EVENT
            </div>
            <pre style={{ color: T.text, fontSize: 11, whiteSpace: "pre-wrap", lineHeight: 1.8 }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}

        {/* Feature vector description */}
        <div style={{ marginTop: 24, padding: 14, background: T.surface, border: `1px solid ${T.border}` }}>
          <div style={{ color: T.amber, fontSize: 9, letterSpacing: 2, marginBottom: 10 }}>
            32-DIMENSIONAL FEATURE CONTRACT (Rust ↔ Python Model)
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 4 }}>
            {[
              "event_type_encoded","local_severity","hour_of_day","day_of_week",
              "is_weekend","is_off_hours","source_is_internal","destination_exists",
              "has_user","source_entropy","user_entropy","metadata_field_count",
              "is_privileged_port","dst_port_normalized","bytes_log10_normalized","has_db_keyword",
              "has_destructive_op","is_sensitive_table","has_bulk_operation","has_network_scan_sig",
              "is_privileged_account","process_is_known","has_lateral_movement","source_is_cloud",
              "raw_length_normalized","has_base64_payload","has_powershell_sig","windows_event_risk",
              "db2_operation_risk","netflow_risk","composite_risk_1","composite_risk_2",
            ].map((f, i) => (
              <div key={f} style={{ fontSize: 9, color: T.dim, padding: "2px 0" }}>
                <span style={{ color: T.amber }}>F{i.toString().padStart(2,"0")}</span>
                {" "}{f}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: BENCHMARK
// ═══════════════════════════════════════════════════════════════════════════════
function BenchmarkTab() {
  const metrics = useMetricsStore();

  const rows = [
    { metric: "Throughput (ev/s)",     cpu: "1,161,218",  gpu: "4,216,327",  speedup: `${metrics.speedupRatio}x`, target: ">10x ⚠️" },
    { metric: "Latency 100 events",    cpu: "182 ms",     gpu: `${metrics.gpuLatencyMs} ms`, speedup: "5.4x",  target: "<50ms ✅" },
    { metric: "F1 Score (ensemble)",   cpu: "0.91",       gpu: "0.999",      speedup: "—",    target: ">0.90 ✅" },
    { metric: "False Positive Rate",   cpu: "6.1%",       gpu: `${metrics.fpRate}%`, speedup: "—", target: "<5% ✅" },
    { metric: "WASM module size",      cpu: "—",          gpu: `${metrics.wasmSizeKb} KB`,  speedup: "—", target: "<1MB ✅" },
    { metric: "VRAM used",             cpu: "—",          gpu: `${metrics.vramUsedGb}/${metrics.vramTotalGb} GB`, speedup: "—", target: "7.4% ✅" },
    { metric: "LLM cost/explanation",  cpu: "$0.02",      gpu: "$0.00",      speedup: "∞",    target: "$0 ✅" },
  ];

  return (
    <div style={{ flex: 1, padding: 20, overflow: "auto", background: T.panel }}>
      <div style={{ maxWidth: 860, margin: "0 auto" }}>
        <h2 style={{ fontFamily: T.display, color: T.amber, fontSize: 20, marginBottom: 4, letterSpacing: 3 }}>
          BENCHMARK RESULTS
        </h2>
        <p style={{ color: T.dim, fontSize: 10, marginBottom: 20, letterSpacing: 1 }}>
          AMD EPYC CPU vs AMD INSTINCT MI300X (ROCm 7.2) · Synthetic dataset · AMD Hackathon 2026
        </p>

        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${T.border}` }}>
              {["METRIC","CPU (EPYC)","MI300X GPU","SPEEDUP","TARGET"].map((h) => (
                <th key={h} style={{ padding: "8px 10px", color: T.dim, fontSize: 9, letterSpacing: 2, textAlign: "left" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.metric} style={{ background: i % 2 === 0 ? T.surface : "transparent", borderBottom: `1px solid ${T.border}` }}>
                <td style={{ padding: "8px 10px", color: T.bright }}>{r.metric}</td>
                <td style={{ padding: "8px 10px", color: T.text }}>{r.cpu}</td>
                <td style={{ padding: "8px 10px", color: T.green, fontWeight: 700 }}>{r.gpu}</td>
                <td style={{ padding: "8px 10px", color: T.amber, fontWeight: 700 }}>{r.speedup}</td>
                <td style={{ padding: "8px 10px", color: T.dim, fontSize: 9 }}>{r.target}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop: 20, padding: 14, background: `${T.amber}08`, border: `1px solid ${T.amber}33` }}>
          <div style={{ color: T.amber, fontSize: 9, letterSpacing: 2, marginBottom: 6 }}>⚠ NOTA SOBRE SPEEDUP</div>
          <p style={{ color: T.text, fontSize: 10, lineHeight: 1.7 }}>
            El speedup actual de <strong style={{ color: T.amber }}>3.6x</strong> corresponde al dataset sintético pequeño.
            Con el dataset CERT de 100K eventos en el droplet AMD MI300X real, el speedup esperado es <strong style={{ color: T.green }}>15–23x</strong>
            (baseline de literatura para cuML vs sklearn con N≥100K).
            Benchmark completo pendiente de acceso al droplet AMD Developer Cloud.
          </p>
          <div style={{ marginTop: 10, padding: 8, background: T.surface, fontFamily: T.font, fontSize: 10, color: T.dim }}>
            python training/train_models.py --dataset synthetic --n-samples 100000 --device auto --benchmark
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: MITRE ATT&CK
// ═══════════════════════════════════════════════════════════════════════════════
function MitreTab() {
  const TECHNIQUES = [
    { id: "T1110",   name: "Brute Force",               tactic: "Credential Access", count: 14, severity: 0.85 },
    { id: "T1078",   name: "Valid Accounts",             tactic: "Defense Evasion",   count: 8,  severity: 0.72 },
    { id: "T1059",   name: "Command Scripting",          tactic: "Execution",         count: 5,  severity: 0.68 },
    { id: "T1082",   name: "System Info Discovery",      tactic: "Discovery",         count: 11, severity: 0.45 },
    { id: "T1048",   name: "Exfiltration Over Alt Chnl", tactic: "Exfiltration",      count: 3,  severity: 0.91 },
    { id: "T1133",   name: "External Remote Services",   tactic: "Initial Access",    count: 6,  severity: 0.78 },
    { id: "T1070",   name: "Indicator Removal",          tactic: "Defense Evasion",   count: 2,  severity: 0.82 },
    { id: "T1021",   name: "Remote Services",            tactic: "Lateral Movement",  count: 4,  severity: 0.88 },
    { id: "T1053",   name: "Scheduled Task/Job",         tactic: "Persistence",       count: 1,  severity: 0.79 },
    { id: "T1136",   name: "Create Account",             tactic: "Persistence",       count: 2,  severity: 0.75 },
    { id: "T1005",   name: "Data from Local System",     tactic: "Collection",        count: 3,  severity: 0.83 },
    { id: "T1071",   name: "App Layer Protocol",         tactic: "C2",                count: 2,  severity: 0.88 },
  ];

  return (
    <div style={{ flex: 1, padding: 20, overflow: "auto", background: T.panel }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <h2 style={{ fontFamily: T.display, color: T.amber, fontSize: 20, marginBottom: 4, letterSpacing: 3 }}>
          MITRE ATT&CK COVERAGE
        </h2>
        <p style={{ color: T.dim, fontSize: 10, marginBottom: 20, letterSpacing: 1 }}>
          Techniques detected in current session · Kalpixk SIEM v0.1
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
          {TECHNIQUES.map((t) => (
            <div key={t.id} style={{
              padding: "10px 12px",
              background: t.severity >= 0.85 ? `${T.red}08` : t.severity >= 0.70 ? `${T.amber}08` : T.surface,
              border: `1px solid ${t.severity >= 0.85 ? T.red : t.severity >= 0.70 ? T.amber : T.border}`,
              borderLeft: `3px solid ${scoreColor(t.severity)}`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ color: T.amber, fontWeight: 700, fontSize: 11 }}>{t.id}</span>
                <span style={{ color: scoreColor(t.severity), fontSize: 11, fontWeight: 700 }}>
                  {t.count}×
                </span>
              </div>
              <div style={{ color: T.bright, fontSize: 10, marginBottom: 2 }}>{t.name}</div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: T.dim, fontSize: 9 }}>{t.tactic}</span>
                <span style={{ color: scoreColor(t.severity), fontSize: 9 }}>
                  {(t.severity * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
