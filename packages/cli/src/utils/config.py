"""
Configuration Utilities Module

This module provides configuration management utilities for the Truffle CLI:
- Handles manifest.json file operations and validation
- Manages pyproject.toml configuration
- Processes requirements.txt dependencies
- Provides version management utilities
"""

import json
import re
import tomli
import tomli_w
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from .logger import log

# Constants
DEFAULT_VERSION = "0.6.5"
MANIFEST_VERSION = 1

def get_sdk_version() -> str:
    """Get the current SDK version."""
    return DEFAULT_VERSION

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load and validate manifest.json.
    
    Args:
        manifest_path: Path to manifest.json
        
    Returns:
        Parsed manifest data
        
    Raises:
        FileNotFoundError: If manifest doesn't exist
        ValueError: If manifest is invalid
    """
    try:
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest.json not found at {manifest_path}")
            
        manifest = json.loads(manifest_path.read_text())
        
        # Validate required fields
        required_fields = [
            "name",
            "description",
            "example_prompts",
            "manifest_version",
            "app_bundle_id"
        ]
        
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field in manifest: {field}")
                
        # Validate types
        if not isinstance(manifest["name"], str):
            raise ValueError("manifest.name must be a string")
            
        if not isinstance(manifest["description"], str):
            raise ValueError("manifest.description must be a string")
            
        if not isinstance(manifest["example_prompts"], list):
            raise ValueError("manifest.example_prompts must be a list")
            
        if not isinstance(manifest["manifest_version"], int):
            raise ValueError("manifest.manifest_version must be an integer")
            
        return manifest
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to load manifest: {str(e)}")

def update_manifest(
    manifest_path: Path,
    updates: Dict[str, Any],
    create: bool = False
) -> None:
    """
    Update or create manifest.json.
    
    Args:
        manifest_path: Path to manifest.json
        updates: Values to update
        create: Whether to create if missing
        
    Raises:
        FileNotFoundError: If manifest doesn't exist and create=False
        ValueError: If manifest becomes invalid
    """
    try:
        if manifest_path.exists():
            manifest = load_manifest(manifest_path)
        elif create:
            manifest = {
                "name": "",
                "description": "",
                "example_prompts": [],
                "manifest_version": MANIFEST_VERSION,
                "app_bundle_id": str(uuid.uuid4()),
                "packages": []
            }
        else:
            raise FileNotFoundError(f"manifest.json not found at {manifest_path}")
            
        # Update values
        manifest.update(updates)
        
        # Validate updated manifest
        if not manifest["name"]:
            raise ValueError("manifest.name cannot be empty")
            
        if not manifest["description"]:
            raise ValueError("manifest.description cannot be empty")
            
        # Write back
        manifest_path.write_text(
            json.dumps(manifest, indent=4, sort_keys=True, ensure_ascii=False)
        )
        
    except Exception as e:
        raise ValueError(f"Failed to update manifest: {str(e)}")

def load_pyproject(pyproject_path: Path) -> Dict[str, Any]:
    """
    Load and validate pyproject.toml.
    
    Args:
        pyproject_path: Path to pyproject.toml
        
    Returns:
        Parsed TOML data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If TOML is invalid
    """
    try:
        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
            
        with pyproject_path.open("rb") as f:
            pyproject = tomli.load(f)
            
        # Validate project table
        if "project" not in pyproject:
            raise ValueError("Missing [project] table in pyproject.toml")
            
        return pyproject
        
    except Exception as e:
        raise ValueError(f"Failed to load pyproject.toml: {str(e)}")

def update_pyproject(
    pyproject_path: Path,
    updates: Dict[str, Any],
    create: bool = False
) -> None:
    """
    Update or create pyproject.toml.
    
    Args:
        pyproject_path: Path to pyproject.toml
        updates: Values to update in [project] table
        create: Whether to create if missing
        
    Raises:
        FileNotFoundError: If file doesn't exist and create=False
        ValueError: If TOML becomes invalid
    """
    try:
        if pyproject_path.exists():
            pyproject = load_pyproject(pyproject_path)
        elif create:
            pyproject = {"project": {}}
        else:
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
            
        # Update project table
        if "project" not in pyproject:
            pyproject["project"] = {}
            
        pyproject["project"].update(updates)
        
        # Write back
        with pyproject_path.open("wb") as f:
            tomli_w.dump(pyproject, f)
            
    except Exception as e:
        raise ValueError(f"Failed to update pyproject.toml: {str(e)}")

def format_requirements(
    packages: Dict[str, str],
    include_versions: bool = True
) -> str:
    """
    Format requirements.txt content.
    
    Args:
        packages: Package names and versions
        include_versions: Whether to include version specs
        
    Returns:
        Formatted requirements string
    """
    lines = []
    for package, version in sorted(packages.items()):
        if include_versions and version:
            if not re.match(r"^[0-9]", version):
                version = f"=={version}"
            lines.append(f"{package}{version}")
        else:
            lines.append(package)
    return "\n".join(lines)

def validate_version_spec(version: str) -> bool:
    """
    Validate version specification string.
    
    Args:
        version: Version string to validate
        
    Returns:
        True if valid, False otherwise
    """
    version_pattern = r"^(?:[><=!~]=|[><])\s*[\d\.]+$"
    return bool(re.match(version_pattern, version))
