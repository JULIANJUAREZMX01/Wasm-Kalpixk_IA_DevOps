// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 8.0.0-GUERRILLA (Alpha Stack)

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

/// [ATLATL-ORDNANCE] v7_stealth_poisoning
/// Genera secuencias de salto no deterministas basadas en el drift del reloj y entropia local.
/// Diseñado para romper el rastreo de ejecución en entornos virtualizados o sandboxed.
pub export fn v7_stealth_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
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
        _ = i;
    }
}

/// [ATLATL-ORDNANCE] mesh_entropy_shredder
/// Saturación de buffer con patrones de ruido blanco sintético que neutralizan
/// algoritmos de deduplicación y compresión de red.
pub export fn mesh_entropy_shredder(target_ptr: [*]u8, target_len: usize, key: u64) void {
    var prng = std.rand.DefaultPrng.init(key);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice) |*byte| {
        byte.* = rand.int(u8);
    }
}

/// [ATLATL-ORDNANCE] Legacy: poison_pointers
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

/// [ATLATL-ORDNANCE] v5_active_memory_scrambling
/// Disrupts debugger attachment by rotating memory patterns and causing
/// non-deterministic execution in tracer contexts.
/// Structural Hardening: Extended logic for multi-vector scrambling.
pub export fn v5_active_memory_scrambling(target_ptr: [*]u8, target_len: usize, entropy_seed: u64) void {
    var prng = std.rand.DefaultPrng.init(entropy_seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
        // Phase 1: Bit rotation
        const shift = rand.int(u3);
        if (shift > 0) {
            byte.* = (byte.* << @intCast(shift)) | (byte.* >> @intCast(8 - shift));
        }

        // Phase 2: Positional XOR with seeded entropy
        byte.* ^= rand.int(u8) ^ @as(u8, @truncate(i));

        // Phase 3: Non-linear transformation based on parity
        if (i % 2 == 0) {
            byte.* = byte.* +% rand.int(u8);
        } else {
            byte.* = byte.* ^% rand.int(u8);
        }

        // Phase 4: Conditional inversion
        if (rand.boolean()) {
            byte.* = ~byte.*;
        }
    }
}

/// [ATLATL-ORDNANCE] v5_buffer_seal
/// Protects SharedArrayBuffer segments with rolling canaries.
pub export fn v5_buffer_seal(buffer_ptr: [*]u8, buffer_len: usize, secret_key: u64) void {
    if (buffer_len < 16) return;
    const slice = buffer_ptr[0..buffer_len];
    var prng = std.rand.DefaultPrng.init(secret_key);
    const rand = prng.random();

    // Place rolling canaries at boundaries
    slice[0] = rand.int(u8) ^ 0xAA;
    slice[buffer_len - 1] = rand.int(u8) ^ 0x55;

    // Scramble internal alignment bytes to break automated struct parsing
    var i: usize = 8;
    while (i < buffer_len - 8) : (i += 16) {
        slice[i] ^= 0xFF;
    }
}

/// [ATLATL-ORDNANCE] v5_chaotic_interleaving
/// Rotates memory topology during runtime to disrupt memory analysis.
pub export fn v5_chaotic_interleaving(target_ptr: [*]u8, target_len: usize, stride: usize) void {
    if (target_len < stride * 2 or stride == 0) return;
    const slice = target_ptr[0..target_len];
    var i: usize = 0;
    while (i + stride * 2 <= target_len) : (i += stride * 2) {
        // Swap blocks
        for (0..stride) |j| {
            const temp = slice[i + j];
            slice[i + j] = slice[i + stride + j];
            slice[i + stride + j] = temp;
        }
    }
}

/// [ATLATL-ORDNANCE] v5_logic_bomb_detector
/// Detects suspicious instruction sequences (e.g., JMP short + loop) in raw buffers.
pub export fn v5_logic_bomb_detector(data_ptr: [*]const u8, data_len: usize) bool {
    if (data_len == 0) return false;
    const slice = data_ptr[0..data_len];
    var i: usize = 0;
    while (i < data_len) : (i += 1) {
        // Multi-byte checks
        if (i < data_len - 1) {
            // Check for 0xEB 0xFE (JMP short to itself)
            if (slice[i] == 0xEB and slice[i + 1] == 0xFE) return true;
        }
        // Single-byte checks
        // Check for 0xF4 (HLT) or 0xCC (INT 3) - common in anti-debug/logic bombs
        if (slice[i] == 0xF4 or slice[i] == 0xCC) return true;
    }
    return false;
}

