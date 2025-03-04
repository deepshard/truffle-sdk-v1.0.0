# Truffle SDK Usage

## Client
```python
from truffle import GRPCClient

# Initialize client
client = GRPCClient()

# Generate text
response = client.generate("Your prompt", model="gpt-4")

# Get available models
models = client.get_models()

# Embed text
embeddings = client.query_embed("query", ["doc1", "doc2"])

# Ask user
result = client.ask_user("Please provide input")
```

## Tool Creation
```python
from truffle import tool

# Basic tool
@tool
def my_tool(text: str) -> str:
    return text.upper()

# Tool with description and icon
@tool(description="Process text", icon="✨")
def process(text: str) -> str:
    return text.upper()

# Tool with type validation
@tool
def add_numbers(a: int, b: int) -> int:
    return a + b
```

## Request/Response Types
```python
from truffle.types import (
    GenerateRequest,
    SystemToolRequest,
    UserRequest,
    EmbedRequest
)

# Generation request
req = GenerateRequest(
    prompt="Hello",
    model="gpt-4",
    max_tokens=100
)

# System tool request
tool_req = SystemToolRequest(
    tool_name="my_tool",
    args={"text": "hello"}
)

# User interaction
user_req = UserRequest(
    prompt="Enter value",
    timeout=30
)

# Embedding request
embed_req = EmbedRequest(
    text=["doc1", "doc2"],
    model="text-embedding-ada-002"
) 