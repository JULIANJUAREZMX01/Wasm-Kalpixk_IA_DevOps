// ATLATL-ORDNANCE: Dashboard Logic v3.0 (SAC_OS Hardened)
// Implementation of SACITY aesthetic and WASM Heartbeat

import initWasmModule, {
    health_check,
    get_security_telemetry,
    parse_log_line,
    analyze_and_retaliate,
    version
} from './pkg/kalpixk_core.js';

const API = window.location.origin;
let wasmReady = false;
let heartbeatInterval = null;
let lastHeartbeat = 0;
let phaseBlackActive = false;

// ── WASM Initialization ─────────────────────────────────────
async function initWasm() {
    try {
        await initWasmModule();
        wasmReady = true;
        const v = version();
        const health = JSON.parse(health_check());
        log(`ATLATL-ORDNANCE Core [${v}] Initialized.`, 'info');
        log(`WASM Status: ${health.status} // Feature Dim: ${health.feature_dim}`, 'info');

        document.getElementById('wasm-status').textContent = '● WASM_ACTIVE_MACUAHUITL';
        document.getElementById('wasm-status').className = 'text-[10px] status-ok';

        // Start Heartbeat
        startHeartbeat();
    } catch (e) {
        log(`CRITICAL_WASM_FAILURE: ${e.message}`, 'error');
        document.getElementById('wasm-status').textContent = '● WASM_TAMPERED_ALERT';
        document.getElementById('wasm-status').className = 'text-[10px] status-error blink';
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
                log('🚨 CRITICAL: WASM Runtime Stalled! Defensive Countermeasures Arming.', 'error');
                document.getElementById('wasm-integrity').textContent = 'TAMPERED';
                document.getElementById('wasm-integrity').className = 'text-2xl font-bold status-error blink';
                triggerPhaseBlack(1.0, "WASM_STALL_DETECTION");
            } else {
                document.getElementById('wasm-integrity').textContent = 'SYNCED';
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

    if (el.children.length > 200) el.removeChild(el.firstChild);
}

// ── Terminal Command Input ──────────────────────────────────
const terminalInput = document.getElementById('terminal-input');
terminalInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        const cmd = terminalInput.value.trim().toLowerCase();
        terminalInput.value = '';
        handleCommand(cmd);
    }
});

async function handleCommand(cmd) {
    log(`<span class="text-red-500">SAC_OS></span> ${cmd}`, 'ok');

    if (cmd === 'help') {
        log('AVAILABLE COMMANDS:', 'info');
        log('  status       - Get system state', 'info');
        log('  scan         - Manual thread scan', 'info');
        log('  phase black  - Trigger retaliation', 'info');
        log('  sync         - Sync P2P defense nodes', 'info');
        log('  clear        - Clear terminal', 'info');
        log('  reboot       - Restart SACITY subsystem', 'info');
    } else if (cmd === 'status') {
        const data = await apiFetch('/api/v1/status');
        if (data) log(`SYSTEM_STATUS: Trained=${data.is_trained} // Threshold=${data.threshold}`, 'info');
    } else if (cmd === 'scan') {
        triggerScan();
    } else if (cmd === 'phase black') {
        triggerRetaliationDemo();
    } else if (cmd === 'sync') {
        syncAllNodes();
    } else if (cmd === 'clear') {
        document.getElementById('log-terminal').innerHTML = '';
    } else if (cmd === 'reboot') {
        log('Rebooting SACITY components...', 'warn');
        location.reload();
    } else {
        log(`Unknown command: ${cmd}`, 'error');
    }
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
    } else if (!phaseBlackActive) {
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

function triggerPhaseBlack(score, type = "ANOMALY") {
    phaseBlackActive = true;
    document.getElementById('black-overlay').style.display = 'block';
    document.getElementById('anomaly-status').textContent = 'THREAT!';
    document.getElementById('anomaly-status').className = 'text-2xl font-bold status-error blink';
    log(`🚨 THREAT DETECTED [${type}]: Anomaly Score ${score.toFixed(6)}`, 'error');
    log('💀 PHASE BLACK: EXECUTING MACUAHUITL RETALIATION PROTOCOL', 'error');
    log('💉 Injecting Recursive Entropy Shredder to network buffers...', 'warn');

    setTimeout(() => {
        if (score < 0.7) {
            phaseBlackActive = false;
        }
    }, 10000);
}

// ── UI Actions ──────────────────────────────────────────────
window.triggerScan = async () => {
    log('> Manual Pulse Scan Sequence Initiated...', 'info');
    await refreshMetrics();
};

window.triggerRetaliationDemo = () => {
    log('> MANUAL OVERRIDE: SIMULATING MAXIMUM AGGRESSION', 'warn');
    triggerPhaseBlack(0.999999, "MANUAL_STRIKE");
};

window.updateThreshold = (val) => {
    document.getElementById('threshold-val').textContent = val;
    log(`Aggression threshold recalibrated to: ${val}`, 'info');
};

window.syncAllNodes = async () => {
    log('> Broadcasting threat signatures to P2P Defense Nodes...', 'info');
    // Simulated P2P Sync
    setTimeout(() => {
        log('● SYNC_COMPLETE: 12 Nodes Updated. Global Blacklist Synced.', 'status-ok');
        document.getElementById('reg-count').textContent = '12 THREATS';
    }, 800);
};

// ── System Boot ─────────────────────────────────────────────
function updateClock() {
    document.getElementById('clock').textContent = new Date().toLocaleTimeString('es-MX', { hour12: false });
}

async function init() {
    updateClock();
    setInterval(updateClock, 1000);

    log('ATLATL-ORDNANCE: SACITY_OS v3.0 // GUERRILLA_ALGORÍTMICA LOADED', 'info');
    await initWasm();

    // Initial data fetch
    await refreshMetrics();
    setInterval(refreshMetrics, 5000);
}

init();
