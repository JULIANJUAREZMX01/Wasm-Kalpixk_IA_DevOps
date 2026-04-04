// motor.zig — Entropia de Shannon para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// La entropia de Shannon mide el "desorden" de una secuencia de bytes.
// Archivo normal:             H ~ 4-6 bits (texto, codigo)
// Archivo comprimido/cifrado: H ~ 7.9-8.0 bits (MAXIMA entropia)
//
// FILO DE OBSIDIANA: detectamos el cifrado de ransomware ANTES
// de que el directorio completo sea comprometido.

const std = @import("std");

/// Entropia de Shannon en bits por simbolo
/// H = -SUM p(x) * log2(p(x))
/// Complejidad: O(n) tiempo, O(1) espacio
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
/// Retorna: 0=normal, 1=sospechoso (H>7.2), 2=critico/ransomware (H>7.8)
/// Threshold calibrado para infraestructura CEDIS/WMS
pub export fn classify_entropy(data_ptr: [*]const u8, data_len: usize) u8 {
    const h = shannon_entropy(data_ptr, data_len);
    if (h >= 7.8) return 2;
    if (h >= 7.2) return 1;
    return 0;
}

/// Entropia maxima en ventana deslizante (50% overlap)
/// Detecta cifrado INCREMENTAL — el ransomware no cifra todo de golpe
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

test "zeros have zero entropy" {
    const data = [_]u8{0} ** 256;
    try std.testing.expectEqual(@as(f64, 0.0), shannon_entropy(&data, data.len));
}

test "uniform bytes have max entropy 8.0" {
    var data: [256]u8 = undefined;
    for (&data, 0..) |*b, i| b.* = @intCast(i);
    const h = shannon_entropy(&data, data.len);
    try std.testing.expect(h > 7.99 and h <= 8.0);
}

test "ASCII text has moderate entropy" {
    const text = "Kalpixk SIEM — AMD MI300X Zero-Trust Guardian";
    const h = shannon_entropy(text.ptr, text.len);
    try std.testing.expect(h > 3.0 and h < 6.0);
}

test "classify normal file" {
    const text = "normal log entry from syslog daemon process";
    try std.testing.expectEqual(@as(u8, 0), classify_entropy(text.ptr, text.len));
}
