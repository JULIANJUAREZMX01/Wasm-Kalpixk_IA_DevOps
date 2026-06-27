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

pub fn v9_recursive_zip_trap(target: &mut [u8]) {
    let mut i = 0;
    while i + 4 <= target.len() {
        target[i] = 0x50;
        target[i + 1] = 0x4B;
        target[i + 2] = 0x03;
        target[i + 3] = 0x04;
        i += 4;
    }
}

pub fn v9_hardware_panic_trigger(target: &mut [u8]) {
    let mut i = 0;
    while i + 2 <= target.len() {
        target[i] = 0x0F;
        target[i + 1] = 0x0B;
        i += 2;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_v9_recursive_zip_trap() {
        let mut buffer = [0u8; 16];
        v9_recursive_zip_trap(&mut buffer);
        for i in (0..16).step_by(4) {
            assert_eq!(buffer[i], 0x50);
            assert_eq!(buffer[i + 1], 0x4B);
            assert_eq!(buffer[i + 2], 0x03);
            assert_eq!(buffer[i + 3], 0x04);
        }
    }

    #[test]
    fn test_v9_hardware_panic_trigger() {
        let mut buffer = [0u8; 16];
        v9_hardware_panic_trigger(&mut buffer);
        for i in (0..16).step_by(2) {
            assert_eq!(buffer[i], 0x0F);
            assert_eq!(buffer[i + 1], 0x0B);
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
