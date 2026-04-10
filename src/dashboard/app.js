// ATLATL-ORDNANCE: Dashboard Logic v2.2
// Implementation of SACITY aesthetic and WASM Heartbeat

import initWasmModule, {
    health_check,
    get_security_telemetry,
    parse_log_line,
    analyze_and_retaliate
} from './pkg/kalpixk_core.js';

const API = window.location.origin;
let wasmReady = false;
let heartbeatInterval = null;
let lastHeartbeat = 0;

// ── WASM Initialization ─────────────────────────────────────
async function initWasm() {
    try {
        await initWasmModule();
        wasmReady = true;
        const health = JSON.parse(health_check());
        log(`WASM Core Armoured: ${health.atlatl_ordnance}`, 'info');
        document.getElementById('wasm-status').textContent = '● WASM_ACTIVE';
        document.getElementById('wasm-status').className = 'text-[10px] status-ok';

        // Start Heartbeat
        startHeartbeat();
    } catch (e) {
        log(`CRITICAL_WASM_FAILURE: ${e.message}`, 'error');
        document.getElementById('wasm-status').textContent = '● WASM_TAMPERED';
        document.getElementById('wasm-status').className = 'text-[10px] status-error';
    }
}

// ── Heartbeat Mechanism ──────────────────────────────────────
function startHeartbeat() {
    heartbeatInterval = setInterval(() => {
        if (!wasmReady) return;
        try {
            const telemetry = JSON.parse(get_security_telemetry());
            const hb = telemetry.heartbeat;

            document.getElementById('hb-val').textContent = hb;

            if (hb === lastHeartbeat && hb > 0) {
                log('WARNING: WASM Runtime Stalled! Possible Tampering.', 'warn');
                document.getElementById('wasm-integrity').textContent = 'STALLED';
                document.getElementById('wasm-integrity').className = 'text-2xl font-bold status-error';
            } else {
                document.getElementById('wasm-integrity').textContent = 'VERIFIED';
                document.getElementById('wasm-integrity').className = 'text-2xl font-bold status-ok';
            }
            lastHeartbeat = hb;
        } catch (e) {
            log(`HEARTBEAT_LOST: ${e.message}`, 'error');
        }
    }, 2000);
}

// ── Log Terminal ───────────────────────────────────────────
function log(msg, type = 'ok') {
    const el = document.getElementById('log-terminal');
    const line = document.createElement('div');
    const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });

    const classes = {
        ok: 'status-ok',
        error: 'status-error',
        warn: 'status-warn',
        info: 'status-info'
    };

    line.className = classes[type] || 'status-ok';
    line.innerHTML = `<span class="text-gray-600">[${ts}]</span> ${msg}`;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;

    if (el.children.length > 100) el.removeChild(el.firstChild);
}

// ── API helpers ────────────────────────────────────────────
async function apiFetch(endpoint, opts = {}) {
    try {
        const response = await fetch(`${API}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                'X-Kalpixk-Key': localStorage.getItem('kalpixk_key') || 'development'
            },
            ...opts
        });
        if (!response.ok) throw new Error(`HTTP_${response.status}`);
        return await response.json();
    } catch (e) {
        log(`COMM_FAILURE: ${e.message}`, 'error');
        return null;
    }
}

// ── Metrics & Anomaly Logic ─────────────────────────────────
async function refreshMetrics() {
    const data = await apiFetch('/api/v1/metrics');
    if (!data) return;

    const score = data.detection.reconstruction_errors[0];
    const threshold = data.detection.threshold || 0.7;

    updateScoreUI(score, threshold);

    if (score > threshold) {
        triggerPhaseBlack(score);
    } else {
        document.getElementById('black-overlay').style.display = 'none';
        document.getElementById('anomaly-status').textContent = 'NOMINAL';
        document.getElementById('anomaly-status').className = 'text-2xl font-bold status-ok';
    }
}

function updateScoreUI(score, threshold) {
    const scorePct = Math.min(100, (score / (threshold * 2)) * 100);
    document.getElementById('score-progress').style.width = `${scorePct}%`;
    document.getElementById('score-text').textContent = score.toFixed(6);

    if (score > threshold) {
        document.getElementById('score-text').className = 'status-error font-mono text-sm blink';
    } else {
        document.getElementById('score-text').className = 'status-info font-mono text-sm';
    }
}

function triggerPhaseBlack(score) {
    document.getElementById('black-overlay').style.display = 'block';
    document.getElementById('anomaly-status').textContent = 'THREAT!';
    document.getElementById('anomaly-status').className = 'text-2xl font-bold status-error blink';
    log(`🚨 THREAT DETECTED: Reconstruction Error ${score.toFixed(6)}`, 'error');
    log('💀 PHASE BLACK: INITIATING RECURSIVE RETALIATION', 'error');
}

// ── UI Actions ──────────────────────────────────────────────
window.triggerScan = async () => {
    log('> Manual Thread Scan Sequence Initiated...', 'info');
    await refreshMetrics();
};

window.triggerRetaliationDemo = () => {
    log('> SIMULATING AGGRESSION VECTOR: Ransomware_Exploit', 'warn');
    triggerPhaseBlack(0.985421);
};

window.updateThreshold = (val) => {
    document.getElementById('threshold-val').textContent = val;
    log(`Aggression threshold recalibrated to: ${val}`, 'info');
};

// ── System Boot ─────────────────────────────────────────────
function updateClock() {
    document.getElementById('clock').textContent = new Date().toLocaleTimeString('es-MX', { hour12: false });
}

async function init() {
    updateClock();
    setInterval(updateClock, 1000);

    log('ATLATL-ORDNANCE: GUIERRILLA ALGORÍTMICA LOADED', 'info');
    await initWasm();

    // Initial data fetch
    await refreshMetrics();
    setInterval(refreshMetrics, 5000);
}

init();
