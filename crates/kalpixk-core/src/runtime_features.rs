#![allow(dead_code)]
use crate::metrics::WasmEventMetrics;
use lazy_static::lazy_static;
use std::sync::Mutex;

pub const FEATURE_DIM: usize = 32;

lazy_static! {
    static ref WINDOW_HISTORY: Mutex<Vec<WasmEventMetrics>> = Mutex::new(Vec::new());
}

pub fn extract_32_features(event: &WasmEventMetrics) -> Vec<f32> {
    let mut f = vec![0.0f32; FEATURE_DIM];

    // f[0]-f[7]: Direct from wasmtime
    f[0] = (event.instruction_count as f32 / 1_000_000.0).min(1.0);
    f[1] = (event.memory_pages as f32 / 65536.0).min(1.0);
    f[2] = (event.fuel_consumed as f32 / 1_000_000.0).min(1.0);
    f[3] = (event.wall_time_ns as f32 / 1_000_000_000.0).min(1.0);
    f[4] = (event.call_depth as f32 / 100.0).min(1.0);
    f[5] = if event.instruction_count > 0 {
        (event.import_calls as f32 / event.instruction_count as f32).min(1.0)
    } else {
        0.0
    };
    f[6] = (event.export_calls as f32 / 100.0).min(1.0);

    // Calculate memory growth delta if possible (requires history)
    let mut history = WINDOW_HISTORY.lock().unwrap();
    if let Some(last) = history.last() {
        f[7] = (event.memory_pages as f32 - last.memory_pages as f32).max(0.0) / 100.0;
    } else {
        f[7] = 0.0;
    }

    // f[8]: shannon_entropy
    f[8] = event.entropy;

    // f[9]: instruction_variance
    if history.len() >= 2 {
        let n = history.len() as f32;
        let mean = (history.iter().map(|e| e.instruction_count).sum::<u64>() as f32
            + event.instruction_count as f32)
            / (n + 1.0);
        let variance = (history
            .iter()
            .map(|e| (e.instruction_count as f32 - mean).powi(2))
            .sum::<f32>()
            + (event.instruction_count as f32 - mean).powi(2))
            / (n + 1.0);
        f[9] = (variance.sqrt() / 100_000.0).min(1.0);
    } else {
        f[9] = 0.0;
    }

    // f[10]-f[15]: Instruction ratios (Derived/Placeholder)
    // In a real scenario, these would come from the profiler
    f[10] = 0.2; // arith ratio baseline
    f[11] = 0.3; // mem ratio baseline
    f[12] = 0.1; // ctrl ratio baseline
    f[13] = 0.1; // call ratio baseline
    f[14] = 0.15; // load ratio baseline
    f[15] = 0.15; // store ratio baseline

    // Update history (window of 10)
    history.push(event.clone());
    if history.len() > 10 {
        history.remove(0);
    }

    // f[16]-f[31]: Sliding window statistics (mean, std, min, max x 4 metrics)
    // Metrics: [instruction_count, memory_pages, fuel, wall_time]
    if history.len() > 1 {
        let n = history.len() as f32;

        // Instr count stats
        let ic_vals: Vec<f32> = history.iter().map(|e| e.instruction_count as f32).collect();
        f[16] = ic_vals.iter().sum::<f32>() / (n * 1_000_000.0); // mean
        f[17] = (ic_vals
            .iter()
            .map(|&v| (v - f[16] * 1_000_000.0).powi(2))
            .sum::<f32>()
            / n)
            .sqrt()
            / 1_000_000.0; // std
        f[18] = ic_vals.iter().cloned().fold(f32::INFINITY, f32::min) / 1_000_000.0; // min
        f[19] = ic_vals.iter().cloned().fold(f32::NEG_INFINITY, f32::max) / 1_000_000.0; // max

        // Memory pages stats
        let mp_vals: Vec<f32> = history.iter().map(|e| e.memory_pages as f32).collect();
        f[20] = mp_vals.iter().sum::<f32>() / (n * 65536.0);
        f[21] = 0.01; // placeholder std
        f[22] = mp_vals.iter().cloned().fold(f32::INFINITY, f32::min) / 65536.0;
        f[23] = mp_vals.iter().cloned().fold(f32::NEG_INFINITY, f32::max) / 65536.0;

        // Fuel stats
        let fl_vals: Vec<f32> = history.iter().map(|e| e.fuel_consumed as f32).collect();
        f[24] = fl_vals.iter().sum::<f32>() / (n * 1_000_000.0);
        f[25] = 0.01;
        f[26] = fl_vals.iter().cloned().fold(f32::INFINITY, f32::min) / 1_000_000.0;
        f[27] = fl_vals.iter().cloned().fold(f32::NEG_INFINITY, f32::max) / 1_000_000.0;

        // Wall time stats
        let wt_vals: Vec<f32> = history.iter().map(|e| e.wall_time_ns as f32).collect();
        f[28] = wt_vals.iter().sum::<f32>() / (n * 1_000_000_000.0);
        f[29] = 0.01;
        f[30] = wt_vals.iter().cloned().fold(f32::INFINITY, f32::min) / 1_000_000_000.0;
        f[31] = wt_vals.iter().cloned().fold(f32::NEG_INFINITY, f32::max) / 1_000_000_000.0;
    }

    f
}
