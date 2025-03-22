.PHONY: setup run test lint format shell clean

# Create virtual environment and install dependencies
setup:
	python -m venv trigger
	. trigger/bin/activate && pip install -e .
	. trigger/bin/activate && pip install -r requirements.txt

# Run the application
run:
	. trigger/bin/activate && uvicorn app.main:app --reload

# Run tests
test:
	TESTING=true . trigger/bin/activate && pytest -v

# Run linting
lint:
	. trigger/bin/activate && pylint app tests

# Format code
format:
	. trigger/bin/activate && black app tests
	. trigger/bin/activate && isort app tests

# Enter virtual environment shell
shell:
	. trigger/bin/activate && exec "$$SHELL"

# Clean up temporary files
clean:
	rm -rf __pycache__
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
