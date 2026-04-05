import { initWasm, parse_log_line, version } from './wasm/index'

async function main() {
  await initWasm()

  // Verificar que el WASM funciona
  const result = parse_log_line(
    "Apr 5 02:14:22 server sshd[123]: Failed password for root from 45.33.32.156 port 22",
    "syslog"
  )

  if (result) {
    const event = JSON.parse(result)
    console.log('[Kalpixk] Test WASM OK:', event.event_type, 'score:', event.local_severity)
    document.getElementById('app')!.innerHTML = `
      <div style="font-family:monospace;padding:20px;background:#0d0f14;color:#14b8a6;min-height:100vh">
        <h1>Kalpixk SIEM v${version()}</h1>
        <p>Motor WASM: ✅ Funcionando</p>
        <p>Evento detectado: ${event.event_type}</p>
        <p>Severidad: ${(event.local_severity * 100).toFixed(0)}%</p>
        <p><a href="/dashboard/index.html" style="color:#f59e0b">→ Abrir dashboard completo</a></p>
      </div>
    `
  }
}

main().catch(console.error)
