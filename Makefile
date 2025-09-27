.PHONY: install dev-install run test clean build package help init-db

# Default target
help:
	@echo "AI Cycling Coach - Available commands:"
	@echo "  install      - Install the application"
	@echo "  dev-install  - Install in development mode"
	@echo "  run          - Run the application"
	@echo "  init-db      - Initialize the database"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build distribution packages"
	@echo "  package      - Create standalone executable"

# Installation
install:
	.venv/bin/pip install .

dev-install:
	.venv/bin/pip install -r requirements.txt

# Database initialization
init-db:
	@echo "Initializing database..."
	@mkdir -p data
	@.venv/bin/python -m alembic upgrade head
	@echo "Database initialized successfully!"

# Run application
run:
	.venv/bin/python main.py

# Testing
test:
	.venv/bin/pytest

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build distribution
build: clean
	python -m build

# Package as executable (requires PyInstaller)
package:
	@echo "Creating standalone executable..."
	@.venv/bin/pip install pyinstaller
	@.venv/bin/pyinstaller --onefile --name cycling-coach main.py
	@echo "Executable created in dist/cycling-coach"

# Development tools
lint:
	black --check .
	isort --check-only .

format:
	black .
	isort .

# Quick setup for new users
setup: dev-install init-db
	@echo "Setup complete! Run 'make run' to start the application."