// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 7.0-ALPHA (Guerrilla Algorítmica)

const std = @import("std");
const atomic = std.atomic;

/// [ATLATL-ORDNANCE] ESTRUCTURA DE CONTROL DE MEMORIA
pub const MemoryContract = struct {
    pub const MAX_BUFFER_SIZE: usize = 1024 * 1024; // 1MB
    pub const CANARY_VALUE: u8 = 0xDE;
    pub const POISON_VALUE: u8 = 0xAD;
};

/// Entropia de Shannon en bits por simbolo
pub export fn shannon_entropy(data_ptr: [*]const u8, data_len: usize) f64 {
    if (data_len == 0) return 0.0;

    var freq = [_]u64{0} ** 256;
    const slice = data_ptr[0..data_len];
    for (slice) |byte| freq[byte] += 1;

    var entropy: f64 = 0.0;
    const n: f64 = @floatFromInt(data_len);
    for (freq) |count| {
        if (count == 0) continue;
        const p: f64 = @as(f64, @floatFromInt(count)) / n;
        entropy -= p * @log(p) / @log(2.0);
    }
    return entropy;
}

/// Clasificacion rapida basada en entropia
pub export fn classify_entropy(data_ptr: [*]const u8, data_len: usize) u8 {
    const h = shannon_entropy(data_ptr, data_len);
    if (h >= 7.8) return 2; // Ransomware/Encrypted
    if (h >= 7.2) return 1; // Suspicious
    return 0;
}

/// [ATLATL-ORDNANCE] DYNAMIC OBFUSCATION
pub export fn dynamic_obfuscation(target_ptr: [*]u8, target_len: usize, seed: u32) void {
    const slice = target_ptr[0..target_len];
    var state = seed;
    for (slice) |*byte| {
        state = state *% 1103515245 +% 12345;
        byte.* ^= @truncate(state >> 16);
    }
}

/// [ATLATL-ORDNANCE] ATOMIC ACCESS VALIDATION
pub export fn validate_atomic_access(ptr: *atomic.Atomic(u8), expected: u8) bool {
    return ptr.load(.Monotonic) == expected;
}

/// [ATLATL-ORDNANCE] v7_audit_tensor
/// Realiza una auditoría profunda de tensores para detectar ataques de "adversarial roughness".
/// Implementa bit-level NaN/Inf shielding.
pub export fn v7_audit_tensor(data_ptr: [*]const f32, data_len: usize) bool {
    const slice = data_ptr[0..data_len];
    var roughness: f32 = 0.0;
    var prev: f32 = 0.0;

    for (slice, 0..) |val, i| {
        // NaN/Inf Shielding
        const bits = @as(u32, @bitCast(val));
        const exponent = (bits >> 23) & 0xFF;
        if (exponent == 0xFF) return true; // NaN o Inf detectado

        if (i > 0) {
            const diff = @abs(val - prev);
            roughness += diff;
        }
        prev = val;
    }

    // Si la rugosidad es extrema para un vector normalizado (32 dims), marcar como sospechoso
    return roughness > 15.0;
}

/// [ATLATL-ORDNANCE] v7_guerrilla_memory_rotation
/// Implementa rotación de memoria no determinante basada en estados cuánticos simulados.
pub export fn v7_guerrilla_memory_rotation(target_ptr: [*]u8, target_len: usize, entropy: u64) void {
    var prng = std.rand.DefaultPrng.init(entropy);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    const rotation = rand.int(usize) % target_len;
    if (rotation == 0) return;

    // In-place rotation (manual reversal)
    std.mem.reverse(u8, slice[0..rotation]);
    std.mem.reverse(u8, slice[rotation..target_len]);
    std.mem.reverse(u8, slice);
}

/// [ATLATL-ORDNANCE] v5_stealth_poisoning
pub export fn v5_stealth_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice) |*byte| {
        const op = rand.int(u8) % 10;
        switch (op) {
            0 => byte.* = 0xEB, // JMP short
            1 => byte.* = 0xFE, // loop
            2 => byte.* = 0xF4, // HLT
            3 => byte.* = 0xCC, // INT 3
            4 => byte.* = 0x0F, // Multi-byte
            5 => byte.* = 0x0B, // UD2
            6 => byte.* = 0x90, // NOP
            7 => byte.* = 0xE9, // JMP near
            else => byte.* = rand.int(u8),
        }
    }
}

/// [ATLATL-ORDNANCE] mesh_entropy_shredder
pub export fn mesh_entropy_shredder(target_ptr: [*]u8, target_len: usize, key: u64) void {
    var prng = std.rand.DefaultPrng.init(key);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice) |*byte| {
        byte.* = rand.int(u8);
    }
}

/// [ATLATL-ORDNANCE] v5_active_memory_scrambling
pub export fn v5_active_memory_scrambling(target_ptr: [*]u8, target_len: usize, entropy_seed: u64) void {
    var prng = std.rand.DefaultPrng.init(entropy_seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
        const shift = rand.int(u3);
        if (shift > 0) {
            byte.* = (byte.* << @intCast(shift)) | (byte.* >> @intCast(8 - shift));
        }
        byte.* ^= rand.int(u8) ^ @as(u8, @truncate(i));
        if (i % 2 == 0) {
            byte.* = byte.* +% rand.int(u8);
        } else {
            byte.* = byte.* ^% rand.int(u8);
        }
        if (rand.boolean()) {
            byte.* = ~byte.*;
        }
    }
}

/// [ATLATL-ORDNANCE] v5_logic_bomb_detector
pub export fn v5_logic_bomb_detector(data_ptr: [*]const u8, data_len: usize) bool {
    if (data_len == 0) return false;
    const slice = data_ptr[0..data_len];
    var i: usize = 0;
    while (i < data_len) : (i += 1) {
        if (i < data_len - 1) {
            if (slice[i] == 0xEB and slice[i + 1] == 0xFE) return true;
        }
        if (slice[i] == 0xF4 or slice[i] == 0xCC) return true;
    }
    return false;
}

test "v7 audit tensor detects Inf" {
    var tensor = [_]f32{ 0.1, 0.2, std.math.inf(f32) };
    try std.testing.expect(v7_audit_tensor(&tensor, 3) == true);
}

test "v7 audit tensor detects roughness" {
    var tensor = [_]f32{0.0} ** 32;
    for (&tensor, 0..) |*v, i| {
        v.* = if (i % 2 == 0) 1.0 else -1.0;
    }
    // roughness = sum(abs(v_i - v_{i-1})) = 31 * 2.0 = 62.0
    try std.testing.expect(v7_audit_tensor(&tensor, 32) == true);
}
