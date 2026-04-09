// Kalpixk SIEM Dashboard — motor WebAssembly en el browser
// AMD Hackathon Mayo 9-10, 2026

// Mostrar loading inmediatamente (antes de que cargue el WASM)
document.getElementById("app")!.innerHTML = `
  <div style="background:#080808;min-height:100vh;display:flex;
              align-items:center;justify-content:center;
              font-family:'Courier New',monospace">
    <div style="text-align:center">
      <div style="color:#ff1a1a;font-size:24px;letter-spacing:4px;
                  margin-bottom:20px">██ KALPIXK SIEM</div>
      <div style="color:#32ff32;font-size:13px" id="status-msg">
        Inicializando motor WebAssembly...
      </div>
      <div style="color:#646464;font-size:11px;margin-top:10px">
        Rust → WASM · Zero Install · AMD MI300X
      </div>
    </div>
  </div>`;

function setStatus(msg: string, color = "#32ff32") {
  const el = document.getElementById("status-msg");
  if (el) el.innerHTML = `<span style="color:${color}">${msg}</span>`;
}

// ─── Tipos ──────────────────────────────────────────────────────────────────
interface ParsedEvent {
  event_type: string;
  local_severity: number;
  source: string;
  user: string | null;
  source_type: string;
  timestamp_ms: number;
  raw: string;
}

// ─── Estado global ──────────────────────────────────────────────────────────
let events: ParsedEvent[] = [];
let wasmParseFn: ((raw: string, type: string) => string | null | undefined) | null = null;
let wasmVersion = "desconocida";

