# Truffle CLI Usage

## Create Project
```bash
# Create new project
truffle init my-project

# Create with description
truffle init my-project -d "Project description"

# Create with example prompts
truffle init my-project -e 5
```

## Build Project
```bash
# Build in current directory
truffle build

# Build specific project
truffle build path/to/project

# Build without validation
truffle build --no-check
```

## Run Project
```bash
# Run in current directory
truffle run

# Run with arguments
truffle run -a "argument1" -a "argument2"

# Run specific project
truffle run path/to/project
```

## Project Files

### main.py
```python
import truffle

class MyTool:
    @truffle.tool
    def process(self, text: str) -> str:
        return text.upper()

if __name__ == "__main__":
    app = truffle.TruffleApp(MyTool())
    app.launch()
```

### manifest.json
```json
{
  "name": "my-project",
  "description": "Project description",
  "example_prompts": [
    "Example prompt 1",
    "Example prompt 2"
  ],
  "manifest_version": 1
}
```

### requirements.txt
```
truffle==0.5.3
``` 