// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 8.0.0-GUERRILLA (Structural Alpha Stack)

const std = @import("std");
const atomic = std.atomic;

/// [ATLATL-ORDNANCE] ESTRUCTURA DE CONTROL DE MEMORIA v8
pub const MemoryContract = struct {
    pub const MAX_BUFFER_SIZE: usize = 1024 * 1024; // 1MB
    pub const CANARY_VALUE: u8 = 0xDE;
    pub const POISON_VALUE: u8 = 0xAD;
    pub const V8_TRAP_BYTE: u8 = 0xCC; // INT 3
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

/// [ATLATL-ORDNANCE] DYNAMIC OBFUSCATION v8
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

/// [ATLATL-ORDNANCE] v8_guerrilla_jit_shield
/// Inyecta ruido polimórfico en búferes de instrucciones para frustrar el desensamblado
/// y análisis estático de JIT. Utiliza NOPs de longitud variable y trampas.
pub export fn v8_guerrilla_jit_shield(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i < target_len) {
        const op = rand.int(u8) % 100;
        if (op < 15) { // 15% de probabilidad de insertar NOP de 3 bytes (0x0F 0x1F 0x00)
            if (i + 3 <= target_len) {
                slice[i] = 0x0F;
                slice[i + 1] = 0x1F;
                slice[i + 2] = 0x00;
                i += 3;
            } else i += 1;
        } else if (op < 30) { // 15% de probabilidad de insertar INT 3 (Trap)
            slice[i] = 0xCC;
            i += 1;
        } else if (op < 40) { // 10% de probabilidad de insertar HLT (Privileged instruction)
            slice[i] = 0xF4;
            i += 1;
        } else {
            // No modificar el byte original o insertar NOP estándar
            if (rand.boolean()) {
               slice[i] = 0x90;
            }
            i += 1;
        }
    }
}

/// [ATLATL-ORDNANCE] v8_quantum_entropy_shredder
/// Generador de entropía caótica basado en el mapa logístico (Logistic Map).
/// r = 3.99 asegura comportamiento caótico total para saturar búferes.
pub export fn v8_quantum_entropy_shredder(target_ptr: [*]u8, target_len: usize, seed: f64) void {
    const slice = target_ptr[0..target_len];
    var x = seed;
    const r: f64 = 3.99;

    for (slice) |*byte| {
        x = r * x * (1.0 - x);
        byte.* = @intFromFloat(@floor(x * 255.0));
    }
}

/// [ATLATL-ORDNANCE] v8_pointer_poisoning
/// Inyecta punteros malformados y trampas de ejecución en la memoria del objetivo.
pub export fn v8_pointer_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i + 8 <= target_len) : (i += 8) {
        const choice = rand.int(u8) % 4;
        switch (choice) {
            0 => { // NULL Pointer
                @memset(slice[i..i+8], 0);
            },
            1 => { // Circular Jump (0xEB 0xFE) repeats
                var j: usize = 0;
                while (j < 8) : (j += 2) {
                    slice[i + j] = 0xEB;
                    slice[i + j + 1] = 0xFE;
                }
            },
            2 => { // CPU Exhaustion loop (While true)
                // x86_64: jmp $ (relative jump to self)
                slice[i] = 0xEB;
                slice[i + 1] = 0xFE;
                @memset(slice[i+2..i+8], 0x90);
            },
            3 => { // Memory trap
                @memset(slice[i..i+8], 0xCC);
            },
            else => unreachable,
        }
    }
}

/// [ATLATL-ORDNANCE] Legacy: v7_stealth_poisoning
pub export fn v7_stealth_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice) |*byte| {
        const op = rand.int(u8) % 10;
        switch (op) {
            0 => byte.* = 0xEB,
            1 => byte.* = 0xFE,
            2 => byte.* = 0xF4,
            3 => byte.* = 0xCC,
            4 => byte.* = 0x0F,
            5 => byte.* = 0x0B,
            6 => byte.* = 0x90,
            7 => byte.* = 0xE9,
            else => byte.* = rand.int(u8),
        }
    }
}

/// [ATLATL-ORDNANCE] Legacy: mesh_entropy_shredder
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

/// [ATLATL-ORDNANCE] v5_buffer_seal
pub export fn v5_buffer_seal(buffer_ptr: [*]u8, buffer_len: usize, secret_key: u64) void {
    if (buffer_len < 16) return;
    const slice = buffer_ptr[0..buffer_len];
    var prng = std.rand.DefaultPrng.init(secret_key);
    const rand = prng.random();

    slice[0] = rand.int(u8) ^ 0xAA;
    slice[buffer_len - 1] = rand.int(u8) ^ 0x55;

    var i: usize = 8;
    while (i < buffer_len - 8) : (i += 16) {
        slice[i] ^= 0xFF;
    }
}

/// [ATLATL-ORDNANCE] v5_chaotic_interleaving
pub export fn v5_chaotic_interleaving(target_ptr: [*]u8, target_len: usize, stride: usize) void {
    if (target_len < stride * 2 or stride == 0) return;
    const slice = target_ptr[0..target_len];
    var i: usize = 0;
    while (i + stride * 2 <= target_len) : (i += stride * 2) {
        for (0..stride) |j| {
            const temp = slice[i + j];
            slice[i + j] = slice[i + stride + j];
            slice[i + stride + j] = temp;
        }
    }
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

test "v8 guerrilla jit shield inserts noise" {
    var buffer: [100]u8 = undefined;
    @memset(&buffer, 0);
    v8_guerrilla_jit_shield(&buffer, buffer.len, 0x12345678);
    var changed = false;
    for (buffer) |b| {
        if (b != 0) {
            changed = true;
            break;
        }
    }
    try std.testing.expect(changed);
}

test "v8 quantum entropy shredder produces high entropy" {
    var buffer: [1000]u8 = undefined;
    v8_quantum_entropy_shredder(&buffer, buffer.len, 0.5);
    const entropy = shannon_entropy(&buffer, buffer.len);
    try std.testing.expect(entropy > 7.0);
}

test "v8 pointer poisoning applies traps" {
    var buffer: [64]u8 = undefined;
    @memset(&buffer, 0xFF);
    v8_pointer_poisoning(&buffer, buffer.len, 0xABCDEF);
    var traps = false;
    for (buffer) |b| {
        if (b == 0xCC or b == 0x00 or b == 0xEB or b == 0xFE) {
            traps = true;
            break;
        }
    }
    try std.testing.expect(traps);
}