// ─── Logs de demo (12 escenarios reales) ────────────────────────────────────
const DEMO_LOGS = [
  { raw: "Apr  5 02:14:22 cancun-srv01 sshd[1234]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:23 cancun-srv01 sshd[1235]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:24 cancun-srv01 sshd[1236]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:25 cancun-srv01 sshd[1237]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "Apr  5 02:14:26 cancun-srv01 sshd[1238]: Failed password for root from 45.33.32.156 port 22", type: "syslog" },
  { raw: "TIMESTAMP=2026-04-05-02.15.00 AUTHID=CEDIS_USR HOSTNAME=185.220.101.35 OPERATION=DDL STATEMENT=DROP TABLE NOMINAS", type: "db2" },
  { raw: "Apr  5 10:00:00 cancun-srv01 sshd[1]: Accepted publickey for jjuarez from 192.168.1.50 port 44321", type: "syslog" },
  { raw: "Apr  5 03:00:00 cancun-srv01 sudo[888]: jjuarez : TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=/bin/bash", type: "syslog" },
  { raw: "Apr  5 04:22:10 cancun-srv01 kernel: [UFW BLOCK] IN=eth0 OUT= SRC=45.33.32.156 DST=10.0.0.5 PROTO=TCP DPT=3389", type: "syslog" },
  { raw: "TIMESTAMP=2026-04-05-03.00.00 AUTHID=SYS HOSTNAME=10.0.0.5 OPERATION=SELECT STATEMENT=SELECT * FROM EMPLEADOS WHERE SALARIO > 50000", type: "db2" },
  { raw: "Apr  5 05:11:00 cancun-srv01 sshd[999]: Failed password for admin from 203.0.113.45 port 22", type: "syslog" },
  { raw: "Apr  5 06:00:01 cancun-srv01 sshd[1300]: Failed password for root from 45.33.32.157 port 22", type: "syslog" },
];

// ─── Helpers de UI ──────────────────────────────────────────────────────────
function sevColor(s: number) {
  if (s >= 0.8) return "#ff1a1a";
  if (s >= 0.5) return "#ff6400";
  if (s >= 0.3) return "#f59e0b";
  return "#32ff32";
}
function sevLabel(s: number) {
  if (s >= 0.8) return "CRÍTICO";
  if (s >= 0.5) return "ALTO";
  if (s >= 0.3) return "MEDIO";
  return "NORMAL";
}
function sevBar(s: number) {
  const pct = Math.round(s * 100);
  const c = sevColor(s);
  return `<div style="background:#1a1a1a;border-radius:3px;height:5px;margin-top:4px">
    <div style="background:${c};width:${pct}%;height:5px;border-radius:3px;box-shadow:0 0 6px ${c}88;transition:width .4s"></div>
  </div>`;
}

// ─── Render principal ────────────────────────────────────────────────────────
function render() {
  const crit  = events.filter(e => e.local_severity >= 0.8);
  const high  = events.filter(e => e.local_severity >= 0.5 && e.local_severity < 0.8);
  const avg   = events.length ? events.reduce((a,e) => a + e.local_severity, 0) / events.length : 0;
  const stColor = crit.length ? "#ff1a1a" : high.length ? "#ff6400" : "#32ff32";
  const stText  = crit.length ? "⚠ ALERTA CRÍTICA" : high.length ? "⚠ ALERTA ALTA" : "● SISTEMA NORMAL";

  const rows = [...events].reverse().map(ev => `
    <tr style="border-bottom:1px solid #111;transition:background .2s" onmouseover="this.style.background='#111'" onmouseout="this.style.background='transparent'">
      <td style="padding:8px 12px;color:#646464;font-size:11px;white-space:nowrap">${new Date(ev.timestamp_ms || Date.now()).toLocaleTimeString("es-MX")}</td>
      <td style="padding:8px 12px;color:#00c8ff;font-size:11px">${ev.source_type.toUpperCase()}</td>
      <td style="padding:8px 12px;color:#e2e8f0;font-size:11px">${ev.event_type}</td>
      <td style="padding:8px 12px;color:#a0aec0;font-size:11px">${ev.source}</td>
      <td style="padding:8px 12px;font-size:11px;min-width:110px">
        <span style="color:${sevColor(ev.local_severity)};font-weight:bold">${sevLabel(ev.local_severity)}</span>
        <span style="color:#646464"> ${(ev.local_severity*100).toFixed(0)}%</span>
        ${sevBar(ev.local_severity)}
      </td>
      <td style="padding:8px 12px;color:#646464;font-size:10px;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${ev.raw.replace(/"/g,"&quot;")}">${ev.raw.substring(0,65)}${ev.raw.length>65?"…":""}</td>
    </tr>`).join("");

  document.getElementById("app")!.innerHTML = `
    <style>
      *{box-sizing:border-box;margin:0;padding:0}
      body{background:#080808}
      @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
      ::-webkit-scrollbar{width:5px;background:#0d0f14}
      ::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:3px}
    </style>

    <div style="background:#080808;min-height:100vh;font-family:'Courier New',monospace;color:#e2e8f0">

      <!-- HEADER -->
      <div style="background:#0a0c10;border-bottom:1px solid #1a1a1a;padding:10px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px">
        <div style="display:flex;align-items:center;gap:12px">
          <div style="width:8px;height:8px;background:#ff1a1a;border-radius:50%;box-shadow:0 0 8px #ff1a1a;animation:pulse 1.5s infinite"></div>
          <span style="color:#ff1a1a;font-weight:bold;letter-spacing:3px;font-size:15px">██ KALPIXK SIEM</span>
          <span style="color:#444;font-size:10px">WebAssembly · Zero Install · AMD Hackathon 2026</span>
        </div>
        <div style="text-align:right">
          <div style="color:${stColor};font-size:11px;font-weight:bold">${stText}</div>
          <div style="color:#444;font-size:9px">Motor: ${wasmVersion}</div>
        </div>
      </div>

      <!-- KPIs -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:16px 20px">
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;padding:16px">
          <div style="color:#555;font-size:10px;margin-bottom:6px">EVENTOS ANALIZADOS</div>
          <div style="color:#00c8ff;font-size:28px;font-weight:bold">${events.length}</div>
          <div style="color:#444;font-size:9px">motor WASM real</div>
        </div>
        <div style="background:#0a0c10;border:1px solid ${crit.length?"#ff1a1a44":"#1a1a1a"};border-radius:6px;padding:16px;${crit.length?"box-shadow:0 0 12px #ff1a1a22":""}">
          <div style="color:#555;font-size:10px;margin-bottom:6px">CRÍTICOS ≥80%</div>
          <div style="color:#ff1a1a;font-size:28px;font-weight:bold">${crit.length}</div>
          <div style="color:#444;font-size:9px">requieren acción inmediata</div>
        </div>
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;padding:16px">
          <div style="color:#555;font-size:10px;margin-bottom:6px">ALERTAS ALTAS</div>
          <div style="color:#ff6400;font-size:28px;font-weight:bold">${high.length}</div>
          <div style="color:#444;font-size:9px">severidad 50-79%</div>
        </div>
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;padding:16px">
          <div style="color:#555;font-size:10px;margin-bottom:6px">SEVERIDAD PROMEDIO</div>
          <div style="color:${sevColor(avg)};font-size:28px;font-weight:bold">${(avg*100).toFixed(0)}%</div>
          ${sevBar(avg)}
        </div>
      </div>

      <!-- TABLA -->
      <div style="padding:0 20px 16px">
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;overflow:hidden">
          <div style="padding:12px 16px;border-bottom:1px solid #1a1a1a;display:flex;align-items:center;justify-content:space-between">
            <span style="color:#e2e8f0;font-size:12px;font-weight:bold">🔴 EVENTOS EN TIEMPO REAL</span>
            <div style="display:flex;gap:8px">
              <button id="btn-sim" onclick="window._simAtaque()" style="background:#ff1a1a18;border:1px solid #ff1a1a44;color:#ff1a1a;padding:5px 12px;border-radius:4px;cursor:pointer;font-family:monospace;font-size:10px">▶ SIMULAR ATAQUE</button>
              <button onclick="window._clear()" style="background:#1a1a1a;border:1px solid #222;color:#555;padding:5px 12px;border-radius:4px;cursor:pointer;font-family:monospace;font-size:10px">⟳ LIMPIAR</button>
            </div>
          </div>
          <div style="overflow-x:auto;max-height:340px;overflow-y:auto">
            <table style="width:100%;border-collapse:collapse">
              <thead style="position:sticky;top:0;background:#0d0f14;z-index:1">
                <tr>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left;font-weight:normal;white-space:nowrap">HORA</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left;font-weight:normal">FUENTE</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left;font-weight:normal">TIPO EVENTO</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left;font-weight:normal">IP ORIGEN</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left;font-weight:normal">SEVERIDAD</th>
                  <th style="padding:8px 12px;color:#444;font-size:9px;text-align:left;font-weight:normal">LOG ORIGINAL</th>
                </tr>
              </thead>
              <tbody>${rows || '<tr><td colspan="6" style="padding:32px;text-align:center;color:#444;font-size:11px">Motor WASM listo — presiona ▶ SIMULAR ATAQUE</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- CONSOLA -->
      <div style="padding:0 20px 16px">
        <div style="background:#0a0c10;border:1px solid #1a1a1a;border-radius:6px;overflow:hidden">
          <div style="padding:10px 16px;border-bottom:1px solid #1a1a1a">
            <span style="color:#32ff32;font-size:11px">▌ CONSOLA WASM</span>
          </div>
          <div id="wasm-log" style="padding:12px 16px;font-size:10px;color:#32ff32;min-height:80px;max-height:140px;overflow-y:auto;background:#050505;line-height:1.6"></div>
        </div>
      </div>

      <!-- FOOTER -->
      <div style="padding:10px 20px;border-top:1px solid #111;display:flex;justify-content:space-between">
        <span style="color:#333;font-size:9px">Kalpixk SIEM · Rust→WebAssembly · Parsers: syslog/db2/windows/netflow/json · 32 features</span>
        <span style="color:#333;font-size:9px">AMD Hackathon · Mayo 9-10, 2026 · <a href="https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps" style="color:#444">GitHub</a></span>
      </div>

    </div>`;
}

function wasmLog(msg: string, color = "#32ff32") {
  const el = document.getElementById("wasm-log");
  if (!el) return;
  const ts = new Date().toLocaleTimeString("es-MX");
  el.innerHTML += `<div><span style="color:#444">[${ts}]</span> <span style="color:${color}">${msg}</span></div>`;
  el.scrollTop = el.scrollHeight;
}

function addEvent(raw: string, type: string) {
  if (!wasmParseFn) return;
  try {
    const result = wasmParseFn(raw, type);
    if (!result) { wasmLog(`[skip] sin match: ${raw.substring(0,50)}`, "#444"); return; }
    const ev = JSON.parse(result) as ParsedEvent;
    ev.raw = raw;
    ev.timestamp_ms = ev.timestamp_ms || Date.now();
    events.push(ev);
    wasmLog(`${type.toUpperCase()} → ${ev.event_type} | ${ev.source} | ${(ev.local_severity*100).toFixed(0)}%`, sevColor(ev.local_severity));
    render();
  } catch (e) {
    wasmLog(`[error] ${e}`, "#ff1a1a");
  }
}

// Funciones globales para los botones
(window as any)._simAtaque = () => {
  events = [];
  wasmLog("▶ Iniciando simulación: SSH BruteForce + DB2 SQL + Privilege Escalation...", "#ff6400");
  let i = 0;
  const iv = setInterval(() => {
    if (i >= DEMO_LOGS.length) { clearInterval(iv); wasmLog("■ Simulación completada.", "#555"); return; }
    addEvent(DEMO_LOGS[i].raw, DEMO_LOGS[i].type);
    i++;
  }, 500);
};
(window as any)._clear = () => { events = []; wasmLog("⟳ Limpiado.", "#555"); render(); };

// ─── Inicializar WASM ────────────────────────────────────────────────────────
async function main() {
  try {
    setStatus("Cargando módulo WebAssembly...");

    // Import dinámico — el path se resuelve en build time por Vite
    const wasmModule = await import("./wasm/index");
    await wasmModule.initWasm();

    wasmVersion = wasmModule.version();
    wasmParseFn = wasmModule.parse_log_line;

    // Renderizar dashboard vacío
    render();

    // Log inicial
    const health = JSON.parse(wasmModule.health_check());
    wasmLog(`Motor listo: ${wasmVersion}`, "#32ff32");
    wasmLog(`Contract: ${health.contract_version} · Dims: ${health.feature_dim} · Status: ${health.status}`, "#00c8ff");
    wasmLog(`Parsers: syslog · db2 · windows · netflow · json`, "#00c8ff");
    wasmLog(`Presiona ▶ SIMULAR ATAQUE o espera la carga automática...`, "#555");

    // Autoload con delay
    let i = 0;
    const iv = setInterval(() => {
      if (i >= DEMO_LOGS.length) { clearInterval(iv); return; }
      addEvent(DEMO_LOGS[i].raw, DEMO_LOGS[i].type);
      i++;
    }, 350);

  } catch (err: any) {
    console.error("[Kalpixk] Error WASM:", err);
    document.getElementById("app")!.innerHTML = `
      <div style="background:#080808;min-height:100vh;display:flex;align-items:center;
                  justify-content:center;font-family:'Courier New',monospace">
        <div style="text-align:center;padding:40px;max-width:600px">
          <div style="color:#ff1a1a;font-size:18px;margin-bottom:20px">❌ Error cargando motor WASM</div>
          <pre style="color:#555;font-size:10px;text-align:left;background:#0d0f14;
                      padding:16px;border-radius:4px;overflow:auto;max-height:200px">${err?.message || err}</pre>
          <div style="color:#444;font-size:10px;margin-top:20px">
            Este dashboard requiere un browser moderno con soporte WebAssembly.<br/>
            Chrome 90+, Firefox 89+, Safari 15+, Edge 90+
          </div>
          <div style="margin-top:16px">
            <a href="https://not-yet-named-user-skipped-to-sp-15105d41.base44.app/KalpixkDashboard"
               style="color:#ff6400;font-size:11px">
              → Ver dashboard offline en Base44
            </a>
          </div>
        </div>
      </div>`;
  }
}

main();
