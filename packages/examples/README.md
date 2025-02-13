# Truffle SDK Examples

Simple examples demonstrating basic tool creation.

## Examples

### Hello World
Simple "Hello World" tool demonstrating basic tool creation.
```python
import truffle

@truffle.tool(description="Says hello")
def hello(name: str) -> str:
    return f"Hello, {name}!"
```

### Text Tool
Basic text processing tool with arguments.
```python
import truffle

@truffle.tool(description="Process text")
@truffle.args(
    text="The text to process",
    uppercase="Convert to uppercase"
)
def process_text(text: str, uppercase: bool = False) -> str:
    if uppercase:
        return text.upper()
    return text
```