// ATLATL-ORDNANCE: Kalpixk Control Center — Dashboard Logic
// Military-Grade Anomaly Detection Dashboard with WASM Edge Integration

import initWasmModule, { parse_and_extract, health_check, get_security_telemetry } from './pkg/kalpixk_core.js';

const API = window.location.origin;
let refreshInterval = null;
let wasmReady = false;

// ── WASM Initialization ─────────────────────────────────────
async function initWasm() {
    try {
        await initWasmModule();
        wasmReady = true;
        const health = JSON.parse(health_check());
        log(`WASM Edge Ready: ${health.module} v${health.contract_version}`, 'ok');
        document.getElementById('wasm-status').textContent = '● WASM_ACTIVE';
        document.getElementById('wasm-status').className = 'text-[10px] status-ok blink';
    } catch (e) {
        log(`WASM_LOAD_FAILURE: ${e.message}`, 'error');
        document.getElementById('wasm-status').textContent = '● WASM_OFFLINE';
        document.getElementById('wasm-status').className = 'text-[10px] status-error';
    }
}

// ── Clock ──────────────────────────────────────────────────
function updateClock() {
    document.getElementById('clock').textContent =
        new Date().toLocaleTimeString('es-MX', { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

// ── Log Terminal ───────────────────────────────────────────
function log(msg, type = 'ok') {
    const colors = { ok: '#00FF00', error: '#FF0000', warn: '#FF8C00', info: '#00FFFF' };
    const el = document.getElementById('log');
    const line = document.createElement('div');
    const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });

    line.style.color = colors[type] || colors.ok;
    line.textContent = `[${ts}] ${msg}`;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
    while (el.children.length > 100) el.removeChild(el.firstChild);
}

// ── API helpers ────────────────────────────────────────────
async function apiFetch(endpoint, opts = {}) {
    try {
        const r = await fetch(`${API}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...opts
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return await r.json();
    } catch (e) {
        log(`COMM_FAILURE: ${e.message}`, 'error');
        return null;
    }
}

// ── Health / Status ────────────────────────────────────────
async function refreshStatus() {
    const data = await apiFetch('/health');
    if (!data) {
        document.getElementById('conn-status').textContent = '● OFFLINE_DANGER';
        document.getElementById('conn-status').className = 'text-sm status-error blink';
        return;
    }
    document.getElementById('conn-status').textContent = '● SYSTEM_ARMOURED';
    document.getElementById('conn-status').className = 'text-sm status-ok blink';
    log(`Neural Core Status: ${data.status} | Engine: ${data.device}`, 'info');
}

async function refreshMetrics() {
    const data = await apiFetch('/metrics');
    if (!data) return;

    const m = data.metrics;
    document.getElementById('cpu-pct').textContent = m.cpu_usage?.toFixed(1) + '%' || '--';
    document.getElementById('ram-pct').textContent = m.heap_usage?.toFixed(1) + '%' || '--';

    const score = data.detection?.reconstruction_errors?.[0] ?? 0;
    const isAnomaly = data.detection?.anomalies?.[0] ?? false;
    const threshold = data.detection?.threshold ?? 0.5;

    document.getElementById('score-val').textContent = score.toFixed(6);
    const pct = Math.min(100, (score / Math.max(threshold * 3, 0.1)) * 100);
    document.getElementById('score-bar').style.width = pct + '%';

    if (isAnomaly) {
        document.getElementById('anomaly-status').textContent = 'THREAT!';
        document.getElementById('anomaly-status').className = 'text-xl font-bold status-error blink';
        log(`🚨 THREAT_VECTOR DETECTED! SCORE: ${score.toFixed(6)}`, 'error');

        // ATLATL-ORDNANCE: Trigger Phase Black UI if score is critical
        if (score > threshold * 2) {
            document.getElementById('black-overlay').style.display = 'block';
            log('💀 PHASE BLACK: RETALIATION SEQUENCE ACTIVE', 'error');
        }
    } else {
        document.getElementById('anomaly-status').textContent = 'CLEAN';
        document.getElementById('anomaly-status').className = 'text-xl font-bold status-ok';
        document.getElementById('black-overlay').style.display = 'none';
    }

    if (wasmReady) {
        // Telemetry check (if implemented in WASM)
        try {
            const telemetry = JSON.parse(get_security_telemetry());
            if (telemetry.threat_level === 'high') {
                log(`⚠️ WASM Edge reports HIGH SHARED_ACCESS_COUNT: ${telemetry.shared_access_count}`, 'warn');
            }
        } catch(e) {}
    }
}

// ── WASM Processing Example ────────────────────────────────
async function processLocalLog(rawJson) {
    if (!wasmReady) return;
    try {
        log('> WASM_EDGE: Parsing local log vector...', 'info');
        const result = JSON.parse(parse_and_extract(rawJson));
        log(`> WASM_EXTRACT: ${result.event_type} | Severity: ${result.local_severity}`, 'ok');
        return result.features;
    } catch (e) {
        log(`WASM_EXEC_ERROR: ${e}`, 'error');
    }
}

// ── Acciones ───────────────────────────────────────────────
async function runDetect() {
    log('> THREAD_SCAN SEQUENCE INITIATED...', 'info');

    // Simulate local WASM parsing before sending to GPU
    const mockLog = JSON.stringify({
        timestamp_ms: Date.now(),
        event_type: "FileAccess",
        local_severity: 0.1,
        source: "127.0.0.1",
        source_type: "syslog",
        raw: "Feb 10 10:00:00 server sshd[123]: Accepted password for root"
    });

    await processLocalLog(mockLog);
    await refreshMetrics();
}

async function runTrain() {
    log('> RE-OPTIMIZING NEURAL WEIGHTS ON MI300X...', 'warn');
    const data = await apiFetch('/train', { method: 'POST' });
    if (data?.success) {
        log('> NEURAL CALIBRATION COMPLETE ✅', 'ok');
    }
}

async function simulateAnomaly(type) {
    log(`> SIMULATING AGGRESSION VECTOR: ${type}`, 'warn');
    const data = await apiFetch(`/simulate/${type}`);
    if (data) {
        const detected = data.detected;
        const score = data.detection?.reconstruction_errors?.[0]?.toFixed(6);
        log(`> RESULT: ${detected ? 'THREAT_NEUTRALIZED 🚨' : 'SYSTEM_UNAWARE'} | Score: ${score}`,
            detected ? 'error' : 'warn');
    }
}

function updateThreshold(val) {
    document.getElementById('threshold-val').textContent = parseFloat(val).toFixed(1);
    log(`> AGGRESSION_THRESHOLD UPDATED: ${val}`, 'info');
}

// ── Auto-refresh ────────────────────────────────────────────
async function init() {
    log('> ATLATL-ORDNANCE: GUERRILLA ALGORÍTMICA LOADED', 'ok');
    await initWasm();
    log('> CONNECTING TO MI300X NEURAL ARRAY...', 'info');
    await refreshStatus();
    await refreshMetrics();
    refreshInterval = setInterval(async () => {
        await refreshMetrics();
    }, 5000);
    log('> ACTIVE_MONITORING: ON (5000ms latency)', 'ok');
}

init();
