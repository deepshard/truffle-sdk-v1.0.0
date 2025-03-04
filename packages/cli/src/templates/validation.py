"""
Template Validation

This module provides validation utilities for Truffle project files and structure:
- Validates main.py files for required imports and structure
- Validates manifest.json files for required fields and types
- Validates requirements.txt files for SDK dependencies
- Ensures proper project layout and file organization
"""

import re
import json
from pathlib import Path

def validate_main_py(main_py_file: Path) -> bool:
    """
    Validate a main.py file for a Truffle app.
    
    Args:
        main_py_file: Path to the main.py file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        main_py_text = main_py_file.read_text()
        
        # Check for required imports
        if "import truffle" not in main_py_text:
            return False
            
        # Check for app launch
        if ".launch()" not in main_py_text:
            return False
            
        return True
    except Exception:
        return False

def validate_manifest(manifest_file: Path) -> bool:
    """
    Validate a manifest.json file for a Truffle app.
    
    Args:
        manifest_file: Path to the manifest.json file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        manifest = json.loads(manifest_file.read_text())
        
        # Check required fields
        required_fields = {
            "name",
            "description",
            "example_prompts",
            "manifest_version",
            "app_bundle_id"
        }
        
        if not all(field in manifest for field in required_fields):
            return False
            
        # Validate field types
        if not isinstance(manifest["name"], str):
            return False
        if not isinstance(manifest["description"], str):
            return False
        if not isinstance(manifest["example_prompts"], list):
            return False
            
        return True
    except Exception:
        return False

def validate_requirements(requirements_file: Path) -> bool:
    """
    Validate a requirements.txt file for a Truffle app.
    
    Args:
        requirements_file: Path to the requirements.txt file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        content = requirements_file.read_text()
        lines = [line.strip() for line in content.splitlines()]
        package_lines = [line for line in lines if line and not line.startswith("#")]
        truffle_lines = [line for line in package_lines if line.startswith("truffle")]

        if not truffle_lines:
            return False

        # Check for version specification
        version_pattern = r"truffle\s*(?:[><=!~]=|[><])\s*[\d\.]+"
        for line in truffle_lines:
            if re.match(version_pattern, line):
                return True

        return False
    except Exception:
        return False 