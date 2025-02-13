"""
Project Initialization Command

This module handles the creation of new Truffle projects. It provides functionality to:
- Create new project directories with proper structure
- Generate necessary project files (main.py, manifest.json, requirements.txt)
- Collect and store project metadata and example prompts
- Set up initial project configuration and dependencies
"""

import typer
from pathlib import Path
import json
import shutil
import uuid
from typing import Optional, List

from utils.logger import log, Symbols
from templates.generator import (
    generate_main_py,
    generate_manifest,
    generate_requirements
)

def init(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    description: Optional[str] = typer.Option(
        None,
        "--description", "-d",
        help="Description of the project"
    ),
    num_examples: int = typer.Option(
        5,
        "--examples", "-e",
        help="Number of example prompts to collect"
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
        
        # Collect example prompts
        with log.group("Input sample prompts", emoji=Symbols.PENCIL):
            example_prompts = []
            for i in range(num_examples):
                prompt = typer.prompt(f"Enter example prompt {i + 1}/{num_examples}")
                example_prompts.append(prompt)
                log.detail(f"{i + 1}. \"{prompt}\"")

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
