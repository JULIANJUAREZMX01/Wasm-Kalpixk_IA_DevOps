// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: La defensa no termina en el bloqueo.

const std = @import("std");

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

/// [ATLATL-ORDNANCE] POINTER POISONING
/// Inyecta un bucle infinito JMP $ en el buffer del atacante.
pub export fn poison_pointers(target_ptr: [*]u8, target_len: usize) void {
    const slice = target_ptr[0..target_len];
    for (slice, 0..) |*byte, i| {
        if (i % 2 == 0) {
            byte.* = 0xEB; // JMP short
        } else {
            byte.* = 0xFE; // offset -2
        }
    }
}

/// [ATLATL-ORDNANCE] MEMORY RANGE POISONING
/// Corrompe un rango de memoria con basura de alta entropía para romper parsers/debuggers.
pub export fn poison_memory_range(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];
    for (slice) |*byte| {
        byte.* = rand.int(u8);
    }
}

/// [ATLATL-ORDNANCE] RECURSIVE ENTROPY TRAP (ZIP BOMB CHUNK)
/// Genera un chunk de datos que parece comprimible pero expande entropía al procesarse.
pub export fn generate_recursive_entropy_trap(target_ptr: [*]u8, target_len: usize) void {
    const slice = target_ptr[0..target_len];
    // Patrón repetitivo pero con variaciones de bit que confunden algoritmos de compresión
    // y pueden causar desbordamientos en parsers de bajo nivel.
    for (slice, 0..) |*byte, i| {
        if (i % 42 == 0) {
            byte.* = 0xFF;
        } else {
            byte.* = @truncate(i ^ (i >> 8));
        }
    }
}

/// [ATLATL-ORDNANCE] DETECCION DE CORRUPCION
pub export fn detect_memory_corruption(ptr: [*]const u8, len: usize, expected_canary: u8) bool {
    const slice = ptr[0..len];
    for (slice) |byte| {
        if (byte != expected_canary) return true;
    }
    return false;
}

test "poison pointers results in infinite loop pattern" {
    var buffer = [_]u8{0} ** 10;
    poison_pointers(&buffer, buffer.len);
    try std.testing.expectEqual(@as(u8, 0xEB), buffer[0]);
    try std.testing.expectEqual(@as(u8, 0xFE), buffer[1]);
}

test "memory range poisoning produces high entropy" {
    var buffer = [_]u8{0} ** 1024;
    poison_memory_range(&buffer, buffer.len, 1234);
    const h = shannon_entropy(&buffer, buffer.len);
    try std.testing.expect(h > 7.0);
}
