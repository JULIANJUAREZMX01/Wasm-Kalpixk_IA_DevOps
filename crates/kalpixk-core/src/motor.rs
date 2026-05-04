//! [ATLATL-ORDNANCE] motor.rs — Port of Zig Metal Core to Rust
//! Implements active memory scrambling and stealth poisoning without external linkage.

pub fn v5_active_memory_scrambling(data: &mut [u8], seed: u64) {
    let mut state = seed;
    for byte in data.iter_mut() {
        // LCG-based pseudo-random rotation and XOR
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        let shift = (state >> 60) as u32 & 0x07;
        *byte = byte.rotate_left(shift) ^ (state as u8);
    }
}

pub fn v5_stealth_poisoning(data: &mut [u8], seed: u64) {
    let mut state = seed;
    for byte in data.iter_mut() {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        let op = (state >> 56) as u8 % 10;
        match op {
            0 => *byte = 0xEB, // JMP short
            1 => *byte = 0xFE, // loop
            2 => *byte = 0xF4, // HLT
            3 => *byte = 0xCC, // INT 3
            4 => *byte = 0x0F, // Multi-byte
            5 => *byte = 0x0B, // UD2
            6 => *byte = 0x90, // NOP
            7 => *byte = 0xE9, // JMP near
            _ => *byte = state as u8,
        }
    }
}
