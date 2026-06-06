// motor.rs — Rust port of Zig Metal logic for v8.0.0-GUERRILLA
// Ensures build compatibility in environments without a Zig compiler.

use std::sync::atomic::{AtomicU8, Ordering};

pub fn shannon_entropy_rust(data: &[u8]) -> f64 {
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

#[no_mangle]
pub extern "C" fn shannon_entropy(data_ptr: *const u8, data_len: usize) -> f64 {
    let data = unsafe { std::slice::from_raw_parts(data_ptr, data_len) };
    shannon_entropy_rust(data)
}

#[no_mangle]
pub extern "C" fn v5_active_memory_scrambling(target_ptr: *mut u8, target_len: usize, seed: u64) {
    let target = unsafe { std::slice::from_raw_parts_mut(target_ptr, target_len) };
    let mut state = seed;
    for byte in target.iter_mut() {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        *byte ^= (state >> 32) as u8;
    }
}

#[no_mangle]
pub extern "C" fn v5_chaotic_interleaving(target_ptr: *mut u8, target_len: usize, stride: usize) {
    let target = unsafe { std::slice::from_raw_parts_mut(target_ptr, target_len) };
    if stride == 0 || target.len() < 2 {
        return;
    }
    for i in (0..target.len() - 1).step_by(stride) {
        target.swap(i, (i + 1) % target.len());
    }
}

#[no_mangle]
pub extern "C" fn v7_guerrilla_memory_rotation(target_ptr: *mut u8, target_len: usize, seed: u64) {
    let target = unsafe { std::slice::from_raw_parts_mut(target_ptr, target_len) };
    if target.len() < 2 {
        return;
    }
    let mut state = seed;
    let stride = (seed as usize % (target.len() / 2)) + 1;
    for i in (0..target.len()).step_by(stride) {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        let j = (state as usize) % target.len();
        target.swap(i, j);
    }
}

#[no_mangle]
pub extern "C" fn v7_audit_tensor(data_ptr: *const f32, data_len: usize) -> bool {
    let data = unsafe { std::slice::from_raw_parts(data_ptr, data_len) };
    for &val in data {
        if !val.is_finite() {
            return false;
        }
    }
    true
}

#[no_mangle]
pub extern "C" fn v8_guerrilla_jit_shield(target_ptr: *mut u8, target_len: usize, seed: u64) {
    let target = unsafe { std::slice::from_raw_parts_mut(target_ptr, target_len) };
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

#[no_mangle]
pub extern "C" fn v8_quantum_entropy_shredder(
    target_ptr: *mut u8,
    target_len: usize,
    initial_x: f64,
) {
    let target = unsafe { std::slice::from_raw_parts_mut(target_ptr, target_len) };
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

#[no_mangle]
pub extern "C" fn v8_pointer_poisoning(target_ptr: *mut u8, target_len: usize, seed: u64) {
    let target = unsafe { std::slice::from_raw_parts_mut(target_ptr, target_len) };
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
                // NULL Pointer Trap
                for j in 0..8 {
                    target[i + j] = 0;
                }
            }
            1 => {
                // Circular Jump Trap (0xEB 0xFE)
                target[i] = 0xEB;
                target[i + 1] = 0xFE;
                for j in 2..8 {
                    target[i + j] = 0x90;
                }
            }
            2 => {
                // CPU Exhaustion / HLT Loop
                target[i] = 0xF4;
                target[i + 1] = 0xEB;
                target[i + 2] = 0xFD; // JMP -3
                for j in 3..8 {
                    target[i + j] = 0xCC;
                }
            }
            _ => {
                // Random Poison
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

/// [ATLATL-ORDNANCE] v9_polymorphic_challenge_gen
/// Deterministic LCG + XOCHIMIL XOR for mesh authentication.
pub fn v9_polymorphic_challenge_gen(seed: u64) -> u64 {
    let multiplier: u64 = 6364136223846793005;
    let increment: u64 = 1;
    let xochimil: u64 = 0x584F4348494D494C; // 'XOCHIMIL'
    seed.wrapping_mul(multiplier).wrapping_add(increment) ^ xochimil
}

/// [ATLATL-ORDNANCE] v9_binary_integrity_hash
/// Rolling FNV-1a variant for runtime WASM integrity.
pub fn v9_binary_integrity_hash(data: &[u8]) -> u64 {
    let mut hash: u64 = 14695981039346656037; // Offset basis
    let prime: u64 = 1099511628211;

    for &byte in data {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(prime);
    }
    hash
}
