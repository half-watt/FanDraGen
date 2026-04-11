# FanDraGen — use the venv Python directly (no manual `source .venv/bin/activate`).
# Requires GNU Make (macOS/Linux) or `make` from Chocolatey/WSL on Windows.

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
STREAMLIT := .venv/bin/streamlit
WEB_APP := web/app.py
# Default sample index for `make sample` when N is omitted
N ?= 0

.PHONY: help setup run cli test demo sample prompt

help:
	@echo "FanDraGen commands:"
	@echo "  make setup     Create .venv and install requirements (run once per clone)"
	@echo "  make run       Launch the Streamlit UI (default)"
	@echo "  make cli       Run the terminal demo (python main.py)"
	@echo "  make demo      Same as make cli"
	@echo "  make sample N=3   Run CLI sample index N (0-7)"
	@echo "  make prompt P=\"...\"  Run a custom CLI prompt"
	@echo "  make test      Run pytest"
	@echo ""
	@echo "Python: use 3.11+ when possible (see .python-version). eval_type_backport helps older Pythons."
	@echo ""
	@echo "Examples:"
	@echo "  make setup && make run"
	@echo "  make cli"
	@echo "  make sample N=1"

setup: .venv/bin/python
	$(PIP) install -q --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Setup complete. Try: make run"

.venv/bin/python:
	python3 -m venv .venv

# Web UI (Streamlit)
run: .venv/bin/python
	@test -f $(PYTHON) || (echo "Run: make setup" && exit 1)
	$(STREAMLIT) run $(WEB_APP) --server.port 8501 --browser.gatherUsageStats false

# Terminal demo (legacy main.py)
cli: .venv/bin/python
	@test -f $(PYTHON) || (echo "Run: make setup" && exit 1)
	$(PYTHON) main.py

demo: cli

# Usage: make sample N=3
sample: .venv/bin/python
	@test -f $(PYTHON) || (echo "Run: make setup" && exit 1)
	$(PYTHON) main.py --sample $(N)

# Usage: make prompt P="your question"
prompt: .venv/bin/python
	@test -f $(PYTHON) || (echo "Run: make setup" && exit 1)
	$(PYTHON) main.py --prompt "$(P)"

test: .venv/bin/python
	@test -f $(PYTHON) || (echo "Run: make setup" && exit 1)
	$(PYTHON) -m pytest -q
