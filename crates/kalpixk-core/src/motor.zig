// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: La defensa no termina en el bloqueo.

const std = @import("std");

/// Entropia de Shannon en bits por simbolo
/// H = -SUM p(x) * log2(p(x))
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
/// Si se detecta un intento de desbordamiento, inyectamos punteros
/// que redirigen la ejecución a un bucle infinito.
/// En WASM, esto se traduce en corromper el buffer compartido del atacante.
pub export fn poison_pointers(target_ptr: [*]u8, target_len: usize) void {
    const slice = target_ptr[0..target_len];
    // Inyectamos el opcode de un bucle infinito JMP $ (0xEB 0xFE en x86,
    // pero aqui simplemente llenamos con basura que cause pánico o loops)
    for (slice, 0..) |*byte, i| {
        if (i % 2 == 0) {
            byte.* = 0xEB; // JMP short
        } else {
            byte.* = 0xFE; // offset -2 (bucle infinito)
        }
    }
}

/// [ATLATL-ORDNANCE] DETECCION DE CORRUPCION
/// Verifica si los canarios de memoria han sido alterados.
pub export fn detect_memory_corruption(ptr: [*]const u8, len: usize, expected_canary: u8) bool {
    const slice = ptr[0..len];
    for (slice) |byte| {
        if (byte != expected_canary) return true; // Corrompido
    }
    return false;
}

/// Entropia maxima en ventana deslizante
pub export fn sliding_window_entropy(
    data_ptr: [*]const u8,
    data_len: usize,
    window_size: usize,
) f64 {
    if (data_len < window_size or window_size == 0)
        return shannon_entropy(data_ptr, data_len);

    var max_h: f64 = 0.0;
    const step = window_size / 2;
    var i: usize = 0;
    while (i + window_size <= data_len) : (i += step) {
        const h = shannon_entropy(data_ptr + i, window_size);
        if (h > max_h) max_h = h;
    }
    return max_h;
}

test "poison pointers results in infinite loop pattern" {
    var buffer = [_]u8{0} ** 10;
    poison_pointers(&buffer, buffer.len);
    try std.testing.expectEqual(@as(u8, 0xEB), buffer[0]);
    try std.testing.expectEqual(@as(u8, 0xFE), buffer[1]);
}

test "detect corruption works" {
    const buffer = [_]u8{0xAA} ** 10;
    var corrupt_buffer = buffer;
    corrupt_buffer[5] = 0xFF;

    try std.testing.expect(detect_memory_corruption(&buffer, buffer.len, 0xAA) == false);
    try std.testing.expect(detect_memory_corruption(&corrupt_buffer, corrupt_buffer.len, 0xAA) == true);
}
