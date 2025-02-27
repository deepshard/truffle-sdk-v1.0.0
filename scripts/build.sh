#!/bin/bash
set -e

# Log if API key is set and its source
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "OPENAI_API_KEY is set. Length: ${#OPENAI_API_KEY} characters"
    if [ ! -z "$GITHUB_ACTIONS" ]; then
        echo "Running in GitHub Actions - API key is from GitHub Secrets"
    else
        echo "API injecter? I barely know her!"
    fi
else
    echo "OPENAI_API_KEY is not set"
fi

# Create a config file with the API key if available
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "Adding prompt generation..."
    mkdir -p ./packages/cli/src/config
    cat > ./packages/cli/src/config/api_config.py << EOL
# Auto-generated during build - do not edit
OPENAI_API_KEY = "${OPENAI_API_KEY}"
EOL
else
    echo "Using standard prompts"
    # Ensure empty config exists
    mkdir -p ./packages/cli/src/config
    cat > ./packages/cli/src/config/api_config.py << EOL
# Auto-generated during build - no API key available
OPENAI_API_KEY = None
EOL
fi

# Generate protobuf files
echo "Generating protobuf files..."
python3 -m grpc_tools.protoc -I./protos --python_out=./packages/sdk/src/platform --grpc_python_out=./packages/sdk/src/platform ./protos/*.proto

# Build packages
echo "Building packages..."
python3 -m build

echo "Build complete!"
