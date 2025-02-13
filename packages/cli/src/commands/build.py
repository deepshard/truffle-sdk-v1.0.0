"""
Project Build Command

This module handles the building and packaging of Truffle projects. It provides functionality to:
- Validate project structure and required files
- Package project files into a distributable .truffle archive
- Report build metrics and file sizes
- Ensure proper compression and organization of project assets
"""

import typer
from pathlib import Path
import zipfile
from typing import Optional

from utils.logger import log, Symbols
from templates.validation import (
    validate_main_py,
    validate_manifest,
    validate_requirements
)

def _format_size(size_bytes: int) -> str:
    """Format file size with appropriate units."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"

def _assemble_zip(dir_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Create a zip file from a directory and all its contents.
    
    Args:
        dir_path: Path to the directory to zip
        output_path: Optional custom output path, defaults to dir_name.truffle
        
    Returns:
        Path to the created zip file
        
    Raises:
        NotADirectoryError: If dir_path is not a directory
        FileExistsError: If output_path already exists
    """
    if not dir_path.is_dir():
        raise NotADirectoryError(f"{dir_path} is not a directory")

    # If no output path specified, create zip in parent dir with same name
    if output_path is None:
        output_path = dir_path.parent / f"{dir_path.name}.truffle"

    # Ensure we don't overwrite existing files
    if output_path.exists():
        raise FileExistsError(f"Output path {output_path} already exists")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all files and directories
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                # Calculate relative path for the archive
                rel_path = file_path.relative_to(dir_path)
                # Prepend the directory name to create the correct structure
                arcname = str(Path(dir_path.name) / rel_path)
                zipf.write(file_path, arcname)

    return output_path

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
    with log.group("Building Truffle app", emoji=Symbols.HAMMER):
        log.info("Building Truffle app", version="0.6.5")
        log.detail(f"{Symbols.FOLDER} Source: {project_path}")
        
        try:
            # Validate project structure
            with log.group("Validating project structure", emoji=Symbols.MAGNIFIER):
                main_py = project_path / "main.py"
                manifest_json = project_path / "manifest.json"
                requirements_txt = project_path / "requirements.txt"
                
                log.check("main.py", version="1.0.0")
                log.check("manifest.json", version="1")
                log.check("requirements.txt")
                
                if check_files:
                    if not validate_main_py(main_py):
                        raise ValueError("Invalid main.py file")
                    if not validate_manifest(manifest_json):
                        raise ValueError("Invalid manifest.json file")
                    if not validate_requirements(requirements_txt):
                        raise ValueError("Invalid requirements.txt file")
            
            # Build package
            with log.group("Assembling package", emoji=Symbols.PACKAGE):
                # Calculate sizes and create archive
                orig_size = sum(f.stat().st_size for f in project_path.rglob('*') if f.is_file())
                file_count = len(list(project_path.rglob('*')))
                
                zip_path = _assemble_zip(project_path)
                file_size = zip_path.stat().st_size
                
                log.metric(str(file_count), "files processed")
                log.metric(_format_size(file_size), f"compressed from {_format_size(orig_size)}")
            
            # Success message
            log.success("Build successful!")
            log.detail(f"{Symbols.PACKAGE} Output: {zip_path.name}")
            
        except Exception as e:
            log.error("Build failed", {
                "Error": str(e),
                "Location": str(project_path.absolute())
            })
            raise typer.Exit(1)
