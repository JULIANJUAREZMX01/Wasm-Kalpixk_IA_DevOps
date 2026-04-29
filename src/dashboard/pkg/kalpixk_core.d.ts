/* tslint:disable */
/* eslint-disable */

export function analyze_and_retaliate(json_event: string): string;

export function compute_ueba_features(events_json: string): string;

export function extract_features_legacy(json_event: string): Float32Array;

export function get_feature_names(): string[];

export function get_security_telemetry(): string;

export function health_check(): string;

export function parse_log_line(raw: string, source_type: string): string | undefined;

export function process_batch(logs_json: string, source_type: string): string;

export function version(): string;

export function wasm_lockdown(node: string, score: number, event_json: string): string;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly analyze_and_retaliate: (a: number, b: number) => [number, number];
    readonly "cabi_post_extract_features": (a: number) => void;
    readonly compute_ueba_features: (a: number, b: number) => [number, number];
    readonly extract_features_legacy: (a: number, b: number) => [number, number];
    readonly get_feature_names: () => [number, number];
    readonly get_security_telemetry: () => [number, number];
    readonly health_check: () => [number, number];
    readonly "extract_features": (a: bigint, b: number, c: bigint, d: bigint, e: number, f: number, g: number, h: number) => number;
    readonly parse_log_line: (a: number, b: number, c: number, d: number) => [number, number];
    readonly process_batch: (a: number, b: number, c: number, d: number) => [number, number];
    readonly version: () => [number, number];
    readonly wasm_lockdown: (a: number, b: number, c: number, d: number, e: number) => [number, number];
    readonly cabi_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly cabi_realloc_wit_bindgen_0_35_0: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __externref_drop_slice: (a: number, b: number) => void;
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
