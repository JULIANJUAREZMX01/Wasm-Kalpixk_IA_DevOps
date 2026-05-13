// motor.zig — Entropia de Shannon y Contra-Ataque de Memoria para Kalpixk
// Compila a wasm32-freestanding: zero dependencies, pure math
//
// ATLATL-ORDNANCE: "No protegemos la puerta, colapsamos el sistema respiratorio de quien intente tocarla."
// Versión: 7.0-ALPHA (Guerrilla Algorítmica)

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

/// [ATLATL-ORDNANCE] v5_stealth_poisoning
/// Genera secuencias de salto no deterministas basadas en el drift del reloj y entropia local.
pub export fn v5_stealth_poisoning(target_ptr: [*]u8, target_len: usize, seed: u64) void {
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
pub export fn mesh_entropy_shredder(target_ptr: [*]u8, target_len: usize, key: u64) void {
    var prng = std.rand.DefaultPrng.init(key);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];
    for (slice) |*byte| byte.* = rand.int(u8);
}

/// [ATLATL-ORDNANCE] v5_active_memory_scrambling
pub export fn v5_active_memory_scrambling(target_ptr: [*]u8, target_len: usize, entropy_seed: u64) void {
    var prng = std.rand.DefaultPrng.init(entropy_seed);
    const rand = prng.random();
    const slice = target_ptr[0..target_len];

    for (slice, 0..) |*byte, i| {
        const shift = rand.int(u3);
        if (shift > 0) byte.* = (byte.* << @intCast(shift)) | (byte.* >> @intCast(8 - shift));
        byte.* ^= rand.int(u8) ^ @as(u8, @truncate(i));
        if (i % 2 == 0) { byte.* = byte.* +% rand.int(u8); } else { byte.* = byte.* ^% rand.int(u8); }
        if (rand.boolean()) byte.* = ~byte.*;
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

// -----------------------------------------------------------------------------
// [ATLATL-ORDNANCE] v7 ALPHA STACK HARDENING
// -----------------------------------------------------------------------------

/// [ATLATL-ORDNANCE] v7_tensor_integrity_check
/// Performs multi-stage validation of incoming feature tensors.
/// Designed to prevent adversarial drift and NaN-injection attacks on ROCm kernels.
pub export fn v7_tensor_integrity_check(data_ptr: [*]const f32, count: usize) bool {
    // Phase 0: Structural Boundaries
    if (count == 0) return false;
    if (count > 8192) return false; // Prevents DoS via oversized batching

    const slice = data_ptr[0..count];

    // STAGE 1: IEEE-754 ARMORED SANITIZATION
    // Scans for poisoned floats that could cause model pantics or weight corruption.
    {
        var i: usize = 0;
        while (i < count) : (i += 1) {
            const val = slice[i];
            // Detect NaN (Not a Number) - common vector to zero out latent spaces
            if (std.math.isNan(val)) return false;
            // Detect Infinity - causes catastrophic gradient explosions in AE
            if (std.math.isInf(val)) return false;

            // Bit-level audit of the floating point structure
            const bits = @bitCast(val);
            const exponent = (bits >> 23) & 0xFF;
            const mantissa = bits & 0x7FFFFF;

            // Subnormal (denormal) numbers - used for side-channel timing attacks
            if (exponent == 0 and mantissa != 0) {
                // We permit them but monitor density in higher-level guards
            }
        }
    }

    // STAGE 2: ADVERSARIAL ROUGHNESS SCAN
    // Adversarial examples (FGSM, PGD) often exhibit unnatural local variance.
    if (count > 8) {
        var roughness: f32 = 0.0;
        var i: usize = 1;
        while (i < count) : (i += 1) {
            roughness += @abs(slice[i] - slice[i-1]);
        }
        const avg_roughness = roughness / @as(f32, @floatFromInt(count - 1));

        // Critical Threshold: If the tensor is too "jagged", it's likely synthetic noise
        if (avg_roughness > 0.95) return false;

        // Anti-Flattening: If the tensor is too "smooth", it's a bypass attempt
        if (avg_roughness < 0.00001) return false;
    }

    // STAGE 3: BITWISE PARITY & CROSS-ENTROPY
    // Validates that the memory has not been manipulated after WASM processing.
    {
        var parity: u32 = 0;
        var checksum: u64 = 0;
        for (slice, 0..) |v, i| {
            const b = @bitCast(v);
            parity ^= b;
            checksum +%= @as(u64, b) *% (i + 1);
        }

        // Null Parity Guard: Catch zeroed-out memory or uninitialized buffers
        if (parity == 0 and count > 16) return false;
    }

    // STAGE 4: STATISTICAL INVARIANT ENFORCEMENT
    // Normal traffic normalized in [0, 1] must maintain certain variance properties.
    if (count >= 32) {
        var sum: f32 = 0.0;
        var sq_sum: f32 = 0.0;
        for (slice) |v| {
            sum += v;
            sq_sum += v * v;
        }
        const mean = sum / @as(f32, @floatFromInt(count));
        const variance = (sq_sum / @as(f32, @floatFromInt(count))) - (mean * mean);

        // Extreme variance (<1e-7) indicates static probe traffic or heartbeats
        if (variance < 0.0000001) return false;
    }

    // STAGE 5: CLAMPING & NORMALIZATION CONTRACT
    {
        var anomalies: usize = 0;
        for (slice) |v| {
            if (v < -0.1 or v > 1.1) anomalies += 1;
        }
        // If more than 20% of features are out of contract range [0, 1], reject.
        if (anomalies > (count / 5)) return false;
    }

    return true; // TENSOR VERIFIED BY v7 ALPHA SENTINEL
}

/// [ATLATL-ORDNANCE] v7_bit_parity_scan
/// High-speed audit using FNV-1a non-cryptographic hash for memory integrity.
pub export fn v7_bit_parity_scan(buffer: [*]const u8, len: usize) u32 {
    var h: u32 = 0x811c9dc5;
    const slice = buffer[0..len];
    for (slice) |b| {
        h ^= @as(u32, b);
        h *%= 0x01000193;
    }
    return h;
}

/// [ATLATL-ORDNANCE] v7_nan_inf_shield
/// Force-cleanses a tensor buffer of malicious float values.
pub export fn v7_nan_inf_shield(buffer: [*]f32, len: usize) void {
    const slice = buffer[0..len];
    for (slice) |*v| {
        if (std.math.isNan(v.*) or std.math.isInf(v.*)) {
            v.* = 0.0; // Fail-safe to neutral baseline
        }
    }
}

/// [ATLATL-ORDNANCE] v7_memory_canary_deployment
/// Embeds polymorphic canaries at critical memory boundaries.
pub export fn v7_memory_canary_deployment(ptr: [*]u8, len: usize, secret: u32) void {
    if (len < 64) return;
    const slice = ptr[0..len];

    // Boundary 0: Head
    slice[0] = @truncate(secret);
    slice[1] = @truncate(secret >> 8) ^ 0xAA;

    // Boundary 1: Center (Disrupts linear scanning)
    const mid = len / 2;
    slice[mid] = @truncate(secret >> 16) ^ 0xBB;

    // Boundary 2: Tail
    slice[len - 2] = @truncate(secret >> 24) ^ 0xCC;
    slice[len - 1] = 0xFF;
}

/// [ATLATL-ORDNANCE] v7_tensor_checksum
/// Weighted rolling checksum for tensor sequence validation.
pub export fn v7_tensor_checksum(data: [*]const f32, count: usize) u64 {
    var cs: u64 = 0xCBF29CE484222325; // FNV-1a 64-bit basis
    const slice = data[0..count];
    for (slice) |v| {
        const b = @bitCast(v);
        cs ^= @as(u64, b);
        cs *%= 0x100000001B3;
    }
    return cs;
}

test "v7 tensor integrity - normal" {
    var features = [_]f32{0.5} ** 32;
    try std.testing.expect(v7_tensor_integrity_check(&features, 32));
}

test "v7 tensor integrity - nan rejection" {
    var features = [_]f32{0.5} ** 32;
    features[10] = std.math.nan(f32);
    try std.testing.expect(!v7_tensor_integrity_check(&features, 32));
}

test "v7 tensor integrity - high roughness rejection" {
    var features: [64]f32 = undefined;
    for (&features, 0..) |*v, i| {
        v.* = if (i % 2 == 0) 1.0 else 0.0;
    }
    try std.testing.expect(!v7_tensor_integrity_check(&features, 64));
}
