import { useState, useEffect, useRef } from "react";
import {
  AreaChart, Area, XAxis, YAxis, ResponsiveContainer,
  Tooltip, ReferenceLine, CartesianGrid,
} from "recharts";
import { useAlertStore } from "../stores/alertStore";
import { useMetricsStore } from "../stores/metricsStore";
import { useWasmStore }    from "../stores/wasmStore";

// ── Design tokens (SAC_OS Alignment) ──────────────────────────────────────────
const T = {
  bg:      "#02040a", // Deeper black
  panel:   "#050814",
  surface: "#080c1d",
  border:  "#1a264a",
  amber:   "#ff9e00", // Brighter SAC orange
  green:   "#00f291", // Electric green
  red:     "#ff003c", // Phase Black red
  blue:    "#00a2ff", // Command blue
  purple:  "#a200ff",
  dim:     "#42557a",
  text:    "#a0b4d4",
  bright:  "#ffffff",
  font:    "'JetBrains Mono', monospace",
  display: "'Syne', sans-serif",
};

const scoreColor = (s: number) => s >= 0.85 ? T.red : s >= 0.65 ? T.amber : T.green;
const scoreLabel = (s: number) => s >= 0.85 ? "EXTERMINATE" : s >= 0.65 ? "RETALIATE" : "MONITOR";
const fmt        = (d: Date)   => d.toLocaleTimeString("es-MX", { hour12: false });

const seedChart  = () =>
  Array.from({ length: 60 }, (_, i) => ({
    t: i,
    s: Math.min(0.98, 0.05 + Math.random() * 0.2 + (Math.random() > 0.92 ? Math.random() * 0.7 : 0)),
  }));

// ── Sub-components ────────────────────────────────────────────────────────────
function Label({ text, accent = T.amber }: { text: string; accent?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8, flexShrink: 0 }}>
      <div style={{ width: 4, height: 4, background: accent, borderRadius: "50%" }} />
      <span style={{ color: T.dim, fontSize: 9, letterSpacing: 2, fontWeight: 700 }}>
        {text}
      </span>
      <div style={{ flex: 1, height: 1, background: T.border, opacity: 0.5 }} />
    </div>
  );
}

function Bar({ pct, color }: { pct: number; color: string }) {
  return (
    <div style={{ height: 2, background: T.border, overflow: "hidden", flex: 1 }}>
      <div style={{ width: `${Math.min(100, pct)}%`, height: "100%", background: color, transition: "width 0.8s ease-in-out" }} />
    </div>
  );
}

