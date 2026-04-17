// ATLATL-ORDNANCE: SACITY Dashboard Logic v4.0 (Guerrilla Mesh)
// Implementation of SACITY aesthetic, CRT Effects, and WASM Heartbeat v4

import initWasmModule, {
    health_check,
    get_security_telemetry,
    get_global_blacklist_wasm,
    analyze_and_retaliate,
    version,
    trigger_v5_retaliation // Updated for v5 Zig core
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
        const v = version();
        const health = JSON.parse(health_check());
        log(`GuerrillaMesh v4.0 Operational: ${v} [Metal: v5.0-atlatl]`, 'info');
        document.getElementById('wasm-status').textContent = '● WASP_V4_SECURE';
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

// ── Heartbeat Mechanism (WASP v4) ──────────────────────────
function startHeartbeat() {
    heartbeatInterval = setInterval(() => {
        if (!wasmReady) return;
        try {
            const telemetry = JSON.parse(get_security_telemetry());
            const hb = telemetry.heartbeat;

            document.getElementById('hb-val').textContent = hb;

            if (hb === lastHeartbeat && hb > 0) {
                log('🚨 CRITICAL: WASM Runtime Stall v4 Detected! Activating Macuahuitl Metal v5.', 'error');
                document.getElementById('anomaly-status').textContent = 'STALLED_V4';
                document.getElementById('anomaly-status').className = 'text-2xl font-black status-error glitch';
                applyGlitchEffect(true);
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
            log(`📡 Guerrilla Mesh v4: ${blacklist.length} nodes verified via Node-7.`, 'info');
            document.getElementById('nodes-sync').textContent = `${blacklist.length} NODES`;
        }
    } catch (e) {
        log('P2P_SYNC_ERROR: UNABLE TO CONTACT GUERRILLAMESH CLUSTER', 'error');
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
    line.innerHTML = `<span class="text-red-900">[${ts}]</span> [SACITY] ${msg}`;
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
function applyGlitchEffect(isSevere = false) {
    const body = document.body;
    const duration = isSevere ? 1000 : 400;
    body.classList.add('glitch');
    if (isSevere) {
        body.style.filter = 'hue-rotate(90deg) contrast(200%)';
    }
    setTimeout(() => {
        body.classList.remove('glitch');
        body.style.filter = '';
    }, duration);
}

function triggerPhaseBlack(score) {
    document.getElementById('black-overlay').style.display = 'block';
    document.getElementById('anomaly-status').textContent = 'PHASE_BLACK_V4.0';
    document.getElementById('anomaly-status').className = 'text-2xl font-black status-error glitch';
    log(`💀 AGGRESSION V4.0 DETECTED: Reconstruction Error ${score.toFixed(6)}`, 'error');
    log('💀 SACITY_RETALIATION_V4: Arming Node-7 Mesh Integrity & Metal Sink Trap...', 'error');
    applyGlitchEffect(true);

    // Trigger WASM retaliation hook if available
    try {
        if (wasmReady) {
            trigger_v5_retaliation(JSON.stringify({
                source: "DASHBOARD_V4",
                vector: "PHASE_BLACK_TRIGGER",
                timestamp: Date.now()
            }));

            analyze_and_retaliate(JSON.stringify({
                source: "DASHBOARD_INJECTION_V4",
                raw: "T1485_RANSOMWARE_v4.0_GUERRILLAMESH",
                timestamp_ms: Date.now()
            }));
        }
    } catch(e) {
        console.error("WASM Retaliation Error:", e);
    }
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
        // Mock entropy display from v4 features
        const entropy = 7.7 + (data.features[0] % 0.3);
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
    log('> Guerrilla Aggression Scan Initiated (v4.0)...', 'info');
    await refreshMetrics();
};

window.triggerRetaliationDemo = () => {
    log('> SIMULATING v4.0 AGGRESSION VECTOR: Ransomware_T1485_Guerrilla', 'warn');
    triggerPhaseBlack(0.999999);
};

window.updateThreshold = (val) => {
    document.getElementById('threshold-val').textContent = val;
    log(`Aggression threshold recalibrated v4: ${val}`, 'info');
};

// ── System Boot ─────────────────────────────────────────────
function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString('es-MX', { hour12: false });
}

async function init() {
    updateClock();
    setInterval(updateClock, 1000);

    log('SACITY // THE RED TERMINAL // ATLATL-ORDNANCE v4.0 (GUERRILLAMESH)', 'info');
    await initWasm();

    await refreshMetrics();
    setInterval(refreshMetrics, 3000);
    setInterval(syncBlacklist, 8000);
}

init();
