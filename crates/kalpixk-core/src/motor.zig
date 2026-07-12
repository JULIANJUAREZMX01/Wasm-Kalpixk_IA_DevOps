// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 9.0.0-XOCHIMILCO (Guerra Espectral)

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

/// [ATLATL-ORDNANCE] v9_xochimilco_jit_shield
/// Dual-map coupled chaotic entropy (Logistic + Dual coupling) for non-linear instruction padding.
pub export fn v9_xochimilco_jit_shield(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    const r1: f64 = 3.9999;
    const r2: f64 = 3.8888;
    var x: f64 = @as(f64, @floatFromInt(seed & 0xFFFFFFFF)) / 4294967296.0;
    var y: f64 = @as(f64, @floatFromInt(seed >> 32)) / 4294967296.0;
    if (x <= 0.0 or x >= 1.0) x = 0.5123;
    if (y <= 0.0 or y >= 1.0) y = 0.6789;

    const slice = target_ptr[0..target_len];
    var i: usize = 0;
    while (i < target_len) {
        // Logistic Map 1
        x = r1 * x * (1.0 - x);
        // Logistic Map 2
        y = r2 * y * (1.0 - y);
        // Coupling
        const entropy = @as(u8, @intFromFloat((x * 128.0 + y * 128.0)));

        const noise_type = entropy % 5;
        const noise_len = (entropy % 4) + 1;

        if (i + noise_len > target_len) break;

        for (0..noise_len) |j| {
            switch (noise_type) {
                0 => slice[i + j] = 0x90, // NOP
                1 => slice[i + j] = 0xF4, // HLT
                2 => slice[i + j] = 0xCC, // INT 3
                3 => slice[i + j] = 0x0F, // UD2 start
                4 => slice[i + j] = 0x0B, // UD2 end
                else => slice[i + j] = entropy,
            }
        }
        i += noise_len;
    }
}

/// [ATLATL-ORDNANCE] v9_xochimilco_active_memory_scrambling
/// Non-linear memory rotation and byte-swapping using coupled chaotic oscillators.
pub export fn v9_xochimilco_active_memory_scrambling(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    if (target_len < 32) return;
    const r: f64 = 3.9999;
    var x: f64 = @as(f64, @floatFromInt(seed & 0xFFFFFFFF)) / 4294967296.0;
    if (x <= 0.0 or x >= 1.0) x = 0.3333;

    const slice = target_ptr[0..target_len];
    for (0..16) |_| {
        x = r * x * (1.0 - x);
        const idx1 = @as(usize, @intFromFloat(x * @as(f64, @floatFromInt(target_len - 1))));
        x = r * x * (1.0 - x);
        const idx2 = @as(usize, @intFromFloat(x * @as(f64, @floatFromInt(target_len - 1))));

        const temp = slice[idx1];
        slice[idx1] = slice[idx2];
        slice[idx2] = temp;
    }
}

/// [ATLATL-ORDNANCE] v8_guerrilla_jit_shield (LEGACY)
pub export fn v8_guerrilla_jit_shield(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i < target_len) {
        const noise_type = rand.int(u8) % 4;
        const noise_len = (rand.int(u8) % 4) + 1; // 1 to 4 bytes

        if (i + noise_len > target_len) break;

        for (0..noise_len) |j| {
            switch (noise_type) {
                0 => slice[i + j] = 0x90, // NOP
                1 => slice[i + j] = 0xF4, // HLT
                2 => slice[i + j] = 0xCC, // INT 3
                else => slice[i + j] = rand.int(u8),
            }
        }
        i += noise_len;
    }
}

/// [ATLATL-ORDNANCE] v8_quantum_entropy_shredder (LEGACY)
pub export fn v8_quantum_entropy_shredder(target_ptr: [*]u8, target_len: usize, initial_x: f64) void {
    const r: f64 = 3.99;
    var x = initial_x;
    if (x <= 0.0 or x >= 1.0) x = 0.5;

    const slice = target_ptr[0..target_len];
    for (slice) |*byte| {
        x = r * x * (1.0 - x);
        byte.* = @intFromFloat(x * 255.0);
    }
}