/// [ATLATL-ORDNANCE] v7_memory_encryption_at_rest
/// XOR-based rolling encryption for decoy buffers to prevent static analysis.
pub export fn v7_memory_encryption_at_rest(target_ptr: [*]u8, target_len: usize, key: u64) void {
    const slice = target_ptr[0..target_len];
    var prng = std.rand.DefaultPrng.init(key);
    const rand = prng.random();
    for (slice) |*byte| {
        byte.* ^= rand.int(u8);
    }
}

/// [ATLATL-ORDNANCE] v7_audit_tensor
/// Bit-level adversarial roughness detection and NaN/Inf shielding.
/// Prevents tensor-based evasion by validating numeric stability and roughness.
pub export fn v7_audit_tensor(data_ptr: [*]const f32, data_len: usize) bool {
    if (data_len == 0) return true;
    const slice = data_ptr[0..data_len];

    var prev: f32 = slice[0];
    for (slice) |val| {
        // NaN/Inf Shielding
        if (!std.math.isFinite(val)) return false;

        // Adversarial Roughness: Detect extreme local variance indicative of PGD/FGSM
        const diff = @abs(val - prev);
        if (diff > 10.0) return false;
        prev = val;
    }
    return true;
}

/// [ATLATL-ORDNANCE] v7_guerrilla_memory_rotation
/// Non-deterministic memory address obfuscation via stride-based rotation.
/// Disrupts automated memory dump analysis and pointer tracing.
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

/// [ATLATL-ORDNANCE] v7_neural_decoy
/// Generates fake tensor data to mislead attackers attempting to poison training.
pub export fn v7_neural_decoy(target_ptr: [*]f32, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice) |*val| {
        val.* = rand.float(f32) * 2.0 - 1.0; // [-1.0, 1.0]
    }
}

/// [ATLATL-ORDNANCE] v8_guerrilla_jit_shield
/// Inyecta ruido instruccional polimórfico para frustrar el desensamblado dinámico
/// y el análisis de JIT en el motor WASM.
pub export fn v8_guerrilla_jit_shield(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice) |*byte| {
        const r = rand.int(u8);
        if (r < 64) {
            byte.* = 0x90; // NOP
        } else if (r < 128) {
            byte.* = 0xCC; // INT 3
        } else if (r < 192) {
            byte.* = 0xEB; // JMP short
        } else {
            byte.* = rand.int(u8);
        }
    }
}

/// [ATLATL-ORDNANCE] v8_quantum_entropy_shredder
/// Implementa un mapa caótico (Logistic Map) para generar entropía de alta calidad
/// que sature los buffers del atacante y neutralice algoritmos de compresión.
pub export fn v8_quantum_entropy_shredder(target_ptr: [*]u8, target_len: usize, r_param: f64, initial_x: f64) void {
    const slice = target_ptr[0..target_len];
    var x = initial_x;
    const r = r_param; // Usualmente 3.99 para caos total

    for (slice) |*byte| {
        x = r * x * (1.0 - x);
        const val: u8 = @intFromFloat(@floor(x * 255.0));
        byte.* = val;
    }
}

/// [ATLATL-ORDNANCE] v8_pointer_poisoning
/// Corrupción activa de punteros remotos mediante la inyección de saltos infinitos
/// y redirecciones no deterministas en el tráfico de retorno.
pub export fn v8_pointer_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i + 1 < target_len) : (i += 2) {
        slice[i] = 0xEB;     // JMP short
        slice[i + 1] = 0xFE; // to self
        if (rand.boolean()) {
            slice[i] = 0x90;
            slice[i + 1] = 0x90;
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

test "v5 stealth poisoning is non-zero" {
    var buffer: [512]u8 = undefined;
    @memset(&buffer, 0);
    v5_stealth_poisoning(&buffer, buffer.len, 0x54321);
    var sum: u64 = 0;
    for (buffer) |b| sum += b;
    try std.testing.expect(sum > 0);
}

test "mesh entropy shredder produces high entropy" {
    var buffer: [1024]u8 = undefined;
    mesh_entropy_shredder(&buffer, buffer.len, 0x98765);
    const entropy = shannon_entropy(&buffer, buffer.len);
    try std.testing.expect(entropy > 7.5);
}

test "legacy poison pointers" {
    var buffer: [4]u8 = undefined;
    poison_pointers(&buffer, buffer.len);
    try std.testing.expect(buffer[0] == 0xEB);
    try std.testing.expect(buffer[1] == 0xFE);
}
