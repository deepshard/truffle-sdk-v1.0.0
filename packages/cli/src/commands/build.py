"""
Project Build Command

This module handles the building and packaging of Truffle projects. It provides functionality to:
- Validate project structure and required files
- Package project files into a distributable .truffle archive
- Output tools to the system's truffle directory
- Report build metrics and file sizes
"""

import typer
from pathlib import Path
import zipfile
import json
from typing import Optional, List
from dataclasses import dataclass

from ..utils.logger import log, Symbols
from ..utils.validation import (
    validate_project_structure,
    validate_main_py,
    validate_manifest_json,
    validate_requirements_txt
)
from ..utils.config import (
    get_sdk_version,
    load_manifest
)

TRUFFLE_DIR = Path.home() / "truffle"

@dataclass
class TruffleFile:
    """Represents a file in a Truffle project."""
    path: Path
    name: str
    relative_path: Path

    @classmethod
    def from_path(cls, file_path: Path, base_dir: Path) -> 'TruffleFile':
        """Create a TruffleFile from a path."""
        return cls(
            path=file_path,
            name=file_path.name,
            relative_path=file_path.relative_to(base_dir)
        )

    def validate(self) -> None:
        """Validate the file exists and is accessible."""
        if not self.path.exists():
            raise ValueError(f"File not found: {self.path}")
        if not self.path.is_file():
            raise ValueError(f"Not a file: {self.path}")
        if not self.path.is_relative_to(self.path.parent):
            raise ValueError(f"Invalid relative path: {self.path}")

def _ensure_truffle_dir() -> Path:
    """
    Ensure the truffle directory exists.
    Creates it if it doesn't exist.
    
    Returns:
        Path to the truffle directory
    """
    if not TRUFFLE_DIR.exists():
        TRUFFLE_DIR.mkdir(parents=True)
        log.detail(f"Created truffle directory at {TRUFFLE_DIR}")
    return TRUFFLE_DIR

def _format_size(size_bytes: int) -> str:
    """Format file size with appropriate units."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"

def _get_tool_name(project_path: Path) -> str:
    """
    Get the tool name from manifest.json.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Tool name from manifest
        
    Raises:
        ValueError: If manifest is invalid or missing name
    """
    manifest_path = project_path / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
        name = manifest.get("name", "").strip().lower()
        if not name:
            raise ValueError("Tool name not found in manifest.json")
        return name
    except Exception as e:
        raise ValueError(f"Failed to read tool name from manifest: {str(e)}")

def _collect_project_files(source_dir: Path) -> List[TruffleFile]:
    """
    Collect all files from the project directory.
    
    Args:
        source_dir: Source directory to scan
        
    Returns:
        List of TruffleFile objects
        
    Raises:
        NotADirectoryError: If source_dir is not a directory
    """
    if not source_dir.is_dir():
        raise NotADirectoryError(f"{source_dir} is not a directory")

    files: List[TruffleFile] = []
    for file_path in source_dir.rglob("*"):
        if file_path.is_file():
            truffle_file = TruffleFile.from_path(file_path, source_dir)
            truffle_file.validate()
            files.append(truffle_file)
    return files

def _assemble_tool(source_dir: Path, output_path: Path) -> None:
    """
    Create a .truffle file from a directory.
    
    Args:
        source_dir: Source directory to package
        output_path: Output path for the .truffle file
        
    Raises:
        NotADirectoryError: If source_dir is not a directory
    """
    # Create parent directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect and validate all files
    project_files = _collect_project_files(source_dir)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in project_files:
            arcname = str(Path(source_dir.name) / file.relative_path)
            zipf.write(file.path, arcname)

def build(
    project_path: Path = typer.Argument(
        ".",
        help="Path to the project directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    check_files: bool = typer.Option(
        True,
        "--check/--no-check",
        help="Whether to validate project files"
    )
) -> None:
    """Build a Truffle project into a distributable package."""
    with log.group("Building Truffle tool", emoji=Symbols.HAMMER):
        log.info("Building Truffle tool", version=get_sdk_version())
        log.detail(f"{Symbols.FOLDER} Source: {project_path}")
        
        try:
            # Validate project structure
            with log.group("Validating project structure", emoji=Symbols.MAGNIFIER):
                if check_files:
                    if not validate_project_structure(project_path):
                        raise ValueError("Invalid project structure")
                        
                    main_py = project_path / "main.py"
                    manifest_json = project_path / "manifest.json"
                    requirements_txt = project_path / "requirements.txt"
                    
                    if not validate_main_py(main_py):
                        raise ValueError("Invalid main.py file - ensure it has a @truffle.tool decorated function/method")
                    if not validate_manifest_json(manifest_json):
                        raise ValueError("Invalid manifest.json file")
                    if not validate_requirements_txt(requirements_txt):
                        raise ValueError("Invalid requirements.txt file")
                    
                    log.check("Project structure validated")
            
            # Get tool name and prepare output path
            tool_name = _get_tool_name(project_path)
            truffle_dir = _ensure_truffle_dir()
            output_path = truffle_dir / f"{tool_name}.truffle"
            
            # Check if tool already exists
            if output_path.exists():
                if not typer.confirm(f"Tool {tool_name} already exists. Overwrite?", default=False):
                    log.warning("Build cancelled", [{
                        "key": "Reason",
                        "value": "Tool already exists"
                    }])
                    raise typer.Exit(1)
                output_path.unlink()
            
            # Build package
            with log.group("Assembling tool package", emoji=Symbols.PACKAGE):
                # Calculate sizes
                orig_size = sum(f.stat().st_size for f in project_path.rglob('*') if f.is_file())
                file_count = len(list(project_path.rglob('*')))
                
                # Create the package
                _assemble_tool(project_path, output_path)
                file_size = output_path.stat().st_size
                
                log.metric(str(file_count), "files processed")
                log.metric(_format_size(file_size), f"compressed from {_format_size(orig_size)}")
            
            # Success message
            log.success("Build successful!")
            log.detail(f"{Symbols.PACKAGE} Tool: {tool_name}")
            log.detail(f"{Symbols.FOLDER} Location: {output_path}")
            
        except Exception as e:
            log.error("Build failed", {
                "Error": str(e),
                "Location": str(project_path.absolute())
            })
            raise typer.Exit(1)