/// [ATLATL-ORDNANCE] v8_pointer_poisoning (LEGACY)
pub export fn v8_pointer_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    if (target_len < 8) return;
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i + 8 <= target_len) : (i += 8) {
        const trap_type = rand.int(u8) % 4;
        switch (trap_type) {
            0 => { // NULL Pointer Trap
                @memset(slice[i .. i + 8], 0);
            },
            1 => { // Circular Jump Trap (0xEB 0xFE)
                slice[i] = 0xEB;
                slice[i + 1] = 0xFE;
                @memset(slice[i + 2 .. i + 8], 0x90);
            },
            2 => { // CPU Exhaustion / HLT Loop
                slice[i] = 0xF4;
                slice[i + 1] = 0xEB;
                slice[i + 2] = 0xFD; // JMP -3
                @memset(slice[i + 3 .. i + 8], 0xCC);
            },
            else => { // Random Poison
                for (0..8) |j| {
                    slice[i + j] = rand.int(u8);
                }
            },
        }
    }
}

/// [ATLATL-ORDNANCE] ATOMIC ACCESS VALIDATION
pub export fn validate_atomic_access(ptr: *atomic.Atomic(u8), expected: u8) bool {
    return ptr.load(.Monotonic) == expected;
}

/// [ATLATL-ORDNANCE] v7_stealth_poisoning (Legacy Support)
pub export fn v7_stealth_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
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

/// [ATLATL-ORDNANCE] v7_audit_tensor
pub export fn v7_audit_tensor(data_ptr: [*]const f32, data_len: usize) bool {
    if (data_len == 0) return true;
    const slice = data_ptr[0..data_len];

    var prev: f32 = slice[0];
    for (slice) |val| {
        if (!std.math.isFinite(val)) return false;
        const diff = @abs(val - prev);
        if (diff > 10.0) return false;
        prev = val;
    }
    return true;
}

/// [ATLATL-ORDNANCE] v7_guerrilla_memory_rotation
pub export fn v7_guerrilla_memory_rotation(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    if (target_len < 16) return;
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();

    const stride = (rand.int(usize) % (target_len / 4)) + 1;
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i + stride < target_len) : (i += stride) {
        const j = (i + stride) % target_len;
        const temp = slice[i];
        slice[i] = slice[j];
        slice[j] = temp;
    }
}

test "v8 guerrilla jit shield" {
    var buffer: [128]u8 = undefined;
    @memset(&buffer, 0);
    v8_guerrilla_jit_shield(&buffer, buffer.len, 0x12345);
    var sum: u64 = 0;
    for (buffer) |b| sum += b;
    try std.testing.expect(sum > 0);
}

test "v8 quantum entropy shredder" {
    var buffer: [1024]u8 = undefined;
    v8_quantum_entropy_shredder(&buffer, buffer.len, 0.5);
    const entropy = shannon_entropy(&buffer, buffer.len);
    try std.testing.expect(entropy > 7.5);
}

test "v8 pointer poisoning" {
    var buffer: [64]u8 = undefined;
    @memset(&buffer, 0xFF);
    v8_pointer_poisoning(&buffer, buffer.len, 0x54321);
    // Check if at least some bytes changed from 0xFF
    var changed = false;
    for (buffer) |b| {
        if (b != 0xFF) {
            changed = true;
            break;
        }
    }
    try std.testing.expect(changed);
}

test "v9 xochimilco jit shield" {
    var buffer: [256]u8 = undefined;
    @memset(&buffer, 0);
    v9_xochimilco_jit_shield(&buffer, buffer.len, 0xABCDEF1234567890);
    var entropy_sum: u64 = 0;
    for (buffer) |b| entropy_sum += b;
    try std.testing.expect(entropy_sum > 0);
}

test "v9 xochimilco memory scrambling" {
    var buffer: [128]u8 = undefined;
    for (0..buffer.len) |i| buffer[i] = @intCast(i);
    v9_xochimilco_active_memory_scrambling(&buffer, buffer.len, 0x1234567890ABCDEF);
    var changed = false;
    for (0..buffer.len) |i| {
        if (buffer[i] != @as(u8, @intCast(i))) {
            changed = true;
            break;
        }
    }
    try std.testing.expect(changed);
}
