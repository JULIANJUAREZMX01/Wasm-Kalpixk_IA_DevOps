// motor.rs — Rust port of Zig Metal logic for v9.0.0-XOCHIMILCO
// Ensures build compatibility in environments without a Zig compiler.

use std::sync::atomic::{AtomicU8, Ordering};

pub fn shannon_entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }

    let mut freq = [0u64; 256];
    for &byte in data {
        freq[byte as usize] += 1;
    }

    let mut entropy = 0.0;
    let n = data.len() as f64;
    for &count in &freq {
        if count == 0 {
            continue;
        }
        let p = count as f64 / n;
        entropy -= p * p.log2();
    }
    entropy
}

pub fn v9_xochimilco_jit_shield(target: &mut [u8], seed: u64) {
    let r1 = 3.9999f64;
    let r2 = 3.8888f64;
    let mut x1 = 0.5f64;
    let mut x2 = 0.7f64;

    let mut i = 0;
    while i < target.len() {
        x1 = r1 * x1 * (1.0 - x1);
        x2 = r2 * x2 * (1.0 - x2);

        let noise_type = ((x1 * 1000.0) as u64 + seed) % 5;
        let noise_len = (((x2 * 1000.0) as u64) % 4) + 1;

        if i + (noise_len as usize) > target.len() {
            break;
        }

        for j in 0..(noise_len as usize) {
            match noise_type {
                0 => target[i + j] = 0x90, // NOP
                1 => target[i + j] = 0xF4, // HLT
                2 => target[i + j] = 0xCC, // INT 3
                3 => target[i + j] = 0x0F, // UD2 byte 1
                _ => target[i + j] = ((x1 * 255.0) as u8) ^ ((x2 * 255.0) as u8),
            }
        }
        i += noise_len as usize;
    }
}

pub fn v9_xochimilco_active_memory_scrambling(target: &mut [u8], seed: u64) {
    if target.is_empty() {
        return;
    }
    let r = 3.9999f64;
    let mut x = if seed == 0 {
        0.4123
    } else {
        (seed % 1000) as f64 / 1000.0
    };
    if x <= 0.0 || x >= 1.0 {
        x = 0.5;
    }

    for idx in 0..target.len() {
        x = r * x * (1.0 - x);
        let mask = (x * 255.0) as u8;
        target[idx] ^= mask;
    }
}

pub fn v9_xochimilco_ghost_mesh(node_id: &str, payload: &str) -> String {
    let mut state = 0xDEADC0DEu64;
    for b in node_id.bytes().chain(payload.bytes()) {
        state = state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(b as u64);
    }
    format!("v9-xochimilco-mesh-{:x}", state)
}

pub fn v8_guerrilla_jit_shield(target: &mut [u8], seed: u64) {
    let mut state = seed;
    let mut i = 0;
    while i < target.len() {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        let noise_type = (state % 4) as u8;
        let noise_len = ((state >> 8) % 4) as usize + 1;

        if i + noise_len > target.len() {
            break;
        }

        for j in 0..noise_len {
            match noise_type {
                0 => target[i + j] = 0x90, // NOP
                1 => target[i + j] = 0xF4, // HLT
                2 => target[i + j] = 0xCC, // INT 3
                _ => {
                    state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
                    target[i + j] = (state >> 16) as u8;
                }
            }
        }
        i += noise_len;
    }
}

pub fn v8_quantum_entropy_shredder(target: &mut [u8], initial_x: f64) {
    let r = 3.99;
    let mut x = if initial_x <= 0.0 || initial_x >= 1.0 {
        0.5
    } else {
        initial_x
    };

    for byte in target.iter_mut() {
        x = r * x * (1.0 - x);
        *byte = (x * 255.0) as u8;
    }
}

pub fn v8_pointer_poisoning(target: &mut [u8], seed: u64) {
    if target.len() < 8 {
        return;
    }
    let mut state = seed;
    let mut i = 0;
    while i + 8 <= target.len() {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        let trap_type = (state % 4) as u8;

        match trap_type {
            0 => {
                for j in 0..8 {
                    target[i + j] = 0;
                }
            }
            1 => {
                target[i] = 0xEB;
                target[i + 1] = 0xFE;
                for j in 2..8 {
                    target[i + j] = 0x90;
                }
            }
            2 => {
                target[i] = 0xF4;
                target[i + 1] = 0xEB;
                target[i + 2] = 0xFD;
                for j in 3..8 {
                    target[i + j] = 0xCC;
                }
            }
            _ => {
                for j in 0..8 {
                    state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
                    target[i + j] = (state >> 24) as u8;
                }
            }
        }
        i += 8;
    }
}

pub fn v5_active_memory_scrambling(target: &mut [u8], seed: u64) {
    v9_xochimilco_active_memory_scrambling(target, seed);
}

pub fn v5_chaotic_interleaving(target: &mut [u8], stride: usize) {
    if stride == 0 || target.len() < stride {
        return;
    }
    for i in (0..target.len() - stride).step_by(stride) {
        target.swap(i, i + stride);
    }
}

pub fn v7_guerrilla_memory_rotation(target: &mut [u8], seed: u64) {
    if target.len() < 2 {
        return;
    }
    let mut state = seed;
    for i in 0..target.len() - 1 {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        let swap_idx = (state as usize) % target.len();
        target.swap(i, swap_idx);
    }
}

pub fn v7_audit_tensor(data: &[f32]) -> bool {
    if data.is_empty() {
        return true;
    }
    let mut prev = data[0];
    for &val in data {
        if !val.is_finite() {
            return false;
        }
        if (val - prev).abs() > 10.0 {
            return false;
        }
        prev = val;
    }
    true
}

pub fn validate_atomic_access(ptr: &AtomicU8, expected: u8) -> bool {
    ptr.load(Ordering::Relaxed) == expected
}
