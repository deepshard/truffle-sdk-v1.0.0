"""
Project Template Utilities

This module provides template generation utilities for Truffle projects:
- Generates project file templates (main.py, manifest.json)
- Handles template variable substitution
- Manages project asset copying and organization
- Provides default project templates and resources
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import get_sdk_version

def generate_main_py(project_name: str, manifest: Dict[str, Any]) -> str:
    """
    Generate main.py content from template.
    
    Args:
        project_name: Name of the project
        manifest: Project manifest data
        
    Returns:
        Generated main.py content
    """
    return f"""
import truffle

class {project_name}:
    def __init__(self):
        self.client = truffle.TruffleClient()
    
    # All tool calls must start with a capital letter! 
    @truffle.tool(
        description="Replace this with a description of the tool.",
        icon="brain"
    )
    @truffle.args(user_input="A description of the argument")
    def {project_name}Tool(self, user_input: str) -> str:
        \"\"\"
        Replace this text with a basic description of what this function does.
        \"\"\"
        # Implement your tool logic here
        pass

if __name__ == "__main__":
    app = truffle.TruffleApp({project_name}())
    app.launch()
"""

def generate_manifest(
    name: str,
    description: str,
    example_prompts: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate manifest.json content.
    
    Args:
        name: Project name
        description: Project description
        example_prompts: List of example prompts
        
    Returns:
        Generated manifest data
    """
    if example_prompts is None:
        example_prompts = [
            "How do I fetch a website?",
            "Can you process this JSON?"
        ]
        
    return {
        "name": name.lower(),
        "description": description,
        "example_prompts": example_prompts,
        "packages": [],
        "manifest_version": 1
    }

def generate_requirements(sdk_version: Optional[str] = None) -> str:
    """
    Generate requirements.txt content.
    
    Args:
        sdk_version: Optional SDK version, defaults to current
        
    Returns:
        Generated requirements.txt content
    """
    if sdk_version is None:
        sdk_version = get_sdk_version()
        
    return f"truffle=={sdk_version}"

def copy_project_template(
    template_name: str,
    target_path: Path,
    variables: Dict[str, Any]
) -> None:
    """
    Copy and customize a project template.
    
    Args:
        template_name: Name of the template to use
        target_path: Path to copy to
        variables: Template variables
        
    Raises:
        FileNotFoundError: If template doesn't exist
    """
    template_path = Path(__file__).parent.parent / "templates" / template_name
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")
        
    # Copy template files
    shutil.copytree(template_path, target_path)
    
    # Update files with variables
    for file in target_path.rglob("*"):
        if file.is_file() and file.suffix in [".py", ".json", ".txt", ".md"]:
            content = file.read_text()
            for key, value in variables.items():
                content = content.replace(f"{{{{ {key} }}}}", str(value))
            file.write_text(content)

def copy_default_icon(target_path: Path) -> None:
    """
    Copy default app icon to project.
    
    Args:
        target_path: Path to copy icon to
    """
    icon_src = Path(__file__).parent.parent / "assets" / "default_app.png"
    shutil.copy(icon_src, target_path / "icon.png")
