# FanDraGen — use the venv Python directly (no manual `source .venv/bin/activate`).
# Requires GNU Make (macOS/Linux) or `make` from Chocolatey/WSL on Windows.

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
# Default sample index for `make sample` when N is omitted
N ?= 0

.PHONY: help setup run test demo sample prompt

help:
	@echo "FanDraGen commands:"
	@echo "  make setup     Create .venv and install requirements (run once per clone)"
	@echo "  make run       Run the default demo prompt (same as: python main.py)"
	@echo "  make demo      Same as make run"
	@echo "  make sample N=3   Run sample index N (0-7)"
	@echo "  make prompt P=\"...\"  Run a custom prompt"
	@echo "  make test      Run pytest"
	@echo ""
	@echo "Examples:"
	@echo "  make setup && make run"
	@echo "  make sample N=1"
	@echo "  make prompt P=\"Who is the best waiver pickup right now?\""

setup: .venv/bin/python
	$(PIP) install -q --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Setup complete. Try: make run"

.venv/bin/python:
	python3 -m venv .venv

run demo: .venv/bin/python
	@test -f $(PYTHON) || (echo "Run: make setup" && exit 1)
	$(PYTHON) main.py

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
