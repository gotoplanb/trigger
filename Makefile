.PHONY: setup run test lint format shell clean

# Python virtual environment
VENV = trigger
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Project settings
PORT = 8001
APP = app.main:app

# Create virtual environment and install dependencies
setup:
	pipx run virtualenv $(VENV)
	. ./$(VENV)/bin/activate && \
	$(PIP) install -r requirements.txt && \
	$(PIP) install -e .

# Format code
format: setup
	$(PYTHON) -m black .
	$(PYTHON) -m isort .

# Run linting
lint: setup
	$(PYTHON) -m pylint $$(git ls-files '*.py')

# Run tests
test: setup
	TESTING=true $(PYTHON) -m pytest tests/ -v

# Run the application
run: setup
	$(PYTHON) -m uvicorn $(APP) --reload --port $(PORT)

# Enter virtual environment shell
shell:
	. ./$(VENV)/bin/activate && exec "$$SHELL"

# Clean up temporary files
clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
