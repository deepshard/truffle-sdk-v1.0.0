#!/bin/bash
set -e

# Run formatters
echo "Running formatters..."
black .
isort .

# Run type checker
echo "Running type checker..."
mypy .

# Run tests with coverage
echo "Running tests..."
pytest --cov=truffle --cov-report=xml --cov-report=term-missing tests/

echo "Tests complete!"
