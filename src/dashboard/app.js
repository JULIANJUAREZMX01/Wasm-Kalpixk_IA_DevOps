// Kalpixk Control Center — Dashboard Logic
// Portado y extendido de nanobot-cloud/web/app.js

const API = window.location.origin;
let refreshInterval = null;

// ── Clock ──────────────────────────────────────────────────
function updateClock() {
  document.getElementById('clock').textContent =
    new Date().toLocaleTimeString('es-MX', {hour12: false});
}
setInterval(updateClock, 1000);
updateClock();

// ── Log Terminal ───────────────────────────────────────────
function log(msg, type = 'ok') {
  const colors = { ok: '#32ff32', error: '#ff1a1a', warn: '#ffaa00', info: '#00c8ff' };
  const el = document.getElementById('log');
  const line = document.createElement('div');
  const ts = new Date().toLocaleTimeString('es-MX', {hour12:false});
  line.style.color = colors[type] || colors.ok;
  line.textContent = `[${ts}] ${msg}`;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
  // Mantener max 100 líneas
  while (el.children.length > 100) el.removeChild(el.firstChild);
}

// ── API helpers ────────────────────────────────────────────
async function apiFetch(endpoint, opts = {}) {
  try {
    const r = await fetch(`${API}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...opts
    });
    return await r.json();
  } catch(e) {
    log(`API error: ${e.message}`, 'error');
    return null;
  }
}

// ── Health / Status ────────────────────────────────────────
async function refreshStatus() {
  const data = await apiFetch('/health');
  if (!data) {
    document.getElementById('conn-status').textContent = '● OFFLINE';
    document.getElementById('conn-status').className = 'text-sm status-error blink';
    return;
  }
  document.getElementById('conn-status').textContent = '● ONLINE';
  document.getElementById('conn-status').className = 'text-sm status-ok blink';
  document.getElementById('model-status').textContent = data.model_trained ? '✅ trained' : '❌ untrained';
  document.getElementById('model-status').className = `text-xs ${data.model_trained ? 'status-ok' : 'status-error'}`;
  log(`Health: ${data.status} | GPU: ${data.device}`, 'info');
}

async function refreshMetrics() {
  const data = await apiFetch('/metrics');
  if (!data) return;

  // CPU / RAM
  const m = data.metrics;
  document.getElementById('cpu-pct').textContent = m.cpu_usage?.toFixed(1) + '%' || '--';
  document.getElementById('ram-pct').textContent = m.heap_usage?.toFixed(1) + '%' || '--';

  // Anomaly score
  const score = data.detection?.reconstruction_errors?.[0] ?? 0;
  const isAnomaly = data.detection?.anomalies?.[0] ?? false;
  const threshold = data.detection?.threshold ?? 0.5;

  document.getElementById('score-val').textContent = score.toFixed(4);
  const pct = Math.min(100, (score / Math.max(threshold * 2, 1)) * 100);
  document.getElementById('score-bar').style.width = pct + '%';

  if (isAnomaly) {
    document.getElementById('anomaly-status').textContent = '⚠️ ANOMALY!';
    document.getElementById('anomaly-status').className = 'text-sm status-error blink';
    log(`🚨 ANOMALÍA! Score: ${score.toFixed(4)}`, 'error');
  } else {
    document.getElementById('anomaly-status').textContent = '✅ NORMAL';
    document.getElementById('anomaly-status').className = 'text-sm status-ok';
  }

  // Check notificaciones
  document.getElementById('tg-status').textContent = '✅ activo';
  document.getElementById('wa-status').textContent = '⚠️ config pending';
}

// ── Acciones ───────────────────────────────────────────────
async function runDetect() {
  log('> Corriendo detección...', 'info');
  await refreshMetrics();
  log('> Detección completada', 'ok');
}

async function runBenchmark() {
  log('> Iniciando benchmark AMD MI300X...', 'warn');
  const data = await apiFetch('/benchmark');
  if (data?.throughput) {
    log(`> Throughput: ${data.throughput.toLocaleString()} samples/sec`, 'ok');
    log(`> Device: ${data.device}`, 'info');
  }
}

async function runTrain() {
  log('> Re-entrenando modelo...', 'warn');
  const data = await apiFetch('/train', {method: 'POST'});
  if (data?.success) {
    log('> Entrenamiento completado ✅', 'ok');
  }
}

async function simulateAnomaly(type) {
  log(`> Simulando anomalía: ${type}`, 'warn');
  const data = await apiFetch(`/simulate/${type}`);
  if (data) {
    const detected = data.detected;
    log(`> Anomalía ${detected ? 'DETECTADA 🚨' : 'no detectada'} | Score: ${data.detection?.reconstruction_errors?.[0]?.toFixed(4)}`,
        detected ? 'error' : 'warn');
  }
}

function updateThreshold(val) {
  document.getElementById('threshold-val').textContent = parseFloat(val).toFixed(1);
  log(`> Threshold actualizado: ${val}`, 'info');
}

// ── Auto-refresh ────────────────────────────────────────────
async function init() {
  log('> Kalpixk Control Center iniciado', 'ok');
  log('> Conectando con API...', 'info');
  await refreshStatus();
  await refreshMetrics();
  refreshInterval = setInterval(async () => {
    await refreshMetrics();
  }, 10000); // refresh cada 10s
  log('> Auto-refresh activado (10s)', 'ok');
}

init();
