.PHONY: setup clean

setup:
	uv venv
	uv sync

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".venv" -exec rm -rf {} +
