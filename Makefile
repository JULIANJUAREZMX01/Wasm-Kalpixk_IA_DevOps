# Wasm-Kalpixk_IA_DevOps — Comandos principales

.PHONY: test benchmark api setup

setup:
	pip install -r requirements.txt

test:
	pytest tests/ -v

benchmark:
	python benchmarks/benchmark_gpu.py

api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

motor:
	python test_motor.py

gpu-check:
	python3 -c "import torch; print('PyTorch:', torch.__version__); print('GPU OK:', torch.cuda.is_available()); print('VRAM:', round(torch.cuda.get_device_properties(0).total_memory/1e9,1), 'GB') if torch.cuda.is_available() else None"
