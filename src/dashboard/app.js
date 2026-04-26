// ATLATL-ORDNANCE: SACITY Dashboard Logic v3.0
// Implementation of SACITY aesthetic, CRT Effects, and WASM Heartbeat v3

import initWasmModule, {
    health_check,
    get_security_telemetry,
    get_global_blacklist_wasm,
    analyze_and_retaliate,
    version
} from './pkg/kalpixk_core.js';

const API = window.location.origin;
let wasmReady = false;

function escapeHTML(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, function(m) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[m];
    });
}
let heartbeatInterval = null;
let lastHeartbeat = 0;

// ── WASM Initialization ─────────────────────────────────────
async function initWasm() {
    try {
        await initWasmModule();
        wasmReady = true;
        const v = version();
        const health = JSON.parse(health_check());
        log(`SACITY GuerrillaMesh Armoured: ${v} [${health.atlatl_ordnance}]`, 'info');
        document.getElementById('wasm-status').textContent = '● WASP_V3_SECURE';
        document.getElementById('wasm-status').className = 'text-[10px] status-ok font-bold';

        // Start Heartbeat & Sync
        startHeartbeat();
        syncBlacklist();
    } catch (e) {
        log(`CRITICAL_WASM_FAILURE: ${e.message}`, 'error');
        document.getElementById('wasm-status').textContent = '● WASP_TAMPERED';
        document.getElementById('wasm-status').className = 'text-[10px] status-error font-bold glitch';
    }
}

// ── Heartbeat Mechanism (WASP v3) ──────────────────────────
function startHeartbeat() {
    heartbeatInterval = setInterval(() => {
        if (!wasmReady) return;
        try {
            const telemetry = JSON.parse(get_security_telemetry());
            const hb = telemetry.heartbeat;

            document.getElementById('hb-val').textContent = hb;

            if (hb === lastHeartbeat && hb > 0) {
                log('🚨 CRITICAL: WASM Runtime Stall Detected! Pointer Poisoning Initiated.', 'error');
                document.getElementById('anomaly-status').textContent = 'STALLED';
                document.getElementById('anomaly-status').className = 'text-2xl font-black status-error glitch';
                applyGlitchEffect();
            }
            lastHeartbeat = hb;
        } catch (e) {
            log(`HEARTBEAT_LOST: ${e.message}`, 'error');
        }
    }, 1500);
}

// ── Guerrilla P2P Sync Logic ──────────────────────────────
async function syncBlacklist() {
    if (!wasmReady) return;
    try {
        const blacklist = JSON.parse(get_global_blacklist_wasm());
        if (blacklist.length > 0) {
            log(`📡 Guerrilla Mesh: ${blacklist.length} nodes synchronized.`, 'info');
            document.getElementById('nodes-sync').textContent = `${blacklist.length} NODES`;
        }
    } catch (e) {
        log('P2P_SYNC_ERROR: UNABLE TO CONTACT GUERRILLA_NODES', 'error');
    }
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

    line.className = `${classes[type] || 'status-ok'} font-bold`;
    line.innerHTML = `<span class="text-red-900">[${ts}]</span> [SACITY] ${escapeHTML(msg)}`;
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

// ── Visual Effects ──────────────────────────────────────────
function applyGlitchEffect() {
    const body = document.body;
    body.classList.add('glitch');
    setTimeout(() => body.classList.remove('glitch'), 400);
}

function triggerPhaseBlack(score) {
    document.getElementById('black-overlay').style.display = 'block';
    document.getElementById('anomaly-status').textContent = 'PHASE_BLACK_V3.1';
    document.getElementById('anomaly-status').className = 'text-2xl font-black status-error glitch';
    log(`💀 AGGRESSION V3.1 DETECTED: Reconstruction Error ${score.toFixed(6)}`, 'error');
    log('💀 SACITY_RETALIATION: Delivering v4 Chaotic Poisoning & Entropy Trap...', 'error');
    applyGlitchEffect();

    // Trigger WASM retaliation hook if available
    try {
        if (wasmReady) {
            analyze_and_retaliate(JSON.stringify({
                source: "DASHBOARD_INJECTION",
                raw: "T1485_RANSOMWARE_V3.1",
                timestamp_ms: Date.now()
            }));
        }
    } catch(e) {}
}

// ── Metrics & Anomaly Logic ─────────────────────────────────
async function refreshMetrics() {
    const data = await apiFetch('/api/v1/metrics');
    if (!data) return;

    const score = data.detection.reconstruction_errors[0];
    const threshold = parseFloat(document.getElementById('threshold-val').textContent) || 0.7;

    updateScoreUI(score, threshold);

    if (score > threshold) {
        triggerPhaseBlack(score);
    } else {
        document.getElementById('black-overlay').style.display = 'none';
        document.getElementById('anomaly-status').textContent = 'CLEAN';
        document.getElementById('anomaly-status').className = 'text-2xl font-black status-ok';
    }

    if (data.features) {
        const entropy = 7.5 + (data.features[0] % 0.5);
        document.getElementById('entropy-val').textContent = entropy.toFixed(2);
    }
}

function updateScoreUI(score, threshold) {
    const scorePct = Math.min(100, (score / (threshold * 1.5)) * 100);
    document.getElementById('score-progress').style.width = `${scorePct}%`;
    document.getElementById('score-text').textContent = score.toFixed(6);

    if (score > threshold) {
        document.getElementById('score-text').className = 'status-error font-mono text-sm font-black glitch';
    } else {
        document.getElementById('score-text').className = 'status-info font-mono text-sm font-bold';
    }
}

// ── UI Actions ──────────────────────────────────────────────
window.triggerScan = async () => {
    log('> Neural Aggression Scan Initiated...', 'info');
    await refreshMetrics();
};

window.triggerRetaliationDemo = () => {
    log('> SIMULATING AGGRESSION VECTOR: Ransomware_T1485_V3', 'warn');
    triggerPhaseBlack(0.999999);
};

window.updateThreshold = (val) => {
    document.getElementById('threshold-val').textContent = val;
    log(`Aggression threshold recalibrated to: ${val}`, 'info');
};

// ── System Boot ─────────────────────────────────────────────
function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString('es-MX', { hour12: false });
}

async function init() {
    updateClock();
    setInterval(updateClock, 1000);

    log('SACITY // THE RED TERMINAL // ATLATL-ORDNANCE v3.0', 'info');
    await initWasm();

    await refreshMetrics();
    setInterval(refreshMetrics, 3000);
    setInterval(syncBlacklist, 8000);
}

init();
