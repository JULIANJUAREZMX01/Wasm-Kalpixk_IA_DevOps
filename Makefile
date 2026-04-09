.PHONY: setup install run test status clean help

help:
	@echo "🛡️  Kalpixk SIEM Control Board"
	@echo "----------------------------"
	@echo "make setup    - Instalar todo (Python, Rust, WASM, Web)"
	@echo "make run      - Iniciar SIEM (API + Dashboard)"
	@echo "make test     - Correr suite de pruebas"
	@echo "make status   - Ver estado del motor AI"
	@echo "make clean    - Limpiar artefactos temporales"

setup: install

install:
	bash setup.sh

run:
	python main.py

tui:
	python src/ui/terminal_dashboard.py

test:
	pytest tests/ -v --tb=short

status:
	python skills/kalpixk_status.py

wasm-build:
	cd crates/kalpixk-core && wasm-pack build --target web --release

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
	find . -name '*.pyc' -delete 2>/dev/null
	rm -rf web/dist
	rm -rf crates/kalpixk-core/pkg
