// [ATLATL-ORDNANCE] motor.rs — Metal Layer Implementation in Rust
// Pure math, zero dependencies, high performance.
// Structural Alpha Stack Hardening

pub struct Pcg32 {
    state: u64,
    inc: u64,
}

impl Pcg32 {
    pub fn new(seed: u64) -> Self {
        let mut pcg = Pcg32 {
            state: 0,
            inc: (seed << 1) | 1,
        };
        pcg.next();
        pcg.state = pcg.state.wrapping_add(seed);
        pcg.next();
        pcg
    }

    pub fn next(&mut self) -> u32 {
        let old_state = self.state;
        self.state = old_state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(self.inc);
        let xorshifted = (((old_state >> 18) ^ old_state) >> 27) as u32;
        let rot = (old_state >> 59) as u32;
        (xorshifted >> rot) | (xorshifted << (rot.wrapping_neg() & 31))
    }

    pub fn next_bool(&mut self) -> bool {
        (self.next() & 1) == 1
    }
}

pub fn v5_active_memory_scrambling(slice: &mut [u8], entropy_seed: u64) {
    let mut prng = Pcg32::new(entropy_seed);

    for (i, byte) in slice.iter_mut().enumerate() {
        let shift = prng.next() % 8;
        if shift > 0 {
            *byte = byte.rotate_left(shift);
        }
        *byte ^= (prng.next() as u8) ^ (i as u8);
        if i % 2 == 0 {
            *byte = byte.wrapping_add(prng.next() as u8);
        } else {
            *byte ^= prng.next() as u8;
        }
        if prng.next_bool() {
            *byte = !*byte;
        }
    }
}

pub fn v5_chaotic_interleaving(slice: &mut [u8], stride: usize) {
    if stride == 0 || slice.len() < stride * 2 {
        return;
    }
    let mut i = 0;
    while i + stride * 2 <= slice.len() {
        for j in 0..stride {
            slice.swap(i + j, i + stride + j);
        }
        i += stride * 2;
    }
}

pub fn v7_guerrilla_memory_rotation(slice: &mut [u8], seed: u64) {
    if slice.len() < 16 {
        return;
    }
    let mut prng = Pcg32::new(seed);
    let stride = (prng.next() as usize % (slice.len() / 4)) + 1;
    let mut i = 0;
    while i + stride < slice.len() {
        let j = (i + stride) % slice.len();
        slice.swap(i, j);
        i += stride;
    }
}

pub fn v8_guerrilla_jit_shield(slice: &mut [u8], seed: u64) {
    let mut prng = Pcg32::new(seed);
    let mut i = 0;
    while i < slice.len() {
        let op = prng.next() % 100;
        if op < 15 {
            if i + 3 <= slice.len() {
                slice[i] = 0x0F;
                slice[i + 1] = 0x1F;
                slice[i + 2] = 0x00;
                i += 3;
            } else {
                i += 1;
            }
        } else if op < 30 {
            slice[i] = 0xCC;
            i += 1;
        } else if op < 40 {
            slice[i] = 0xF4;
            i += 1;
        } else {
            if prng.next_bool() {
                slice[i] = 0x90;
            }
            i += 1;
        }
    }
}

pub fn v8_quantum_entropy_shredder(slice: &mut [u8], seed: f64) {
    let mut x = seed;
    let r = 3.99;
    for byte in slice.iter_mut() {
        x = r * x * (1.0 - x);
        *byte = (x * 255.0).floor() as u8;
    }
}

pub fn v8_pointer_poisoning(slice: &mut [u8], seed: u64) {
    if slice.len() < 8 {
        return;
    }
    let mut prng = Pcg32::new(seed);
    let mut i = 0;
    while i + 8 <= slice.len() {
        let choice = prng.next() % 4;
        match choice {
            0 => {
                // NULL
                for b in &mut slice[i..i + 8] {
                    *b = 0;
                }
            }
            1 => {
                // Circular
                for j in (0..8).step_by(2) {
                    slice[i + j] = 0xEB;
                    slice[i + j + 1] = 0xFE;
                }
            }
            2 => {
                // CPU Exhaustion
                slice[i] = 0xEB;
                slice[i + 1] = 0xFE;
                for b in &mut slice[i + 2..i + 8] {
                    *b = 0x90;
                }
            }
            3 => {
                // Trap
                for b in &mut slice[i..i + 8] {
                    *b = 0xCC;
                }
            }
            _ => unreachable!(),
        }
        i += 8;
    }
}

pub fn v7_audit_tensor(slice: &[f32]) -> bool {
    if slice.is_empty() {
        return true;
    }
    let mut prev = slice[0];
    for &val in slice {
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

pub fn v7_stealth_poisoning(slice: &mut [u8], seed: u64) {
    let mut prng = Pcg32::new(seed);

    for byte in slice.iter_mut() {
        let op = prng.next() % 10;
        match op {
            0 => *byte = 0xEB,
            1 => *byte = 0xFE,
            2 => *byte = 0xF4,
            3 => *byte = 0xCC,
            4 => *byte = 0x0F,
            5 => *byte = 0x0B,
            6 => *byte = 0x90,
            7 => *byte = 0xE9,
            _ => *byte = (prng.next() & 0xFF) as u8,
        }
    }
}

pub fn mesh_entropy_shredder(slice: &mut [u8], key: u64) {
    let mut prng = Pcg32::new(key);
    for byte in slice.iter_mut() {
        *byte = (prng.next() & 0xFF) as u8;
    }
}

pub fn shannon_entropy(slice: &[u8]) -> f64 {
    if slice.is_empty() {
        return 0.0;
    }
    let mut freq = [0u64; 256];
    for &byte in slice {
        freq[byte as usize] += 1;
    }
    let mut entropy = 0.0;
    let n = slice.len() as f64;
    for &count in &freq {
        if count == 0 {
            continue;
        }
        let p = count as f64 / n;
        entropy -= p * p.log2();
    }
    entropy
}

pub fn classify_entropy(slice: &[u8]) -> u8 {
    let h = shannon_entropy(slice);
    if h >= 7.8 {
        2
    } else if h >= 7.2 {
        1
    } else {
        0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shannon_entropy() {
        let data = [0u8; 100];
        assert_eq!(shannon_entropy(&data), 0.0);

        let mut data2 = [0u8; 256];
        for i in 0..256 {
            data2[i] = i as u8;
        }
        assert!(shannon_entropy(&data2) > 7.9);
    }
}
