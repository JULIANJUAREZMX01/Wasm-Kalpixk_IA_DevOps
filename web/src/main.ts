/**
 * Kalpixk SIEM — Unified Dashboard
 * Integrates WASM Edge + AMD MI300X Neural Core
 */
import { initWasm, version, parse_log_line, health_check } from "./wasm/index";

interface ParsedEvent {
  timestamp_ms: number;
  event_type: string;
  source: string;
  local_severity: number;
  raw: string;
}

interface ApiStatus {
  status: string;
  model_trained: boolean;
  device: string;
  gpu_available: boolean;
}

let events: ParsedEvent[] = [];
let wasmVersion = "cargando...";
let wasmParseFn: any = null;
let apiStatus: ApiStatus | null = null;
let apiMetrics: any = null;

const DEMO_LOGS = [
  { type: "syslog",  raw: "Apr 9 10:00:00 server sshd[123]: Failed password for root from 192.168.1.50" },
  { type: "db2",     raw: "TIMESTAMP=20260409 AUTHID=DB2INST1 OPERATION=DDL STATEMENT=DROP TABLE SENSITIVE_DATA" },
  { type: "windows", raw: "EventID: 7045 ServiceName: MaliciousSvc Computer: WS-01 ServiceFileName: C:\\temp\\malware.exe" },
  { type: "syslog",  raw: "Apr 9 10:05:00 server sshd[456]: Accepted publickey for jjuarez from 10.0.0.5" },
];

function setStatus(msg: string) {
  const el = document.getElementById("wasm-log");
  if (el) el.innerHTML += `<div>[SYSTEM] ${msg}</div>`;
}

async function checkApi() {
  try {
    const res = await fetch("/health");
    if (res.ok) {
      apiStatus = await res.json();
      console.log("API Connected:", apiStatus);
    }
  } catch (e) {
    console.log("API Offline or Dev mode");
  }
}

async function fetchMetrics() {
  if (!apiStatus) return;
  try {
    const res = await fetch("/metrics");
    if (res.ok) {
      apiMetrics = await res.json();
      render();
    }
  } catch (e) {
    console.error("Error fetching metrics", e);
  }
}

function sevColor(val: number) {
  if (val >= 0.8) return "#ff1a1a";
  if (val >= 0.5) return "#ff6400";
  return "#32ff32";
}

