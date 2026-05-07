import json
import numpy as np
from wasmtime import Store, Instance, Linker
from src.runtime.wasm_loader import wasm_loader
from loguru import logger

WASM_PATH = "target/wasm32-wasip1/release/kalpixk_core.wasm"

class WasmFeatureExtractor:
    def __init__(self):
        try:
            self.module = wasm_loader.get_module(WASM_PATH)
            self.linker = Linker(wasm_loader.engine)
            self.linker.define_wasi()
            self.store = Store(wasm_loader.engine)
            from wasmtime import WasiConfig; self.store.set_wasi(WasiConfig()) # Basic WASI config
            self.instance = self.linker.instantiate(self.store, self.module)
            # Use lower-case alphanumeric name from WIT
            self.extract_fn = self.instance.exports(self.store).get("extractfeatures")
            # Helper for memory access if needed, but extract_features returns a Vec which wasm-bindgen handles
            # Actually wasm-bindgen exports usually take strings via some JS glue.
            # In wasmtime-py, we might need to handle the string allocation.
            logger.info("WasmFeatureExtractor initialized")
        except Exception as e:
            logger.error(f"Failed to init WasmFeatureExtractor: {e}")
            self.extract_fn = None

    def extract(self, metrics_dict: dict) -> np.ndarray:
        if not self.extract_fn:
            from src.runtime.fallback import fallback_extractor
            return fallback_extractor.extract(metrics_dict)

        try:
            # Call flat WIT function with individual arguments
            res = self.extract_fn(
                self.store,
                metrics_dict.get("instruction-count", 0),
                metrics_dict.get("memory-pages", 0),
                metrics_dict.get("fuel-consumed", 0),
                metrics_dict.get("wall-time-ns", 0),
                float(metrics_dict.get("entropy", 0.0)),
                metrics_dict.get("call-depth", 0),
                metrics_dict.get("import-calls", 0),
                metrics_dict.get("export-calls", 0),
            )
            return np.array(res, dtype=np.float32)
        except Exception as e:
            logger.warning(f"WASM extract failed: {e}. Using fallback.")
            from src.runtime.fallback import fallback_extractor
            return fallback_extractor.extract(metrics_dict)

feature_extractor = WasmFeatureExtractor()
