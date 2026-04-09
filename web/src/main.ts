import { initWasm, parse_log_line, process_batch, version, health_check, analyze_and_retaliate } from "./wasm/index";

// ═══════════════════════════════════════════════════
// KALPIXK SIEM — Dashboard principal funcional
// Motor WASM corriendo en el browser
// ═══════════════════════════════════════════════════

const LOGS_DEMO = [
  { raw: "Apr  5 02:14:22 cancun-srv01 sshd[1234]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:23 cancun-srv01 sshd[1235]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:24 cancun-srv01 sshd[1236]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:25 cancun-srv01 sshd[1237]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:26 cancun-srv01 sshd[1238]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:27 cancun-srv01 sshd[1239]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "TIMESTAMP=2026-04-05-02.15.00 AUTHID=CEDIS_USR HOSTNAME=185.220.101.35 OPERATION=DDL STATEMENT=DROP TABLE NOMINAS", type: "db2" },
  { raw: "Apr  5 10:00:00 cancun-srv01 sshd[1]: Accepted publickey for jjuarez from 192.168.1.50 port 44321", type: "syslog" },
  { raw: "Apr  5 03:00:00 cancun-srv01 sudo[888]: jjuarez : TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=/bin/bash", type: "syslog" },
  { raw: "Apr  5 04:22:10 cancun-srv01 kernel: [UFW BLOCK] IN=eth0 OUT= SRC=45.33.32.156 DST=10.0.0.5 LEN=60 PROTO=TCP DPT=3389", type: "syslog" },
  { raw: "TIMESTAMP=2026-04-05-03.00.00 AUTHID=SYS HOSTNAME=10.0.0.5 OPERATION=SELECT STATEMENT=SELECT * FROM EMPLEADOS WHERE SALARIO > 50000", type: "db2" },
  { raw: "Apr  5 05:11:00 cancun-srv01 sshd[999]: Failed password for admin from 203.0.113.45 port 22", type: "syslog" },
];

interface ParsedEvent {
  raw: string;
  event_type: string;
  local_severity: number;
  source: string;
  user: string | null;
  source_type: string;
  timestamp_ms: number;
}

let allEvents: ParsedEvent[] = [];
let wasmReady = false;

function severityColor(s: number): string {
  if (s >= 0.8) return "#ff1a1a";
  if (s >= 0.5) return "#ff6400";
  if (s >= 0.3) return "#f59e0b";
  return "#32ff32";
}

function severityLabel(s: number): string {
  if (s >= 0.8) return "CRÍTICO";
  if (s >= 0.5) return "ALTO";
  if (s >= 0.3) return "MEDIO";
  return "NORMAL";
}

function severityBar(s: number): string {
  const pct = Math.round(s * 100);
  const color = severityColor(s);
  return `<div style="background:#1a1a1a;border-radius:3px;height:6px;width:100%;margin-top:4px">
    <div style="background:${color};width:${pct}%;height:6px;border-radius:3px;transition:width 0.5s;box-shadow:0 0 6px ${color}88"></div>
  </div>`;
}

function renderDashboard() {
  const critical = allEvents.filter(e => e.local_severity >= 0.8);
  const high = allEvents.filter(e => e.local_severity >= 0.5 && e.local_severity < 0.8);
  const normal = allEvents.filter(e => e.local_severity < 0.5);
  const avgSev = allEvents.length ? allEvents.reduce((a,e) => a + e.local_severity, 0) / allEvents.length : 0;

  const statusColor = critical.length > 0 ? "#ff1a1a" : high.length > 0 ? "#ff6400" : "#32ff32";
  const statusText  = critical.length > 0 ? "ALERTA CRÍTICA" : high.length > 0 ? "ALERTA ALTA" : "SISTEMA NORMAL";

  const eventsHtml = allEvents.slice().reverse().map(ev => `
    <tr style="border-bottom:1px solid #1a1a1a">
      <td style="padding:8px 12px;color:#646464;font-size:11px">${new Date(ev.timestamp_ms || Date.now()).toLocaleTimeString("es-MX")}</td>
      <td style="padding:8px 12px;color:#00c8ff;font-size:11px">${ev.source_type.toUpperCase()}</td>
      <td style="padding:8px 12px;color:#e2e8f0;font-size:11px">${ev.event_type}</td>
      <td style="padding:8px 12px;color:#a0aec0;font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${ev.source}</td>
      <td style="padding:8px 12px;font-size:11px">
        <span style="color:${severityColor(ev.local_severity)};font-weight:bold">${severityLabel(ev.local_severity)}</span>
        <span style="color:#646464"> ${(ev.local_severity*100).toFixed(0)}%</span>
      </td>
      <td style="padding:8px 12px;color:#a0aec0;font-size:11px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${ev.raw}">${ev.raw.substring(0,60)}${ev.raw.length>60?"…":""}</td>
    </tr>
  `).join("");

  document.getElementById("app")!.innerHTML = `
    <div style="background:#080808;min-height:100vh;font-family:'Courier New',monospace;color:#e2e8f0">

      <!-- HEADER -->
      <div style="background:#0d0f14;border-bottom:1px solid #1a1a1a;padding:12px 24px;display:flex;align-items:center;justify-content:space-between">
        <div style="display:flex;align-items:center;gap:16px">
          <div style="width:10px;height:10px;background:#ff1a1a;border-radius:50%;box-shadow:0 0 8px #ff1a1a;animation:pulse 1.5s infinite"></div>
          <span style="color:#ff1a1a;font-weight:bold;letter-spacing:3px;font-size:16px">██ KALPIXK SIEM</span>
          <span style="color:#646464;font-size:11px">WebAssembly Blue Team SIEM · AMD Hackathon 2026</span>
        </div>
        <div style="text-align:right">
          <div style="color:${statusColor};font-weight:bold;font-size:12px">${statusText}</div>
          <div style="color:#646464;font-size:10px" id="wasm-ver">${wasmReady ? "WASM ✅ ACTIVO" : "Cargando WASM..."}</div>
        </div>
      </div>

      <!-- KPIs -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:24px">
        <div style="background:#0d0f14;border:1px solid #1a1a1a;border-radius:8px;padding:20px">
          <div style="color:#646464;font-size:11px;margin-bottom:8px">EVENTOS ANALIZADOS</div>
          <div style="color:#00c8ff;font-size:32px;font-weight:bold">${allEvents.length}</div>
          <div style="color:#646464;font-size:10px">por el motor WASM</div>
        </div>
        <div style="background:#0d0f14;border:1px solid ${critical.length>0?'#ff1a1a':'#1a1a1a'};border-radius:8px;padding:20px;${critical.length>0?'box-shadow:0 0 12px #ff1a1a44':''}">
          <div style="color:#646464;font-size:11px;margin-bottom:8px">ALERTAS CRÍTICAS</div>
          <div style="color:#ff1a1a;font-size:32px;font-weight:bold">${critical.length}</div>
          <div style="color:#646464;font-size:10px">severidad ≥ 80%</div>
        </div>
        <div style="background:#0d0f14;border:1px solid #1a1a1a;border-radius:8px;padding:20px">
          <div style="color:#646464;font-size:11px;margin-bottom:8px">ALERTAS ALTAS</div>
          <div style="color:#ff6400;font-size:32px;font-weight:bold">${high.length}</div>
          <div style="color:#646464;font-size:10px">severidad 50-79%</div>
        </div>
        <div style="background:#0d0f14;border:1px solid #1a1a1a;border-radius:8px;padding:20px">
          <div style="color:#646464;font-size:11px;margin-bottom:8px">SEVERIDAD PROMEDIO</div>
          <div style="color:${severityColor(avgSev)};font-size:32px;font-weight:bold">${(avgSev*100).toFixed(0)}%</div>
          ${severityBar(avgSev)}
        </div>
      </div>

      <!-- TABLA DE EVENTOS -->
      <div style="padding:0 24px 24px">
        <div style="background:#0d0f14;border:1px solid #1a1a1a;border-radius:8px;overflow:hidden">
          <div style="padding:16px 20px;border-bottom:1px solid #1a1a1a;display:flex;align-items:center;justify-content:space-between">
            <span style="color:#e2e8f0;font-weight:bold">🔴 EVENTOS EN TIEMPO REAL</span>
            <div style="display:flex;gap:8px">
              <button onclick="simulateLive()" style="background:#ff1a1a22;border:1px solid #ff1a1a44;color:#ff1a1a;padding:6px 14px;border-radius:4px;cursor:pointer;font-family:monospace;font-size:11px">▶ SIMULAR ATAQUE</button>
              <button onclick="clearEvents()" style="background:#1a1a1a;border:1px solid #333;color:#646464;padding:6px 14px;border-radius:4px;cursor:pointer;font-family:monospace;font-size:11px">⟳ LIMPIAR</button>
            </div>
          </div>
          <div style="overflow-x:auto">
            <table style="width:100%;border-collapse:collapse">
              <thead>
                <tr style="background:#111">
                  <th style="padding:10px 12px;color:#646464;font-size:10px;text-align:left;font-weight:normal">HORA</th>
                  <th style="padding:10px 12px;color:#646464;font-size:10px;text-align:left;font-weight:normal">FUENTE</th>
                  <th style="padding:10px 12px;color:#646464;font-size:10px;text-align:left;font-weight:normal">TIPO</th>
                  <th style="padding:10px 12px;color:#646464;font-size:10px;text-align:left;font-weight:normal">IP ORIGEN</th>
                  <th style="padding:10px 12px;color:#646464;font-size:10px;text-align:left;font-weight:normal">SEVERIDAD</th>
                  <th style="padding:10px 12px;color:#646464;font-size:10px;text-align:left;font-weight:normal">LOG ORIGINAL</th>
                </tr>
              </thead>
              <tbody id="events-body">
                ${eventsHtml || '<tr><td colspan="6" style="padding:40px;text-align:center;color:#646464">Cargando eventos...</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- CONSOLA WASM -->
      <div style="padding:0 24px 24px">
        <div style="background:#0d0f14;border:1px solid #1a1a1a;border-radius:8px;overflow:hidden">
          <div style="padding:12px 20px;border-bottom:1px solid #1a1a1a">
            <span style="color:#32ff32;font-size:12px">▌ CONSOLA MOTOR WASM</span>
          </div>
          <div id="wasm-console" style="padding:16px 20px;font-size:11px;color:#32ff32;min-height:100px;max-height:180px;overflow-y:auto;background:#050505">
            <div style="color:#646464">Iniciando motor WebAssembly...</div>
          </div>
        </div>
      </div>

      <!-- FOOTER -->
      <div style="padding:16px 24px;border-top:1px solid #1a1a1a;display:flex;justify-content:space-between;align-items:center">
        <span style="color:#646464;font-size:10px">Kalpixk SIEM · WebAssembly Zero-Install · AMD MI300X · Hackathon Mayo 9-10, 2026</span>
        <span style="color:#646464;font-size:10px">Motor: Rust→WASM · Parsers: syslog/db2/windows/netflow/json · Features: 32 dims</span>
      </div>

    </div>

    <style>
      @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
      * { box-sizing: border-box; }
      ::-webkit-scrollbar { width:6px; background:#0d0f14; }
      ::-webkit-scrollbar-thumb { background:#333; border-radius:3px; }
    </style>
  `;
}

function wasmLog(msg: string, color = "#32ff32") {
  const console_el = document.getElementById("wasm-console");
  if (!console_el) return;
  const ts = new Date().toLocaleTimeString("es-MX");
  console_el.innerHTML += `<div style="color:${color}">[${ts}] ${msg}</div>`;
  console_el.scrollTop = console_el.scrollHeight;
}

function addEvent(raw: string, sourceType: string) {
  if (!wasmReady) return;
  const result = parse_log_line(raw, sourceType);
  if (result) {
    const ev = JSON.parse(result) as ParsedEvent;
    ev.raw = raw;
    ev.timestamp_ms = ev.timestamp_ms || Date.now();
    allEvents.push(ev);
    const sev = (ev.local_severity * 100).toFixed(0);
    const color = severityColor(ev.local_severity);
    wasmLog(`[WASM] ${sourceType.toUpperCase()} → ${ev.event_type} | IP: ${ev.source} | Severidad: ${sev}%`, color);
    renderDashboard();
  }
}

// Función global para el botón de simular
(window as any).simulateLive = function() {
  wasmLog("▶ Iniciando simulación de ataque SSH Brute Force + DB2 SQL Injection...", "#ff6400");
  let idx = 0;
  const interval = setInterval(() => {
    if (idx >= LOGS_DEMO.length) {
      clearInterval(interval);
      wasmLog("■ Simulación completada.", "#646464");
      return;
    }
    addEvent(LOGS_DEMO[idx].raw, LOGS_DEMO[idx].type);
    idx++;
  }, 600);
};

(window as any).clearEvents = function() {
  allEvents = [];
  wasmLog("⟳ Eventos limpiados. Listo para nueva simulación.", "#646464");
  renderDashboard();
};

async function main() {
  document.getElementById("app")!.innerHTML = `
    <div style="background:#080808;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:'Courier New',monospace">
      <div style="text-align:center">
        <div style="color:#ff1a1a;font-size:20px;letter-spacing:3px;margin-bottom:16px">██ KALPIXK SIEM</div>
        <div style="color:#32ff32;font-size:13px">Inicializando motor WebAssembly...</div>
        <div style="color:#646464;font-size:11px;margin-top:8px">Rust → WASM · Zero Install · AMD Hackathon 2026</div>
      </div>
    </div>`;

  try {
    await initWasm();
    wasmReady = true;
    const h = JSON.parse(health_check());
    
    renderDashboard();
    const verEl = document.getElementById("wasm-ver");
    if (verEl) verEl.textContent = `${version()} ✅`;

    wasmLog(`Motor listo: ${version()}`, "#32ff32");
    wasmLog(`Feature contract: ${h.contract_version} · Dimensiones: ${h.feature_dim}`, "#00c8ff");
    wasmLog(`Parsers activos: syslog · json · windows · db2 · netflow`, "#00c8ff");
    wasmLog(`Presiona ▶ SIMULAR ATAQUE para ver el motor en acción`, "#646464");

    // Cargar los 12 eventos demo automáticamente con delay
    let idx = 0;
    const autoLoad = setInterval(() => {
      if (idx >= LOGS_DEMO.length) { clearInterval(autoLoad); return; }
      addEvent(LOGS_DEMO[idx].raw, LOGS_DEMO[idx].type);
      idx++;
    }, 300);

  } catch (err) {
    document.getElementById("app")!.innerHTML = `
      <div style="background:#080808;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:'Courier New',monospace">
        <div style="text-align:center;padding:40px">
          <div style="color:#ff1a1a;font-size:18px;margin-bottom:16px">❌ Error inicializando WASM</div>
          <pre style="color:#646464;font-size:11px;text-align:left;background:#111;padding:16px;border-radius:4px">${err}</pre>
          <div style="color:#646464;font-size:11px;margin-top:16px">El binario WASM debe estar en web/src/wasm/kalpixk_core_bg.wasm</div>
        </div>
      </div>`;
    console.error(err);
  }
}

main();