function render() {
  const app = document.getElementById("app");
  if (!app) return;

  const crit = events.filter(e => e.local_severity >= 0.8);
  const high = events.filter(e => e.local_severity >= 0.5 && e.local_severity < 0.8);
  const avg = events.length ? events.reduce((a, b) => a + b.local_severity, 0) / events.length : 0;

  const stColor = apiStatus ? "#32ff32" : "#ff1a1a";
  const stText = apiStatus ? `● NEURAL CORE ACTIVE (${apiStatus.device})` : "● EDGE MODE ONLY (OFFLINE)";

  const rows = events.slice().reverse().map(ev => `
    <tr style="border-bottom:1px solid #111">
      <td style="padding:8px 12px;font-size:10px;color:#555">${new Date(ev.timestamp_ms).toLocaleTimeString()}</td>
      <td style="padding:8px 12px;font-size:10px;color:#00c8ff">${ev.event_type}</td>
      <td style="padding:8px 12px;font-size:10px;color:#e2e8f0">${ev.source}</td>
      <td style="padding:8px 12px">
        <span style="color:${sevColor(ev.local_severity)};font-weight:bold">${(ev.local_severity * 100).toFixed(0)}%</span>
      </td>
      <td style="padding:8px 12px;font-size:9px;color:#444;font-family:monospace">${ev.raw.substring(0, 60)}...</td>
    </tr>`).join("");

  const gpuInfo = apiMetrics ? `
    <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;padding:16px">
      <div style="color:#555;font-size:10px;margin-bottom:6px">GPU RECONSTRUCTION ERROR</div>
      <div style="color:#ff1a1a;font-size:28px;font-weight:bold">${(apiMetrics.detection.reconstruction_errors[0] || 0).toFixed(6)}</div>
      <div style="color:#444;font-size:9px">threshold: ${apiMetrics.detection.threshold.toFixed(4)}</div>
    </div>
  ` : `
    <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;padding:16px;opacity:0.5">
      <div style="color:#555;font-size:10px;margin-bottom:6px">MI300X TELEMETRY</div>
      <div style="color:#444;font-size:20px;font-weight:bold">WAITING...</div>
      <div style="color:#444;font-size:9px">connect to python api</div>
    </div>
  `;

  app.innerHTML = `
    <style>
      *{box-sizing:border-box;margin:0;padding:0}
      body{background:#080808;color:#e2e8f0;font-family:'Courier New',monospace}
      @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
      .blink{animation:pulse 1.5s infinite}
      ::-webkit-scrollbar{width:5px;background:#0d0f14}
      ::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:3px}
    </style>

    <div style="min-height:100vh;display:flex;flex-direction:column">
      <!-- HEADER -->
      <div style="background:#0a0c10;border-bottom:1px solid #1a1a1a;padding:12px 20px;display:flex;align-items:center;justify-content:space-between">
        <div style="display:flex;align-items:center;gap:12px">
          <div style="width:10px;height:10px;background:#ff1a1a;border-radius:50%;box-shadow:0 0 10px #ff1a1a" class="blink"></div>
          <span style="color:#ff1a1a;font-weight:bold;letter-spacing:4px;font-size:18px">KALPIXK SIEM</span>
        </div>
        <div style="text-align:right">
          <div style="color:${stColor};font-size:11px;font-weight:bold" class="${apiStatus?'':'blink'}">${stText}</div>
          <div style="color:#444;font-size:9px">WASM Core: ${wasmVersion}</div>
        </div>
      </div>

      <!-- GRID -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;padding:20px">
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;padding:16px">
          <div style="color:#555;font-size:10px;margin-bottom:6px">WASM EVENTS</div>
          <div style="color:#00c8ff;font-size:28px;font-weight:bold">${events.length}</div>
          <div style="color:#444;font-size:9px">local edge parsing</div>
        </div>
        ${gpuInfo}
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;padding:16px">
          <div style="color:#555;font-size:10px;margin-bottom:6px">CRITICAL THREATS</div>
          <div style="color:#ff1a1a;font-size:28px;font-weight:bold">${crit.length}</div>
          <div style="color:#444;font-size:9px">severity >= 80%</div>
        </div>
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;padding:16px">
          <div style="color:#555;font-size:10px;margin-bottom:6px">AVG SEVERITY</div>
          <div style="color:${sevColor(avg)};font-size:28px;font-weight:bold">${(avg*100).toFixed(1)}%</div>
          <div style="height:4px;background:#111;margin-top:8px;border-radius:2px">
            <div style="height:100%;background:${sevColor(avg)};width:${avg*100}%"></div>
          </div>
        </div>
      </div>

      <!-- MAIN CONTENT -->
      <div style="flex-grow:1;display:grid;grid-template-columns:3fr 1fr;gap:20px;padding:0 20px 20px">
        <!-- LOG TABLE -->
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;display:flex;flex-direction:column;overflow:hidden">
          <div style="padding:12px 16px;border-bottom:1px solid #1a1a1a;display:flex;justify-content:space-between">
            <span style="font-size:12px;font-weight:bold">LIVE STREAM</span>
            <div style="display:flex;gap:10px">
               <button onclick="window._simulate()" style="background:#ff1a1a22;border:1px solid #ff1a1a;color:#ff1a1a;padding:4px 10px;font-size:10px;cursor:pointer">▶ ATTACK</button>
               <button onclick="window._clear()" style="background:#111;border:1px solid #333;color:#777;padding:4px 10px;font-size:10px;cursor:pointer">CLEAR</button>
            </div>
          </div>
          <div style="overflow-y:auto;flex-grow:1">
            <table style="width:100%;border-collapse:collapse">
              <thead style="position:sticky;top:0;background:#0d0f14;z-index:1">
                <tr>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left">TIME</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left">TYPE</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left">SOURCE</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left">SEV</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left">LOG</th>
                </tr>
              </thead>
              <tbody>${rows || '<tr><td colspan="5" style="padding:40px;text-align:center;color:#333">WAITING FOR VECTOR...</td></tr>'}</tbody>
            </table>
          </div>
        </div>

        <!-- CONSOLE -->
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;display:flex;flex-direction:column;overflow:hidden">
          <div style="padding:10px 16px;border-bottom:1px solid #1a1a1a;font-size:11px;color:#32ff32">WASM_CONSOLE</div>
          <div id="wasm-log" style="padding:12px;font-size:10px;color:#32ff32;flex-grow:1;overflow-y:auto;background:#050505;line-height:1.6"></div>
        </div>
      </div>
    </div>
  `;
}

function wasmLog(msg: string, color = "#32ff32") {
  const el = document.getElementById("wasm-log");
  if (!el) return;
  const ts = new Date().toLocaleTimeString();
  el.innerHTML += `<div><span style="color:#444">[${ts}]</span> <span style="color:${color}">${msg}</span></div>`;
  el.scrollTop = el.scrollHeight;
}

function addEvent(raw: string, type: string) {
  if (!wasmParseFn) return;
  try {
    const result = wasmParseFn(raw, type);
    if (!result) return;
    const ev = JSON.parse(result) as ParsedEvent;
    ev.raw = raw;
    ev.timestamp_ms = Date.now();
    events.push(ev);
    wasmLog(`EDGE_MATCH: ${type} → ${ev.event_type} (${(ev.local_severity*100).toFixed(0)}%)`, sevColor(ev.local_severity));
    render();
  } catch (e) {
    console.error(e);
  }
}

(window as any)._simulate = () => {
  let i = 0;
  const iv = setInterval(() => {
    if (i >= DEMO_LOGS.length) { clearInterval(iv); return; }
    addEvent(DEMO_LOGS[i].raw, DEMO_LOGS[i].type);
    i++;
  }, 400);
};

(window as any)._clear = () => { events = []; render(); };

async function main() {
  await checkApi();
  try {
    await initWasm();
    wasmVersion = version();
    wasmParseFn = parse_log_line;
    render();
    wasmLog(`WASM Engine v${wasmVersion} Online`, "#32ff32");
    const health = JSON.parse(health_check());
    wasmLog(`Features: ${health.feature_dim}D | Parsers: 5`, "#00c8ff");

    setInterval(fetchMetrics, 2000);
  } catch (err) {
    console.error(err);
  }
}

main();
