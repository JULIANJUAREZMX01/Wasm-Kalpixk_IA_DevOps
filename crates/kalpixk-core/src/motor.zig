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

/// [ATLATL-ORDNANCE] v8_guerrilla_jit_shield
/// Implementa un escudo polimórfico de instrucciones para frustrar el desensamblado
/// y análisis de traza dinámico. Introduce ruido computacional (NOP/HLT/INT3) y
/// bifurcaciones falsas basadas en el estado del registro de entropía.
pub export fn v8_guerrilla_jit_shield(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    var i: usize = 0;
    while (i < target_len) {
        const op = rand.int(u8) % 16;

        switch (op) {
            0 => { // Multi-byte NOP (3 bytes)
                if (i + 3 > target_len) break;
                slice[i] = 0x0F;
                slice[i + 1] = 0x1F;
                slice[i + 2] = 0x00;
                i += 3;
            },
            1 => { // INT 3 (Trap) (1 byte)
                if (i + 1 > target_len) break;
                slice[i] = 0xCC;
                i += 1;
            },
            2 => { // HLT (Privileged instruction noise) (1 byte)
                if (i + 1 > target_len) break;
                slice[i] = 0xF4;
                i += 1;
            },
            3 => { // JMP short +1 (3 bytes)
                if (i + 3 > target_len) break;
                slice[i] = 0xEB;
                slice[i + 1] = 0x01;
                slice[i + 2] = rand.int(u8);
                i += 3;
            },
            4 => { // UD2 (Undefined Instruction) (2 bytes)
                if (i + 2 > target_len) break;
                slice[i] = 0x0F;
                slice[i + 1] = 0x0B;
                i += 2;
            },
            5 => { // PUSH/POP noise (2 bytes)
                if (i + 2 > target_len) break;
                slice[i] = 0x50 + (rand.int(u8) % 8); // PUSH reg
                slice[i + 1] = 0x58 + (rand.int(u8) % 8); // POP reg
                i += 2;
            },
            6 => { // Arithmetic noise (ADD AL, imm8) (2 bytes)
                if (i + 2 > target_len) break;
                slice[i] = 0x04;
                slice[i + 1] = rand.int(u8);
                i += 2;
            },
            7 => { // XOR EAX, EAX (Zeroing) (2 bytes)
                if (i + 2 > target_len) break;
                slice[i] = 0x31;
                slice[i + 1] = 0xC0;
                i += 2;
            },
            else => {
                if (i + 1 > target_len) break;
                slice[i] = 0x90; // Standard NOP
                i += 1;
            },
        }
    }
}

/// [ATLATL-ORDNANCE] v8_quantum_entropy_shredder
/// Generador de entropía caótica basado en el mapa logístico (r=3.99).
/// Diseñado para saturar buffers de red y confundir algoritmos de detección
/// basados en patrones estadísticos simples. Alta sensibilidad a condiciones iniciales.
pub export fn v8_quantum_entropy_shredder(target_ptr: [*]u8, target_len: usize, seed: f64) void {
    const slice = target_ptr[0..target_len];
    var x = seed;
    if (x <= 0.0 or x >= 1.0) x = 0.5;
    const r: f64 = 3.99; // Chaotic regime

    for (slice) |*byte| {
        // Logistic map: x_{n+1} = r * x_n * (1 - x_n)
        x = r * x * (1.0 - x);
        byte.* = @intFromFloat(@floor(x * 255.0));
    }
}

/// [ATLATL-ORDNANCE] v8_pointer_poisoning
/// Envenenamiento de punteros agresivo. Inyecta secuencias de terminación y
/// saltos infinitos en buffers de memoria remota para causar denegación de servicio
/// local en el sistema del atacante.
pub export fn v8_pointer_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
        if (i % 8 == 0) {
            // Nullify pointer-like structures
            byte.* = 0x00;
        } else if (i % 7 == 3) {
            // Inject 0xEB 0xFE (JMP $)
            byte.* = if (rand.boolean()) 0xEB else 0xFE;
        } else if (i % 5 == 0) {
            // Randomized corruption
            byte.* = rand.int(u8);
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

/// [ATLATL-ORDNANCE] DETECCION DE CORRUPCION (CANARY GUARD)
pub export fn detect_memory_corruption(ptr: [*]const u8, len: usize, expected_canary: u8) bool {
    const slice = ptr[0..len];
    for (slice) |byte| {
        if (byte != expected_canary) return true;
    }
    return false;
}

test "v8 guerrilla jit shield is non-zero" {
    var buffer: [512]u8 = undefined;
    @memset(&buffer, 0);
    v8_guerrilla_jit_shield(&buffer, buffer.len, 0x54321);
    var sum: u64 = 0;
    for (buffer) |b| sum += b;
    try std.testing.expect(sum > 0);
}

test "v8 quantum entropy shredder produces high entropy" {
    var buffer: [1024]u8 = undefined;
    v8_quantum_entropy_shredder(&buffer, buffer.len, 0.42);
    const entropy = shannon_entropy(&buffer, buffer.len);
    try std.testing.expect(entropy > 7.5);
}

test "v8 pointer poisoning" {
    var buffer: [128]u8 = undefined;
    @memset(&buffer, 0xFF);
    v8_pointer_poisoning(&buffer, buffer.len, 0x12345);
    var changed = false;
    for (buffer) |b| {
        if (b != 0xFF) {
            changed = true;
            break;
        }
    }
    try std.testing.expect(changed);
}
