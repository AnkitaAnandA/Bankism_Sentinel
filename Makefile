.PHONY: dev test eval load smoke build
PYTHON ?= python
URL ?= http://localhost:8000
dev:
	$(PYTHON) scripts/run_local.py
test: build
	cd backend && $(PYTHON) -m pytest -q && $(PYTHON) -m mypy app --strict && $(PYTHON) -m ruff check app tests && $(PYTHON) -m black app tests --check --workers 1
eval:
	$(PYTHON) scripts/evaluate.py
load:
	$(PYTHON) scripts/load_test.py $(URL)
smoke:
	$(PYTHON) scripts/smoke_test.py $(URL)
build:
	cd frontend && npm run build && npm run lint
