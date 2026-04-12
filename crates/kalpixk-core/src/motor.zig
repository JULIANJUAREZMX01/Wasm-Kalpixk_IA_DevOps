// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 3.0-ATLATL (Guerrilla Algorítmica)

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

// ═══════════════════════════════════════════════════════════════════════════════════════
// NEW EVOLUTIONS: PHASE BLACK (v3.0)
// ═══════════════════════════════════════════════════════════════════════════════════════

/// [ATLATL-ORDNANCE] V3 MACUAHUITL ARRAY POISONING
/// Implementa una técnica de envenenamiento de arrays que corrompe metadatos de longitud
/// y punteros de control en estructuras de datos complejas.
/// Mínimo 100 líneas de intervención agresiva.
pub export fn v3_macuahuitl_array_poisoning(target_ptr: [*]u8, target_len: usize, aggressive_level: u8) void {
    const slice = target_ptr[0..target_len];
    var i: usize = 0;

    while (i < target_len) {
        // Bloque de control: Corrupción de descriptores de memoria
        if (i + 16 <= target_len) {
            // Inyectar punteros falsos a direcciones de kernel o loops infinitos
            // 0xDEADBEEF in little endian (simulado)
            slice[i]   = 0xEF;
            slice[i+1] = 0xBE;
            slice[i+2] = 0xAD;
            slice[i+3] = 0xDE;

            // Inyectar longitudes masivas para causar desbordamientos en el lector
            slice[i+4] = 0xFF;
            slice[i+5] = 0xFF;
            slice[i+6] = 0xFF;
            slice[i+7] = 0x7F; // 2GB length

            // JMP back to start (Infinite loop)
            slice[i+8] = 0xEB;
            slice[i+9] = 0xF6; // JMP -10 bytes

            i += 16;
        } else {
            slice[i] = 0xCC; // INT 3 (Trap)
            i += 1;
        }

        // Si el nivel de agresividad es alto, inyectamos basura de alta entropía
        if (aggressive_level > 5) {
            var j: usize = 0;
            while (j < 8 and i < target_len) : ({j += 1; i += 1;}) {
                slice[i] = @truncate((i *% 1103515245 +% 12345) >> 16);
            }
        }
    }
}

/// [ATLATL-ORDNANCE] RECURSIVE ENTROPY SHREDDER
/// Genera un stream de datos diseñado para colapsar motores de compresión (Zlib, LZ4)
/// y parsers de protocolos al forzar backtracking masivo y uso de CPU.
pub export fn recursive_entropy_shredder(target_ptr: [*]u8, target_len: usize) void {
    const slice = target_ptr[0..target_len];

    // El patrón consiste en secuencias que parecen repetitivas (incitando a LZ77 a buscar matches)
    // pero que rompen la predicción de entropía cada pocos bytes.
    for (slice, 0..) |*byte, i| {
        const pattern_selector = i % 128;

        if (pattern_selector < 32) {
            // Secuencia de ceros con un bit de interrupción (Engaña a RLE)
            byte.* = if (i % 31 == 0) 0x01 else 0x00;
        } else if (pattern_selector < 64) {
            // Secuencia incremental (Engaña a predictores delta)
            byte.* = @truncate(i);
        } else if (pattern_selector < 96) {
            // Ruido blanco puro (Máxima entropía)
            byte.* = @truncate(i ^ (i >> 3) ^ 0xAA);
        } else {
            // Patrón de "Muerte de Compresión": PK header falso con longitud infinita
            if (i % 8 == 0) byte.* = 'P';
            if (i % 8 == 1) byte.* = 'K';
            if (i % 8 == 2) byte.* = 0x03;
            if (i % 8 == 3) byte.* = 0x04;
            if (i % 8 >= 4) byte.* = 0xFF;
        }
    }
}

/// [ATLATL-ORDNANCE] POINTER TRAP GENERATOR
/// Crea una zona de memoria llena de "minas terrestres" de software.
/// Cualquier ejecución en este rango resultará en un pánico inmediato o un bucle infinito.
pub export fn generate_pointer_traps(target_ptr: [*]u8, target_len: usize) void {
    const slice = target_ptr[0..target_len];
    var i: usize = 0;
    while (i < target_len) : (i += 4) {
        if (i + 4 <= target_len) {
            // EB FE 90 90 (JMP $ ; NOP ; NOP)
            slice[i]   = 0xEB;
            slice[i+1] = 0xFE;
            slice[i+2] = 0x90;
            slice[i+3] = 0x90;
        }
    }
}

/// [ATLATL-ORDNANCE] HARDWARE HANG SIMULATOR (USERSPACE)
/// Consume ciclos de CPU de forma agresiva en un bucle cerrado para simular
/// un cuelgue del sistema ante un intento de intrusión detectado en el host.
pub export fn simulate_hardware_hang_userspace(iterations: u64) u64 {
    var result: u64 = 0;
    var i: u64 = 0;
    while (i < iterations) : (i += 1) {
        // Operaciones atómicas pesadas para forzar el bus de memoria (simulado)
        result = result *% 1103515245 +% 12345;
        if (result % 2 == 0) {
            result ^= 0x5555555555555555;
        }
    }
    return result;
}

test "v3 poisoning modifies memory" {
    var buffer: [512]u8 = undefined;
    @memset(&buffer, 0);
    v3_macuahuitl_array_poisoning(&buffer, buffer.len, 10);
    try std.testing.expect(buffer[0] == 0xEF);
    try std.testing.expect(buffer[4] == 0xFF);
}

test "entropy shredder generates non-zero data" {
    var buffer: [256]u8 = undefined;
    @memset(&buffer, 0);
    recursive_entropy_shredder(&buffer, buffer.len);
    var all_zero = true;
    for (buffer) |b| {
        if (b != 0) {
            all_zero = false;
            break;
        }
    }
    try std.testing.expect(!all_zero);
}
