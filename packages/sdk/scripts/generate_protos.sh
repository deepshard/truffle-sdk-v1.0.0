#!/bin/bash

# Exit on error
set -e

# Directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Project root directory (parent of script directory)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source and output directories
PROTO_DIR="$PROJECT_ROOT/src/trufflesdk/platform"
OUTPUT_DIR="$PROJECT_ROOT/src/trufflesdk/platform"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Generate Python code from proto
python -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    --pyi_out="$OUTPUT_DIR" \
    "$PROTO_DIR/sdk.proto"

# Fix imports in generated files
sed -i '' 's/^import sdk_pb2/from . import sdk_pb2/' "$OUTPUT_DIR/sdk_pb2_grpc.py" 