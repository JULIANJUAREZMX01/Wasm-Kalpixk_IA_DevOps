import { initWasm, parse_log_line, process_batch, version, health_check } from "./wasm/index";

const C = {
  bg: "#080808", green: "#32ff32", red: "#ff1a1a",
  orange: "#ff6400", cyan: "#00c8ff", gray: "#646464",
};

function render(content: string) {
  document.getElementById("app")!.innerHTML = content;
}

async function main() {
  render(`<div style="padding:20px;color:${C.cyan}">⏳ Cargando motor WASM...</div>`);

  try {
    await initWasm();

    const health = JSON.parse(health_check());

    // Test 1: SSH Brute Force
    const r1 = parse_log_line(
      "Apr  5 02:14:22 cancun-srv01 sshd[1234]: Failed password for root from 45.33.32.156 port 22",
      "syslog"
    );
    const ev1 = r1 ? JSON.parse(r1) : null;

    // Test 2: DROP TABLE DB2
    const r2 = parse_log_line(
      "TIMESTAMP=2026-04-05-02.15.00 AUTHID=CEDIS_USR HOSTNAME=185.220.101.35 OPERATION=DDL STATEMENT=DROP TABLE NOMINAS",
      "db2"
    );
    const ev2 = r2 ? JSON.parse(r2) : null;

    // Test 3: Batch de logs
    const batch = JSON.parse(process_batch(
      JSON.stringify([
        "Apr  5 10:00:00 server sshd[1]: Accepted publickey for jjuarez from 192.168.1.50",
        "Apr  5 02:00:00 server sshd[2]: Failed password for root from 45.33.32.156",
        "Apr  5 03:11:00 server sshd[3]: Failed password for admin from 203.0.113.45",
      ]),
      "syslog"
    ));

    render(`
      <div style="background:${C.bg};min-height:100vh;padding:24px;font-family:'Courier New',monospace">
        <h1 style="color:${C.red};letter-spacing:3px;text-shadow:0 0 12px ${C.red}">
          ██ KALPIXK SIEM
        </h1>
        <p style="color:${C.gray}">WASM-native Blue Team SIEM · AMD MI300X · Hackathon 2026</p>
        <hr style="border-color:#1a1a1a;margin:16px 0"/>

        <h2 style="color:${C.green}">✅ Motor WASM: ${version()}</h2>
        <p style="color:${C.gray}">Feature dim: ${health.feature_dim} · Contract: ${health.contract_version}</p>

        <hr style="border-color:#1a1a1a;margin:16px 0"/>
        <h3 style="color:${C.orange}">🧪 Test 1 — SSH Brute Force (syslog)</h3>
        ${ev1 ? `
          <p style="color:${C.green}">✅ Evento detectado:</p>
          <pre style="color:${C.cyan};background:#111;padding:12px;border-radius:4px">
event_type: ${ev1.event_type}
severity:   ${(ev1.local_severity * 100).toFixed(0)}%
source:     ${ev1.source}
user:       ${ev1.user || "—"}
          </pre>
        ` : `<p style="color:${C.red}">❌ No parseado</p>`}

        <h3 style="color:${C.orange}">🧪 Test 2 — DROP TABLE DB2</h3>
        ${ev2 ? `
          <p style="color:${C.green}">✅ Evento detectado:</p>
          <pre style="color:${C.cyan};background:#111;padding:12px;border-radius:4px">
event_type: ${ev2.event_type}
severity:   ${(ev2.local_severity * 100).toFixed(0)}%
source:     ${ev2.source}
user:       ${ev2.user || "—"}
          </pre>
        ` : `<p style="color:${C.red}">❌ No parseado</p>`}

        <h3 style="color:${C.orange}">🧪 Test 3 — Batch de ${batch.parsed_count} logs</h3>
        <p style="color:${C.green}">
          ✅ ${batch.parsed_count} parseados · 
          ${batch.anomaly_count} anomalías · 
          ${batch.feature_matrix[0]?.length || 0} features/evento
        </p>

        <hr style="border-color:#1a1a1a;margin:16px 0"/>
        <p style="color:${C.gray}">
          <a href="/dashboard/index.html" style="color:${C.orange}">→ Dashboard completo</a>
        </p>
      </div>
    `);
  } catch (err) {
    render(`<div style="padding:20px;color:#ff1a1a">
      ❌ Error cargando WASM: ${err}<br/>
      <small style="color:#646464">Asegúrate de haber compilado: cd crates/kalpixk-core && wasm-pack build --target web --release</small>
    </div>`);
    console.error(err);
  }
}

main();
