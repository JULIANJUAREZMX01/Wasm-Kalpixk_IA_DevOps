import os
from wasmtime import Engine, Module
from loguru import logger

class WasmLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WasmLoader, cls).__new__(cls)
            cls._instance.engine = Engine()
            cls._instance.module_cache = {}
        return cls._instance

    def get_module(self, path: str) -> Module:
        if path not in self.module_cache:
            if not os.path.exists(path):
                logger.error(f"WASM file not found: {path}")
                raise FileNotFoundError(path)
            logger.info(f"Compiling WASM module: {path}")
            self.module_cache[path] = Module.from_file(self.engine, path)
        return self.module_cache[path]

wasm_loader = WasmLoader()
