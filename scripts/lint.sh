#!/bin/bash
set -e

# Run black in check mode
echo "Checking formatting..."
black --check .

# Run isort in check mode
echo "Checking imports..."
isort --check .

# Run flake8
echo "Running flake8..."
flake8 .

# Run mypy
echo "Running type checker..."
mypy .

echo "Lint complete!"
