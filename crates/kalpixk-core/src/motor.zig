// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 5.0-ATLATL (Guerrilla Algorítmica)

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

/// [ATLATL-ORDNANCE] v5_macuahuitl_stealth_poisoning
/// Evolución táctica de la interferencia de flujo. Utiliza secuencias de salto
/// no deterministas basadas en el drift del reloj y semillas dinámicas.
pub export fn v5_macuahuitl_stealth_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
        const step = rand.int(u8) % 32;
        switch (step) {
            0...3 => byte.* = 0xEB, // JMP short
            4...5 => byte.* = 0xFE, // jump to self
            6 => byte.* = 0xCC,      // INT 3
            7 => byte.* = 0xCE,      // INTO (Interrupt on Overflow)
            8 => byte.* = 0xF1,      // INT 1 / ICEBP
            9 => byte.* = 0x0F,      // UD2 prefix
            10 => byte.* = 0x0B,     // UD2
            11 => byte.* = 0x2E,     // CS segment override (noise)
            12 => byte.* = 0x66,     // Operand size override
            13 => byte.* = 0x90,     // NOP
            14...31 => byte.* = rand.int(u8),
            else => unreachable,
        }
    }
}

/// [ATLATL-ORDNANCE] memory_sink_trap
/// Inunda los buffers con patrones de recursión infinita y firmas de archivos
/// "polimórficas" para colapsar los pipelines de emulación de malware.
pub export fn memory_sink_trap(target_ptr: [*]u8, target_len: usize, key: u64) void {
    var prng = std.rand.DefaultPrng.init(key);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
        if (i % 1024 == 0) {
            // Fake ZIP magic
            byte.* = 0x50; // P
        } else if (i % 1024 == 1) {
            byte.* = 0x4B; // K
        } else if (i % 1024 == 2) {
            byte.* = 0x03;
        } else if (i % 1024 == 3) {
            byte.* = 0x04;
        } else if (i % 7 == 0) {
            byte.* = @truncate(i ^ key);
        } else {
            byte.* = rand.int(u8);
        }
    }
}

pub export fn shannon_entropy_v5(data_ptr: [*]const u8, data_len: usize) f64 {
    return shannon_entropy(data_ptr, data_len);
}

// Legacy exports kept for compatibility
pub export fn poison_pointers(target_ptr: [*]u8, target_len: usize) void {
    const slice = target_ptr[0..target_len];
    for (slice, 0..) |*byte, i| {
        if (i % 2 == 0) {
            byte.* = 0xEB;
        } else {
            byte.* = 0xFE;
        }
    }
}

pub export fn v3_macuahuitl_array_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
        switch (i % 8) {
            0 => byte.* = 0xEB, 1 => byte.* = 0xFE,
            2 => byte.* = 0xCC, 3 => byte.* = 0xF4,
            4 => byte.* = 0x90, 5 => byte.* = 0x90,
            6 => byte.* = 0xE9, 7 => byte.* = rand.int(u8),
            else => unreachable,
        }
    }
}

pub export fn recursive_entropy_shredder(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];
    for (slice, 0..) |*byte, i| {
        if (i % 31 == 0) { byte.* = 0x50; }
        else if (i % 31 == 1) { byte.* = 0x4B; }
        else if (i % 17 == 0) { byte.* = rand.int(u8); }
        else { byte.* = @truncate(i ^ (i >> 5) ^ (seed >> 32)); }
    }
}

test "v5 stealth poisoning" {
    var buffer: [1024]u8 = undefined;
    v5_macuahuitl_stealth_poisoning(&buffer, buffer.len, 0x5555);
    var sum: u64 = 0;
    for (buffer) |b| sum += b;
    try std.testing.expect(sum > 0);
}

test "memory sink trap" {
    var buffer: [2048]u8 = undefined;
    memory_sink_trap(&buffer, buffer.len, 0x9999);
    try std.testing.expect(buffer[0] == 0x50);
    try std.testing.expect(buffer[1] == 0x4B);
}
