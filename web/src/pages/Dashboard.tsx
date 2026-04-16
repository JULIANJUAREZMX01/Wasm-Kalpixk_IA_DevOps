import React, { useEffect, useState, useMemo, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useAlertStore } from '../stores/alertStore';
import { useMetricsStore } from '../stores/metricsStore';
import { useWasmStore } from '../stores/wasmStore';
import { AlertFeed } from '../components/AlertFeed';

// Design tokens
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

const scoreColor = (s: number) => s >= 0.85 ? T.red : s >= 0.65 ? T.amber : T.green;
const scoreLabel = (s: number) => s >= 0.85 ? "CRIT" : s >= 0.65 ? "HIGH" : "MED";
const fmt = (d: Date) => d.toLocaleTimeString("es-MX", { hour12: false });
const seedChart = () => Array.from({ length: 90 }, (_, i) => ({
  t: i,
  s: Math.min(0.98, 0.05 + Math.random() * 0.2 + (Math.random() > 0.88 ? Math.random() * 0.7 : 0)),
}));

function Label({ text, accent = T.amber }: { text: string; accent?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8, flexShrink: 0 }}>
      <div style={{ width: 5, height: 5, background: accent, transform: "rotate(45deg)" }} />
      <span style={{ color: T.dim, fontSize: 9, letterSpacing: 3, fontFamily: T.font }}>{text}</span>
      <div style={{ flex: 1, height: 1, background: T.border }} />
    </div>
  );
}

function Bar({ pct, color }: { pct: number; color: string }) {
  return (
    <div style={{ height: 3, background: T.border, borderRadius: 2, overflow: "hidden", flex: 1 }}>
      <div style={{ width: `${Math.min(100, pct)}%`, height: "100%", background: color, transition: "width 1.4s ease" }} />
    </div>
  );
}

export const Dashboard: React.FC = () => {
  const alerts = useAlertStore((s) => s.alerts);
  const criticalCount = useAlertStore((s) => s.criticalCount);
  const totalDetected = useAlertStore((s) => s.totalDetected);
  const metrics = useMetricsStore();
  const wasm = useWasmStore();

  const [clock, setClock] = useState(new Date());
  const [chart, setChart] = useState(seedChart);
  const [scan, setScan] = useState(0);
  const prevLen = useRef(0);

  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const t = setInterval(() => setScan((p) => (p + 1) % 100), 70);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (alerts.length > prevLen.current && alerts[0]) {
      prevLen.current = alerts.length;
      setChart((p) => [...p.slice(1), { t: p[p.length - 1].t + 1, s: alerts[0].score }]);
    }
  }, [alerts]);

  const threatLevel = alerts[0]?.score >= 0.85 ? "CRITICAL" : alerts[0]?.score >= 0.65 ? "HIGH" : "NORMAL";
  const tlColor = threatLevel === "CRITICAL" ? T.red : threatLevel === "HIGH" ? T.amber : T.green;

  return (
    <div style={{ background: T.bg, color: T.text, fontFamily: T.font, height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden", fontSize: 11, position: "relative" }}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes fadeIn { from { opacity:0; transform:translateY(-4px) } to { opacity:1; transform:translateY(0) } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
        @keyframes glow { 0%,100%{text-shadow:0 0 8px currentColor} 50%{text-shadow:0 0 24px currentColor,0 0 48px currentColor} }
        ::-webkit-scrollbar{width:3px;height:3px}
        ::-webkit-scrollbar-track{background:${T.bg}}
        ::-webkit-scrollbar-thumb{background:${T.border};border-radius:2px}
      `}</style>
      <header style={{ background: T.panel, borderBottom: `1px solid ${T.border}`, padding: "6px 16px", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
           <div style={{ width: 28, height: 28, background: T.amber, display: "flex", alignItems: "center", justifyContent: "center" }}>🏹</div>
           <div><div style={{ fontWeight: 800, fontSize: 16 }}>KALPIXK v4.0-ATLATL</div></div>
        </div>
        <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
          <div>{fmt(clock)}</div>
        </div>
      </header>
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 300px", gap: 1, background: T.border, overflow: "hidden" }}>
        <div style={{ background: T.panel, display: "flex", flexDirection: "column", overflow: "hidden" }}>
           <AlertFeed />
        </div>
        <div style={{ background: T.panel, padding: 10 }}>
           <Label text="ANOMALY VECTOR" />
           <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chart}>
                 <Area type="monotone" dataKey="s" stroke={T.green} fill={T.green} fillOpacity={0.1} />
              </AreaChart>
           </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
