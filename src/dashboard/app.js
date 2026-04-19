// ATLATL-ORDNANCE: SACITY Dashboard Logic v4.0
// Implementation of SACITY v4.0, Node-7 Integrity, and Phase Black Evolution

import initWasmModule, {
    health_check,
    get_security_telemetry,
    get_global_blacklist_wasm,
    analyze_and_retaliate,
    trigger_v5_retaliation,
    version
} from './pkg/kalpixk_core.js';

const API = window.location.origin;
let wasmReady = false;
let heartbeatInterval = null;
let lastHeartbeat = 0;

async function initWasm() {
    try {
        await initWasmModule();
        wasmReady = true;
        const v = version();
        const health = JSON.parse(health_check());
        log(`SACITY GuerrillaMesh v4.0 Armoured: ${v} [Node-7 Integrity: ${health.node_7_integrity}]`, 'info');
        document.getElementById('wasm-status').textContent = '● MESH_V4_SECURE';
        document.getElementById('wasm-status').className = 'text-[10px] status-ok font-bold';

        startHeartbeat();
        syncBlacklist();
    } catch (e) {
        log(`CRITICAL_WASM_FAILURE: ${e.message}`, 'error');
        document.getElementById('wasm-status').textContent = '● MESH_TAMPERED';
        document.getElementById('wasm-status').className = 'text-[10px] status-error font-bold glitch';
    }
}

function startHeartbeat() {
    heartbeatInterval = setInterval(() => {
        if (!wasmReady) return;
        try {
            const telemetry = JSON.parse(get_security_telemetry());
            const hb = telemetry.heartbeat;
            document.getElementById('hb-val').textContent = hb;

            if (hb === lastHeartbeat && hb > 0) {
                log('🚨 CRITICAL: WASM Runtime Stall! V5 Stealth Poisoning Triggered.', 'error');
                applyGlitchEffect(true);
            }
            lastHeartbeat = hb;
        } catch (e) {
            log(`HEARTBEAT_LOST: ${e.message}`, 'error');
        }
    }, 1500);
}

async function syncBlacklist() {
    if (!wasmReady) return;
    try {
        const blacklist = JSON.parse(get_global_blacklist_wasm());
        document.getElementById('nodes-sync').textContent = `${blacklist.length} NODES`;
    } catch (e) {}
}

function log(msg, type = 'ok') {
    const el = document.getElementById('log-terminal');
    const line = document.createElement('div');
    const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });
    const classes = { ok: 'status-ok', error: 'status-error', warn: 'status-warn', info: 'status-info' };
    line.className = `${classes[type] || 'status-ok'} font-bold`;
    line.innerHTML = `<span class="text-red-900">[${ts}]</span> [SACITY] ${msg}`;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
    if (el.children.length > 100) el.removeChild(el.firstChild);
}

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

function applyGlitchEffect(permanent = false) {
    const body = document.body;
    body.classList.add('glitch');
    if (!permanent) setTimeout(() => body.classList.remove('glitch'), 400);
}

function triggerPhaseBlack(score) {
    document.getElementById('black-overlay').style.display = 'block';
    document.getElementById('anomaly-status').textContent = 'PHASE_BLACK_V4.0';
    document.getElementById('anomaly-status').className = 'text-2xl font-black status-error glitch';
    log(`💀 AGGRESSION V4.0 DETECTED: Score ${score.toFixed(6)}`, 'error');
    log('💀 SACITY_RETALIATION: V5 Metal Strike & Memory Sink Trap...', 'error');
    applyGlitchEffect();

    try {
        if (wasmReady) {
            trigger_v5_retaliation("C2_VECTOR_DETECTION");
            analyze_and_retaliate(JSON.stringify({
                source: "MESH_ATTACK",
                raw: "T1485_V4_EVOLUTION",
                timestamp_ms: Date.now()
            }));
        }
    } catch(e) {}
}

async function refreshMetrics() {
    const data = await apiFetch('/api/v1/metrics');
    if (!data) return;
    const score = data.detection.reconstruction_errors[0];
    const threshold = parseFloat(document.getElementById('threshold-val').textContent) || 0.7;
    updateScoreUI(score, threshold);
    if (score > threshold) triggerPhaseBlack(score);
    else {
        document.getElementById('black-overlay').style.display = 'none';
        document.getElementById('anomaly-status').textContent = 'CLEAN';
    }
}

function updateScoreUI(score, threshold) {
    const scorePct = Math.min(100, (score / (threshold * 1.5)) * 100);
    document.getElementById('score-progress').style.width = `${scorePct}%`;
    document.getElementById('score-text').textContent = score.toFixed(6);
    document.getElementById('score-text').className = score > threshold ? 'status-error font-mono text-sm font-black glitch' : 'status-info font-mono text-sm font-bold';
}

export const triggerScan = async () => { log('> Neural Aggression Scan v4.0...', 'info'); await refreshMetrics(); };
export const triggerRetaliationDemo = () => { log('> SIMULATING V4 VECTOR: Ransomware_T1485_v4', 'warn'); triggerPhaseBlack(0.999); };
export const updateThreshold = (val) => { document.getElementById('threshold-val').textContent = val; log(`Aggression threshold recalibrated: ${val}`, 'info'); };

window.triggerScan = triggerScan;
window.triggerRetaliationDemo = triggerRetaliationDemo;
window.updateThreshold = updateThreshold;

function updateClock() {
    document.getElementById('clock').textContent = new Date().toLocaleTimeString('es-MX', { hour12: false });
}

async function init() {
    updateClock();
    setInterval(updateClock, 1000);
    log('SACITY // RED TERMINAL // ATLATL-ORDNANCE v4.0', 'info');
    await initWasm();
    await refreshMetrics();
    setInterval(refreshMetrics, 3000);
    setInterval(syncBlacklist, 8000);
}
init();
