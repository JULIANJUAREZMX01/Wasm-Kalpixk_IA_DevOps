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

pub fn v9_xochimilco_jit_shield(target: &mut [u8], seed: u64) {
    let _ = seed;
    let r1 = 3.9999;
    let r2 = 3.8888;
    let mut x = 0.5;
    let mut y = 0.51;

    let mut i = 0;
    while i < target.len() {
        x = r1 * x * (1.0 - x) + 0.01 * (y - x);
        y = r2 * y * (1.0 - y) + 0.01 * (x - y);

        let noise_type = (x * 4.0) as u8;
        let noise_len = ((y * 4.0) as usize % 4) + 1;

        if i + noise_len > target.len() {
            break;
        }

        for j in 0..noise_len {
            match noise_type {
                0 => target[i + j] = 0x90,
                1 => target[i + j] = 0xF4,
                2 => target[i + j] = 0xCC,
                3 => target[i + j] = 0x0F,
                _ => target[i + j] = (x * 255.0) as u8,
            }
            if noise_type == 3 && j == 1 {
                target[i + j] = 0x0B;
            }
        }
        i += noise_len;
    }
}

pub fn v9_xochimilco_active_memory_scrambling(target: &mut [u8], seed: u64) {
    if target.is_empty() {
        return;
    }
    let mut state = seed;
    let r = 3.999;
    let mut x = 0.7;

    for i in 0..target.len() {
        x = r * x * (1.0 - x);
        let rot = (x * 7.0) as u32;
        let chaotic_byte = (x * 255.0) as u8;
        target[i] = (target[i] ^ chaotic_byte).rotate_right(rot);

        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        if i > 0 && (state % 10 == 0) {
            target.swap(i, i - 1);
        }
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
                target[i + 2] = 0xFD; // JMP -3
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

pub fn validate_atomic_access(ptr: &AtomicU8, expected: u8) -> bool {
    ptr.load(Ordering::Relaxed) == expected
}
