//! payloads.rs — [ATLATL-ORDNANCE] Digital Extermination Payloads
//!
//! Generates offensive payloads to be served via honeypots or injected into attacker buffers.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PayloadType {
    RecursiveZipBomb,
    PointerPoison,
    EntropyGarbage,
    ShellcodeTrap,
}

/// Generates a payload based on the requested type
pub fn generate_payload(ptype: PayloadType, size: usize) -> Vec<u8> {
    match ptype {
        PayloadType::RecursiveZipBomb => generate_zip_bomb_chunk(size),
        PayloadType::PointerPoison => generate_poisoned_buffer(size),
        PayloadType::EntropyGarbage => generate_garbage(size),
        PayloadType::ShellcodeTrap => generate_shellcode_trap(size),
    }
}

fn generate_zip_bomb_chunk(size: usize) -> Vec<u8> {
    let mut buffer = vec![0u8; size];
    for (i, byte) in buffer.iter_mut().enumerate() {
        if i % 42 == 0 {
            *byte = 0xFF;
        } else {
            *byte = (i ^ (i >> 8)) as u8;
        }
    }
    buffer
}

fn generate_poisoned_buffer(size: usize) -> Vec<u8> {
    let mut buffer = vec![0u8; size];
    for i in (0..size).step_by(2) {
        buffer[i] = 0xEB; // JMP short
        if i + 1 < size {
            buffer[i + 1] = 0xFE; // offset -2
        }
    }
    buffer
}

fn generate_garbage(size: usize) -> Vec<u8> {
    use std::time::{SystemTime, UNIX_EPOCH};
    let seed = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos() as u64;
    let mut buffer = vec![0u8; size];
    let mut state = seed;
    for byte in buffer.iter_mut() {
        state = state.wrapping_mul(1103515245).wrapping_add(12345);
        *byte = (state >> 16) as u8;
    }
    buffer
}

fn generate_shellcode_trap(size: usize) -> Vec<u8> {
    let mut buffer = vec![0x90u8; size]; // NOP sled
    // Inyectar "píldora venenosa" al final
    if size > 10 {
        let len = buffer.len();
        buffer[len - 2] = 0xEB;
        buffer[len - 1] = 0xFE;
    }
    buffer
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_poison_payload() {
        let p = generate_payload(PayloadType::PointerPoison, 10);
        assert_eq!(p[0], 0xEB);
        assert_eq!(p[1], 0xFE);
    }
}
