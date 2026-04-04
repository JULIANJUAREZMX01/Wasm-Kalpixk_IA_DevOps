# Wasm-Kalpixk_IA_DevOps — Comandos

.PHONY: run test benchmark status detect train bot dashboard setup gpu-check ci

setup:
	pip install -r requirements.txt

# ── Core ─────────────────────────────────────────────────────
run:
	python main.py

api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# ── Tests ─────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-ci:
	pytest tests/ -v --tb=short --junit-xml=test-results.xml

# ── Skills ────────────────────────────────────────────────────
status:
	python skills/kalpixk_status.py

status-json:
	python skills/kalpixk_status.py --json

train:
	python skills/train_model.py --samples 1000 --epochs 100

train-notify:
	python skills/train_model.py --samples 1000 --epochs 100 --notify

detect:
	python skills/detect_now.py

detect-loop:
	python skills/detect_now.py --loop 30 --notify

benchmark:
	python skills/benchmark.py --samples 100000 --runs 5

benchmark-notify:
	python skills/benchmark.py --samples 100000 --runs 5 --notify

# ── GPU ────────────────────────────────────────────────────────
gpu-check:
	python3 -c "import torch; gpu=torch.cuda.is_available(); print('GPU:', gpu); print('Name:', torch.cuda.get_device_name(0) if gpu else 'N/A'); print('VRAM:', round(torch.cuda.get_device_properties(0).total_memory/1e9,1),'GB') if gpu else None"

# ── Bot Telegram ──────────────────────────────────────────────
bot:
	python -c "from src.channels.telegram_bot import KalpixkTelegramBot; b=KalpixkTelegramBot(); b.start_polling()"

# ── Docker ────────────────────────────────────────────────────
docker-build:
	docker build -t kalpixk .

docker-run:
	docker run --device=/dev/kfd --device=/dev/dri -p 8000:8000 --env-file .env kalpixk

docker-gpu-check:
	docker run --device=/dev/kfd --device=/dev/dri kalpixk python3 -c "import torch; print('GPU:', torch.cuda.is_available())"

# ── API Tests ──────────────────────────────────────────────────
test-api:
	@curl -s http://localhost:8000/health | python3 -m json.tool

test-telegram:
	@curl -s http://localhost:8000/status/telegram | python3 -m json.tool

test-whatsapp:
	@curl -s http://localhost:8000/status/whatsapp | python3 -m json.tool

test-anomaly:
	@curl -s http://localhost:8000/simulate/memory_spike | python3 -m json.tool

# ── Limpieza ──────────────────────────────────────────────────
clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; echo done
	find . -name '*.pyc' -delete 2>/dev/null; echo done

motor:
	python test_motor.py
