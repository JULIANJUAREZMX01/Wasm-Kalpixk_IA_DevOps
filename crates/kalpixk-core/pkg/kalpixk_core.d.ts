/* tslint:disable */
/* eslint-disable */

/**
 * Analiza un evento JSON y retorna nivel de amenaza + nodo dominante.
 * Exportado a JS para monitoreo activo.
 */
export function analyze_and_retaliate(event_json: string): string;

export function analyze_defense_nodes(event_json: string): string;

export function check_lockdown(event_json: string): boolean;

export function check_memory_bounds_wasp(offset: number, length: number, max_memory: number): string;

/**
 * Computa features UEBA desde una sesión de eventos JSON.
 * Input: JSON array de KalpixkEvent
 * Output: { features: [f64;32], risk_score: f64 }
 */
export function compute_ueba_features(events_json: string): string;

/**
 * Retorna los nombres de las 32 features
 */
export function get_feature_names(): string;

/**
 * [ATLATL-ORDNANCE] Security Telemetry
 */
export function get_security_telemetry(): string;

/**
 * Health check del módulo
 */
export function health_check(): string;

/**
 * Parsea un log JSON crudo (formato interno) y extrae features.
 */
export function parse_and_extract(raw_log: string): string;

/**
 * Parsea una línea de log y retorna JSON con el evento + severidad.
 */
export function parse_log_line(raw: string, source_type: string): string | undefined;

/**
 * Procesa un batch de logs JSON y retorna feature matrix + metadata.
 */
export function process_batch(logs_json: string, source_type: string): string;

export function validate_input_wasp(raw: string, max_len: number): string;

/**
 * Retorna la versión del motor
 */
export function version(): string;

/**
 * Bloquea un módulo WASM y genera reporte forense.
 */
export function wasm_lockdown(node: string, score: number, event_json: string): string;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly analyze_and_retaliate: (a: number, b: number) => [number, number];
    readonly analyze_defense_nodes: (a: number, b: number) => [number, number];
    readonly check_lockdown: (a: number, b: number) => number;
    readonly check_memory_bounds_wasp: (a: number, b: number, c: number) => [number, number];
    readonly compute_ueba_features: (a: number, b: number) => [number, number];
    readonly get_feature_names: () => [number, number];
    readonly get_security_telemetry: () => [number, number];
    readonly health_check: () => [number, number];
    readonly parse_and_extract: (a: number, b: number) => [number, number, number, number];
    readonly parse_log_line: (a: number, b: number, c: number, d: number) => [number, number];
    readonly process_batch: (a: number, b: number, c: number, d: number) => [number, number];
    readonly validate_input_wasp: (a: number, b: number, c: number) => [number, number];
    readonly version: () => [number, number];
    readonly wasm_lockdown: (a: number, b: number, c: number, d: number, e: number) => [number, number];
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __externref_table_dealloc: (a: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
