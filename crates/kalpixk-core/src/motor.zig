// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 8.0-GUERRILLA (Guerrilla Algorítmica)

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

/// [ATLATL-ORDNANCE] v8_guerrilla_jit_shield
/// Implementación de acolchado de instrucciones polimórficas con ruido NOP/HLT/INT3.
/// Frustra el desensamblado y el análisis de JIM mediante la inserción de secuencias no deterministas.
pub export fn v8_guerrilla_jit_shield(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i < target_len) {
        const op = rand.int(u8) % 12;
        switch (op) {
            0 => { // 1-byte NOP
                slice[i] = 0x90;
                i += 1;
            },
            1 => { // HLT
                slice[i] = 0xF4;
                i += 1;
            },
            2 => { // INT 3
                slice[i] = 0xCC;
                i += 1;
            },
            3 => { // 2-byte NOP (0x66 0x90)
                if (i + 2 <= target_len) {
                    slice[i] = 0x66;
                    slice[i + 1] = 0x90;
                    i += 2;
                } else {
                    slice[i] = 0x90;
                    i += 1;
                }
            },
            4 => { // 3-byte NOP (0x0F 0x1F 0x00)
                if (i + 3 <= target_len) {
                    slice[i] = 0x0F;
                    slice[i + 1] = 0x1F;
                    slice[i + 2] = 0x00;
                    i += 3;
                } else {
                    slice[i] = 0x90;
                    i += 1;
                }
            },
            5 => { // UD2 (Undefined Instruction)
                if (i + 2 <= target_len) {
                    slice[i] = 0x0F;
                    slice[i + 1] = 0x0B;
                    i += 2;
                } else {
                    slice[i] = 0x90;
                    i += 1;
                }
            },
            else => {
                slice[i] = rand.int(u8);
                i += 1;
            },
        }
    }
}

/// [ATLATL-ORDNANCE] v8_quantum_entropy_shredder
/// Generación de entropía caótica basada en el mapa logístico (r=3.99).
/// Produce flujos de datos de alta entropía para saturar buffers de atacantes.
pub export fn v8_quantum_entropy_shredder(target_ptr: [*]u8, target_len: usize, initial_x: f64) void {
    const slice = target_ptr[0..target_len];
    var x = initial_x;
    if (x <= 0.0 or x >= 1.0) x = 0.5;
    const r = 3.99;

    for (slice) |*byte| {
        // Logistic Map: x_{n+1} = r * x_n * (1 - x_n)
        x = r * x * (1.0 - x);
        byte.* = @intFromFloat(x * 255.0);
    }
}

/// [ATLATL-ORDNANCE] v8_pointer_poisoning
/// Corrupción de punteros remotos con secuencias de salto no deterministas.
/// Redirige la ejecución a trampas de CPU o bucles infinitos.
pub export fn v8_pointer_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i < target_len) {
        if (i + 2 <= target_len) {
            // JMP short to self (0xEB 0xFE) or randomized jumps
            if (rand.boolean()) {
                slice[i] = 0xEB;
                slice[i + 1] = 0xFE;
            } else {
                slice[i] = 0xEB;
                slice[i + 1] = rand.int(u8);
            }
            i += 2;
        } else {
            slice[i] = 0xCC; // INT 3
            i += 1;
        }
    }
}

/// [ATLATL-ORDNANCE] v7_guerrilla_memory_rotation (Legacy)
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

/// [ATLATL-ORDNANCE] v5_active_memory_scrambling (Legacy)
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

/// [ATLATL-ORDNANCE] v5_chaotic_interleaving (Legacy)
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

test "v8 quantum entropy shredder produces high entropy" {
    var buffer: [1024]u8 = undefined;
    v8_quantum_entropy_shredder(&buffer, buffer.len, 0.35);
    const entropy = shannon_entropy(&buffer, buffer.len);
    try std.testing.expect(entropy > 7.5);
}

test "v8 guerrilla jit shield is non-zero" {
    var buffer: [512]u8 = undefined;
    @memset(&buffer, 0);
    v8_guerrilla_jit_shield(&buffer, buffer.len, 0x12345);
    var sum: u64 = 0;
    for (buffer) |b| sum += b;
    try std.testing.expect(sum > 0);
}
