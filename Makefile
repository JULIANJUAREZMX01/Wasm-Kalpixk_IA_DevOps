# Wasm-Kalpixk_IA_DevOps — Comandos

.PHONY: run test benchmark bot dashboard setup gpu-check telegram whatsapp

setup:
	pip install -r requirements.txt

run:
	python main.py

api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v

benchmark:
	python benchmarks/benchmark_gpu.py

gpu-check:
	python3 -c "import torch; print('PyTorch:', torch.__version__); print('GPU:', torch.cuda.is_available()); print('VRAM:', round(torch.cuda.get_device_properties(0).total_memory/1e9,1), 'GB') if torch.cuda.is_available() else print('CPU mode')"

bot:
	TELEGRAM_ONLY=1 python -c "from src.channels.telegram_bot import KalpixkTelegramBot; b=KalpixkTelegramBot(); b.start_polling()"

dashboard:
	@echo "Dashboard en http://localhost:8000"
	uvicorn main:app --host 0.0.0.0 --port 8000

motor:
	python test_motor.py

docker-build:
	docker build -t kalpixk .

docker-run:
	docker run --device=/dev/kfd --device=/dev/dri -p 8000:8000 --env-file .env kalpixk

telegram-test:
	curl http://localhost:8000/status/telegram

whatsapp-test:
	curl http://localhost:8000/status/whatsapp

simulate-anomaly:
	curl http://localhost:8000/simulate/memory_spike
