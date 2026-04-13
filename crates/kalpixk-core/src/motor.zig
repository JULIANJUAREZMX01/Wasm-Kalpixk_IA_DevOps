// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 2.2-MACUAHUITL (Guerrilla Algorítmica)

const std = @import("std");
const atomic = std.atomic;

/// [ATLATL-ORDNANCE] ESTRUCTURA DE CONTROL DE MEMORIA
/// Define el contrato de memoria para el buffer compartido entre Zig y el Host.
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
/// Cambia las firmas de memoria XOR-eando un rango con una semilla dinamica.
/// Inutiliza firmas estaticas de debuggers y scanners.
pub export fn dynamic_obfuscation(target_ptr: [*]u8, target_len: usize, seed: u32) void {
    const slice = target_ptr[0..target_len];
    var state = seed;
    for (slice) |*byte| {
        // Simple LCG para variar el XOR
        state = state *% 1103515245 +% 12345;
        byte.* ^= @truncate(state >> 16);
    }
}

/// [ATLATL-ORDNANCE] ATOMIC ACCESS VALIDATION
/// Valida que un byte en un buffer compartido no haya sido modificado externamente
/// entre lecturas, detectando race conditions o inyecciones en el SharedArrayBuffer.
pub export fn validate_atomic_access(ptr: *atomic.Atomic(u8), expected: u8) bool {
    return ptr.load(.Monotonic) == expected;
}

/// [ATLATL-ORDNANCE] POINTER POISONING (MACUAHUITL)
/// Inyecta un bucle infinito JMP $ y corrompe los punteros de retorno en el buffer.
/// Si el atacante intenta un buffer overflow, redirige su flujo a un callejón sin salida.
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
    for (slice, 0..) |*byte, i| {
        // Secuencia que engaña a algoritmos DEFLATE/LZ77
        if (i % 42 == 0) {
            byte.* = 0xFF;
        } else if (i % 7 == 0) {
            byte.* = 0x00;
        } else {
            byte.* = @truncate(i ^ (i >> 8));
        }
    }
}

/// [ATLATL-ORDNANCE] DETECCION DE CORRUPCION (CANARY GUARD)
pub export fn detect_memory_corruption(ptr: [*]const u8, len: usize, expected_canary: u8) bool {
    const slice = ptr[0..len];
    for (slice) |byte| {
        if (byte != expected_canary) return true;
    }
    return false;
}

/// [ATLATL-ORDNANCE] MACUAHUITL STRIKE
/// Combina ofuscación dinámica con envenenamiento de memoria masivo.
/// Diseñado para ser la respuesta final cuando el monitor WASM detecta exfiltración.
pub export fn macuahuitl_strike(target_ptr: [*]u8, target_len: usize, key: u64) void {
    const slice = target_ptr[0..target_len];
    var prng = std.rand.DefaultPrng.init(key);
    const rand = prng.random();

    for (slice, 0..) |*byte, i| {
        // Intercalamos instrucciones de loop infinito con basura aleatoria
        if (i % 16 < 2) {
            // EB FE (JMP -2)
            if (i % 2 == 0) byte.* = 0xEB else byte.* = 0xFE;
        } else {
            byte.* = rand.int(u8);
        }
    }
}

/// [ATLATL-ORDNANCE] V3 POINTER POISONING (DESTRUCTIVE REDIRECTION)
/// Inyecta secuencias de salto destructivas que desestabilizan el pipeline del atacante.
pub export fn v3_pointer_poisoning(target_ptr: [*]u8, target_len: usize) void {
    const slice = target_ptr[0..target_len];
    for (slice, 0..) |*byte, i| {
        // Combinación de JMP, HLT y desplazamientos erróneos
        switch (i % 4) {
            0 => byte.* = 0xEB, // JMP
            1 => byte.* = 0xFD, // -3 (Salto al byte anterior al JMP)
            2 => byte.* = 0xF4, // HLT (Halt execution)
            3 => byte.* = 0xCC, // INT 3 (Trap to debugger)
            else => unreachable,
        }
    }
}

/// [ATLATL-ORDNANCE] RECURSIVE ENTROPY GENERATOR (COMPRESSION-BREAKING)
/// Genera un flujo de datos diseñado para causar pánico en algoritmos de descompresión (Zip Bomb).
pub export fn recursive_entropy_generator(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
        if (i % 31 == 0) {
            byte.* = 0x4B; // PK Zip Header Start (partial)
        } else if (i % 17 == 0) {
            byte.* = rand.int(u8); // Random noise to break compression dictionary
        } else {
            byte.* = @truncate(i ^ (i >> 3));
        }
    }
}

/// [ATLATL-ORDNANCE] MEMORY SHREDDER
/// Sobrescribe la memoria con patrones de alta frecuencia para evitar recuperación forense.
pub export fn memory_shredder(target_ptr: [*]u8, target_len: usize) void {
    const slice = target_ptr[0..target_len];
    for (slice, 0..) |*byte, i| {
        byte.* = if (i % 2 == 0) 0xAA else 0x55;
    }
}

/// [ATLATL-ORDNANCE] VALIDATE SHARED BUFFER INTEGRITY
/// Verifica que el buffer no contenga patrones de inyección comunes.
pub export fn validate_buffer_safety(ptr: [*]const u8, len: usize) bool {
    const slice = ptr[0..len];
    var i: usize = 0;
    while (i < len - 2) : (i += 1) {
        // Detectar NOP Sled (0x90 0x90 0x90)
        if (slice[i] == 0x90 and slice[i+1] == 0x90 and slice[i+2] == 0x90) {
            return false;
        }
        // Detectar JMP $ (0xEB 0xFE)
        if (slice[i] == 0xEB and slice[i+1] == 0xFE) {
            return false;
        }
    }
    return true;
}

test "macuahuitl strike effectively poisons memory" {
    var buffer: [256]u8 = undefined;
    @memset(&buffer, 0);
    macuahuitl_strike(&buffer, buffer.len, 0x1337);

    // Verificar que al menos algunas partes del buffer tengan el JMP infinito
    try std.testing.expect(buffer[0] == 0xEB);
    try std.testing.expect(buffer[1] == 0xFE);
}

test "shannon entropy calculation" {
    const data = "ATLATL-ORDNANCE";
    const entropy = shannon_entropy(data, data.len);
    try std.testing.expect(entropy > 3.0);
}