const ASCII_BANNER = `
    _  _____ _        _  _____ _
   / \\|_   _| |      / \\|_   _| |
  / _ \\ | | | |     / _ \\ | | | |
 / ___ \\| | | |___ / ___ \\| | | |___
/_/   \\_\\_| |_____/_/   \\_\\_| |_____|  ORDNANCE v4.0
`;

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function Dashboard() {
  const alerts        = useAlertStore((s) => s.alerts);
  const criticalCount = useAlertStore((s) => s.criticalCount);
  const totalDetected = useAlertStore((s) => s.totalDetected);
  const metrics       = useMetricsStore();
  const wasm          = useWasmStore();

  const [clock, setClock] = useState(new Date());
  const [chart, setChart] = useState(seedChart);
  const [scan,  setScan]  = useState(0);
  const [tab,   setTab]   = useState<"realtime"|"parsers"|"mesh"|"journal">("realtime");

  const prevLen = useRef(0);

  useEffect(() => { const t = setInterval(() => setClock(new Date()), 1000); return () => clearInterval(t); }, []);
  useEffect(() => { const t = setInterval(() => setScan((p) => (p + 1.5) % 100), 50); return () => clearInterval(t); }, []);

  useEffect(() => {
    if (alerts.length > prevLen.current && alerts[0]) {
      prevLen.current = alerts.length;
      setChart((p) => [...p.slice(1), { t: p[p.length - 1].t + 1, s: alerts[0].score }]);
    }
  }, [alerts]);

  const threatLevel = alerts[0]?.score >= 0.85 ? "PHASE BLACK" : alerts[0]?.score >= 0.65 ? "AGGRESSIVE" : "STABLE";
  const tlColor     = threatLevel === "PHASE BLACK" ? T.red : threatLevel === "AGGRESSIVE" ? T.amber : T.green;

  return (
    <div style={{
      background: T.bg, color: T.text, fontFamily: T.font,
      height: "100vh", display: "flex", flexDirection: "column",
      overflow: "hidden", fontSize: 11, position: "relative",
    }}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes fadeIn  { from { opacity:0; transform:scale(0.98) } to { opacity:1; transform:scale(1) } }
        @keyframes pulse   { 0%,100%{opacity:1} 50%{opacity:.4} }
        @keyframes blinker { 50% { opacity: 0; } }
        ::-webkit-scrollbar{width:2px;height:2px}
        ::-webkit-scrollbar-track{background:${T.bg}}
        ::-webkit-scrollbar-thumb{background:${T.dim}}
        .new-row { animation: fadeIn .3s ease-out }
        .blink    { animation: pulse 1s infinite }
        .critical-blink { animation: blinker 0.2s linear infinite; color: ${T.red}; font-weight: 800; }
      `}</style>

      {/* CRT scanline effects */}
      <div style={{
        position:"fixed", inset:0, zIndex:999, pointerEvents:"none", opacity: 0.15,
        background:"repeating-linear-gradient(0deg,transparent,transparent 2px, #000 2px, #000 3px)",
      }}/>
      <div style={{
        position:"fixed", left:0, right:0, height:1, top:`${scan}%`,
        background: `rgba(0, 162, 255, 0.2)`,
        zIndex:998, pointerEvents:"none",
      }}/>

      {/* ═══ HEADER ═══════════════════════════════════════════════════════════ */}
      <header style={{
        background: T.panel, borderBottom: `1px solid ${T.border}`,
        padding: "8px 20px", display: "flex", alignItems: "center",
        justifyContent: "space-between", flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 15 }}>
          <pre style={{ fontSize: 4, lineHeight: 1, color: T.amber, margin: 0 }}>{ASCII_BANNER}</pre>
          <div>
            <div style={{ fontFamily: T.display, fontWeight: 900, fontSize: 18, letterSpacing: 5, color: T.bright }}>
              KALPIXK <span style={{ color: T.amber }}>SIEM</span>
            </div>
            <div style={{ color: T.dim, fontSize: 8, letterSpacing: 1 }}>
              ALPHA STACK (WASM/ZIG/RUST) • GUERRILLA MESH v4.0-ATLATL
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          {["STABLE","AGGRESSIVE","PHASE BLACK"].map((lvl) => (
            <div key={lvl} style={{
              padding: "4px 12px", fontSize: 9, fontWeight: 700, letterSpacing: 2,
              border: `1px solid ${lvl === threatLevel ? tlColor : T.border}`,
              background: lvl === threatLevel ? `${tlColor}20` : "transparent",
              color:      lvl === threatLevel ? tlColor : T.dim,
              boxShadow:  lvl === threatLevel ? `0 0 10px ${tlColor}40` : "none",
            }}>{lvl}</div>
          ))}
        </div>

        <div style={{ display: "flex", gap: 25, alignItems: "center" }}>
          {[
            { l: "NEURAL_SYNC", v: (totalDetected + 1337).toLocaleString(), c: T.amber },
            { l: "EXTERMINATIONS", v: criticalCount, c: T.red },
            { l: "MESH_NODES", v: "07", c: T.blue },
            { l: "METAL_LAT", v: `${metrics.gpuLatencyMs}ms`, c: T.green },
          ].map(({ l, v, c }) => (
            <div key={l} style={{ textAlign: "right" }}>
              <div style={{ color: T.dim, fontSize: 8, letterSpacing: 1 }}>{l}</div>
              <div style={{ color: c, fontSize: 16, fontWeight: 900 }}>{v}</div>
            </div>
          ))}
          <div style={{
            color: T.bright, fontSize: 18, fontWeight: 900, letterSpacing: 2,
            borderLeft: `1px solid ${T.border}`, paddingLeft: 20, minWidth: 100, textAlign: "right"
          }}>
            {fmt(clock)}
          </div>
        </div>
      </header>

      {/* ═══ NAVIGATION ════════════════════════════════════════════════════════ */}
      <nav style={{ background: T.surface, borderBottom: `1px solid ${T.border}`, display: "flex", flexShrink: 0 }}>
        {([
          ["realtime", "OPERATIONS"],
          ["parsers",  "METAL CORE"],
          ["mesh",     "GUERRILLA MESH"],
          ["journal",  "WAR JOURNAL"],
        ] as const).map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={{
            background: tab === key ? `${T.blue}15` : "transparent",
            border: "none", color: tab === key ? T.blue : T.dim,
            padding: "10px 24px", fontSize: 10, fontWeight: 700, letterSpacing: 3,
            borderBottom: `2px solid ${tab === key ? T.blue : "transparent"}`,
            cursor: "pointer", transition: "all 0.2s",
          }}>{label}</button>
        ))}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", paddingRight: 20, gap: 10 }}>
          <div style={{ fontSize: 9, color: T.dim }}>NODE-7 INTEGRITY:</div>
          <div style={{
            padding: "2px 8px", background: `${T.green}20`, color: T.green,
            border: `1px solid ${T.green}40`, fontSize: 9, fontWeight: 700
          }}>VERIFIED ✓</div>
          <div style={{ width: 1, height: 12, background: T.border }} />
          <div style={{ fontSize: 9, color: T.dim }}>WASM: <span style={{ color: T.blue }}>v{wasm.version}</span></div>
        </div>
      </nav>

      {/* ═══ CONTENT ═════════════════════════════════════════════════════════ */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex" }}>
        {tab === "realtime" && <RealtimeTab chart={chart} />}
        {tab === "parsers"  && <div style={{ padding: 40 }}>METAL CORE MODULES (ZIG v5.0) — IMPLEMENTING STRIKE LOGIC...</div>}
        {tab === "mesh"     && <div style={{ padding: 40 }}>MESH TOPOLOGY — 7 ACTIVE NODES DETECTED.</div>}
        {tab === "journal"  && <div style={{ padding: 40 }}>WAR JOURNAL ACCESS — [OP_V4_GUERRILLAMESH] LOGGED.</div>}
      </div>

      {/* ═══ FOOTER ══════════════════════════════════════════════════════════ */}
      <footer style={{
        background: T.panel, borderTop: `1px solid ${T.border}`,
        padding: "6px 20px", display: "flex", alignItems: "center", gap: 15,
        fontSize: 9, flexShrink: 0,
      }}>
        <div style={{ color: T.red, fontWeight: 900, letterSpacing: 2 }}>[SYSTEM_MSG]</div>
        <div style={{ flex: 1, overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis", color: T.dim }}>
          {alerts[0] ? `>>> ATLATL DETECTED ${alerts[0].eventType} FROM ${alerts[0].ip} | ACTION: ${scoreLabel(alerts[0].score)}` : ">>> GRID STANDBY. NO AGGRESSION DETECTED."}
        </div>
        <div style={{ color: T.dim, letterSpacing: 1 }}>
          ATLATL-ORDNANCE // SAC_OS_CORE // CANCUN_427
        </div>
      </footer>
    </div>
  );
}

function RealtimeTab({ chart }: { chart: { t: number; s: number }[] }) {
  const alerts  = useAlertStore((s) => s.alerts);
  const metrics = useMetricsStore();

  return (
    <div style={{ flex: 1, display: "grid", gridTemplateColumns: "240px 1fr 300px", overflow: "hidden", gap: 1, background: T.border }}>

      {/* ── LEFT: COMBAT STATUS ────────────────────────────────────────────── */}
      <div style={{ background: T.panel, padding: 15, overflow: "auto" }}>
        <Label text="MESH STATUS" accent={T.blue} />
        {[
          { n: "Node-1: RECON", st: "ARMED" },
          { n: "Node-2: LATERAL", st: "ARMED" },
          { n: "Node-3: CREDS", st: "ARMED" },
          { n: "Node-4: EXEC", st: "ARMED" },
          { n: "Node-5: RCE", st: "ARMED" },
          { n: "Node-6: EXFIL", st: "ARMED" },
          { n: "Node-7: INTEGRITY", st: "VERIFIED", c: T.green },
        ].map(node => (
          <div key={node.n} style={{
            marginBottom: 8, padding: "8px 12px", background: T.surface,
            border: `1px solid ${T.border}`, display: "flex", justifyContent: "space-between"
          }}>
            <span style={{ fontSize: 10, fontWeight: 700 }}>{node.n}</span>
            <span style={{ fontSize: 9, color: node.c || T.amber, letterSpacing: 1 }}>{node.st}</span>
          </div>
        ))}

        <div style={{ marginTop: 20 }}>
          <Label text="PHASE BLACK MEASURES" accent={T.red} />
          {[
            { m: "V5 METAL STRIKE", val: "READY" },
            { m: "RECURSIVE ZIP BOMB", val: "ACTIVE" },
            { m: "POINTER POISONING", val: "STANDBY" },
            { m: "C2 CORRUPTION", val: "ENABLED" },
          ].map(m => (
            <div key={m.m} style={{ marginBottom: 6, fontSize: 9 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                <span style={{ color: T.dim }}>{m.m}</span>
                <span style={{ color: T.red }}>{m.val}</span>
              </div>
              <Bar pct={100} color={T.red + "40"} />
            </div>
          ))}
        </div>
      </div>

      {/* ── CENTER: ENGAGEMENT FEED ─────────────────────────────────────────── */}
      <div style={{ background: T.bg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ flex: 1, padding: 15, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <Label text="LIVE ENGAGEMENT FEED" accent={T.red} />
          <div style={{
            display: "grid", gridTemplateColumns: "70px 120px 1fr 100px",
            padding: "0 10px 8px", borderBottom: `1px solid ${T.border}`,
            fontSize: 9, color: T.dim, letterSpacing: 2
          }}>
            <span>TIMESTAMP</span><span>AGRESSOR_IP</span><span>VECTOR</span><span style={{ textAlign: "right" }}>SEVERITY</span>
          </div>
          <div style={{ flex: 1, overflowY: "auto", marginTop: 5 }}>
            {alerts.map((a, i) => (
              <div key={a.id} className="new-row" style={{
                display: "grid", gridTemplateColumns: "70px 120px 1fr 100px",
                padding: "10px", marginBottom: 1, background: i === 0 ? `${scoreColor(a.score)}15` : T.surface,
                borderLeft: `3px solid ${scoreColor(a.score)}`,
                borderRight: `1px solid ${T.border}`,
                borderBottom: `1px solid ${T.border}`,
              }}>
                <span style={{ color: T.dim, fontSize: 10 }}>{fmt(a.ts)}</span>
                <span style={{ color: T.bright, fontSize: 10, fontWeight: 700 }}>{a.ip}</span>
                <span style={{ color: T.text, fontSize: 10 }}>{a.msg}</span>
                <div style={{ textAlign: "right", color: scoreColor(a.score), fontWeight: 900, fontSize: 11 }}>
                  {(a.score * 100).toFixed(1)}%
                  <div style={{ fontSize: 7, letterSpacing: 1 }}>{scoreLabel(a.score)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ height: 180, padding: 15, borderTop: `1px solid ${T.border}` }}>
          <Label text="ANOMALY TREND (ALPHA STACK ENSEMBLE)" accent={T.green} />
          <ResponsiveContainer width="100%" height={130}>
            <AreaChart data={chart}>
              <defs>
                <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={T.red} stopOpacity={0.4}/>
                  <stop offset="95%" stopColor={T.red} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={T.border} vertical={false} />
              <XAxis dataKey="t" hide />
              <YAxis domain={[0, 1]} hide />
              <ReferenceLine y={0.85} stroke={T.red} strokeDasharray="5 5" />
              <Area type="stepAfter" dataKey="s" stroke={T.red} fill="url(#g)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── RIGHT: TELEMETRY ───────────────────────────────────────────────── */}
      <div style={{ background: T.panel, padding: 15, overflow: "auto" }}>
        <Label text="METAL PERFORMANCE" accent={T.green} />
        <div style={{ background: T.surface, padding: 12, border: `1px solid ${T.border}`, marginBottom: 20 }}>
          {[
            { l: "THROUGHPUT", v: "4.2M ev/s", p: 95, c: T.green },
            { l: "VRAM USED", v: `${metrics.vramUsedGb}GB`, p: 65, c: T.blue },
            { l: "GPU LOAD", v: `${metrics.gpuLoadPct}%`, p: metrics.gpuLoadPct, c: T.amber },
            { l: "METAL LATENCY", v: `${metrics.gpuLatencyMs}ms`, p: 20, c: T.green },
          ].map(stat => (
            <div key={stat.l} style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 8, color: T.dim }}>{stat.l}</span>
                <span style={{ fontSize: 10, fontWeight: 700, color: stat.c }}>{stat.v}</span>
              </div>
              <Bar pct={stat.p} color={stat.c} />
            </div>
          ))}
        </div>

        <Label text="WASM CONTRACTS" accent={T.blue} />
        <div style={{ fontSize: 9, color: T.text }}>
          {[
            ["shannon_entropy", "Zig v5"],
            ["v5_stealth_poison", "Zig v5"],
            ["validate_raw_log", "Rust v4"],
            ["analyze_all_nodes", "Rust v4"],
            ["execute_retaliation", "Rust v4"],
          ].map(([fn, lang]) => (
            <div key={fn} style={{
              display: "flex", justifyContent: "space-between", padding: "6px 0",
              borderBottom: `1px solid ${T.border}`, opacity: 0.8
            }}>
              <span style={{ color: T.blue }}>{fn}()</span>
              <span style={{ color: T.dim }}>{lang}</span>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 25, padding: 10, background: `${T.red}10`, border: `1px solid ${T.red}40` }}>
          <div className="critical-blink" style={{ fontSize: 10, textAlign: "center", letterSpacing: 2 }}>
            OFFENSIVE MODE ENABLED
          </div>
          <div style={{ fontSize: 8, color: T.dim, textAlign: "center", marginTop: 4 }}>
            ATAQUE PARA DEFENDER ACTIVATED
          </div>
        </div>
      </div>
    </div>
  );
}
