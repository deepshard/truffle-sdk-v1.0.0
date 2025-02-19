"""
Project Initialization Command

This module handles the creation of new Truffle projects. It provides functionality to:
- Create new project directories with proper structure
- Generate necessary project files (main.py, manifest.json, requirements.txt)
- Collect and store project metadata and AI-generated example prompts
- Set up initial project configuration and dependencies
"""

import typer
from pathlib import Path
import json
import shutil
import uuid
import os
import requests
from typing import Optional, List

from utils.logger import log, Symbols
from utils.templates import (
    generate_main_py,
    generate_manifest,
    generate_requirements
)

def _generate_example_prompts(tool_name: str, description: str) -> List[str]:
    """Generate example prompts using a simple OpenAI API call."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        log.warning("Sample prompt generation failed - please enter 5 sample prompts inside $manifest.json file")
        return []

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "Reflect on realistic use cases for this tool and generate 5 natural example prompts. Return only the prompts, one per line."
                    },
                    {
                        "role": "user",
                        "content": f"Tool Name: {tool_name}\nDescription: {description}\n\nGenerate 5 example prompts that show how users would naturally interact with this tool."
                    }
                ],
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip().split('\n')[:5]
    except Exception as e:
        log.warning("Sample prompt generation failed - please enter 5 sample prompts inside $manifest.json file")
        return []

def init(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    description: Optional[str] = typer.Option(
        None,
        "--description", "-d",
        help="Description of the project"
    )
) -> None:
    """Initialize a new Truffle project."""
    with log.group("Initializing new Truffle project", emoji=Symbols.PACKAGE):
        log.info("Creating new Truffle project", version="0.6.5")
        
        # Validate and format project name
        if project_name == ".":
            project_name = Path(project_name).absolute().name
            if not typer.confirm(f"Project Name: {project_name}", default=True):
                project_name = typer.prompt("Enter Project Name")
        
        # Capitalize first letter
        project_name = str(project_name)[0].upper() + str(project_name)[1:]
        proj_path = Path(project_name)
        
        # Check if project exists
        if proj_path.exists():
            log.error("Project already exists", {
                "name": project_name,
                "path": str(proj_path)
            })
            raise typer.Exit(1)

        # Get project details
        log.prompt("Project Name", project_name)
        if not description:
            description = typer.prompt("Description")
        
        # Generate example prompts
        log.info("Generating sample prompts", emoji=Symbols.SPARKLES)
        example_prompts = _generate_example_prompts(project_name, description)

        # Generate manifest
        manifest_data = {
            "name": project_name.lower(),
            "description": description,
            "example_prompts": example_prompts,
            "packages": [],
            "manifest_version": 1,
            "app_bundle_id": str(uuid.uuid4())
        }
        
        # Create project structure
        with log.group("Creating project structure", emoji=Symbols.SPARKLES):
            proj_path.mkdir()
            
            # Log file creation before actually creating them
            for file in ["main.py", "manifest.json", "requirements.txt", "icon.png"]:
                log.created_file(file)
            
            # Create files
            (proj_path / "main.py").write_text(
                generate_main_py(project_name, manifest_data)
            )
            (proj_path / "manifest.json").write_text(
                json.dumps(manifest_data, indent=4, sort_keys=True, ensure_ascii=False)
            )
            (proj_path / "requirements.txt").write_text(
                generate_requirements("0.6.5")
            )
            
            # Copy icon
            icon_src = Path(__file__).parent.parent / "cli_assets" / "default_app.png"
            shutil.copy(icon_src, proj_path / "icon.png")
            
            # Success message
            log.success("Project initialized successfully!")
            log.detail(f"{Symbols.FOLDER} Location: ./{project_name}")
            log.detail(f"{Symbols.WRENCH} Run 'truffle build' to package your app")
