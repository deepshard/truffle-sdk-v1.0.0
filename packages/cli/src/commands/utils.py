"""
CLI Utilities Module

This module provides common utilities for CLI commands, including:
- Project configuration management
- File validation and verification
- Package requirement handling
- Project structure validation
"""

import ast
import re
import tomli
import tomli_w
from pathlib import Path
from typing import Optional

from utils.logger import log

def update_pyproject(
    pyproject_path: Path,
    new_name: Optional[str] = None,
    new_description: Optional[str] = None,
) -> None:
    """
    Update the project name and description in pyproject.toml.
    
    Args:
        pyproject_path: Path to pyproject.toml
        new_name: New name for the project
        new_description: New description for the project
        
    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
        KeyError: If project table is missing
    """
    if not pyproject_path.exists():
        raise FileNotFoundError(f"No pyproject.toml found in {pyproject_path.parent}")

    # Read existing toml
    with pyproject_path.open("rb") as f:
        pyproject = tomli.load(f)

    if "project" not in pyproject:
        raise KeyError("No [project] table found in pyproject.toml")

    # Update values if provided
    if new_name is not None:
        pyproject["project"]["name"] = new_name

    if new_description is not None:
        pyproject["project"]["description"] = new_description

    # Write updated toml
    with pyproject_path.open("wb") as f:
        tomli_w.dump(pyproject, f)

def validate_requirements_txt(requirements_file: Path) -> bool:
    """
    Validate requirements.txt file structure and content.
    
    Args:
        requirements_file: Path to requirements.txt
        
    Returns:
        True if valid, False otherwise
    """
    try:
        content = requirements_file.read_text()
        lines = [line.strip() for line in content.splitlines()]
        package_lines = [line for line in lines if line and not line.startswith("#")]
        truffle_lines = [line for line in package_lines if line.startswith("truffle")]

        if not truffle_lines:
            log.error("Invalid requirements.txt", {
                "reason": "truffle package not found"
            })
            return False

        version_pattern = r"truffle\s*(?:[><=!~]=|[><])\s*[\d\.]+"
        for line in truffle_lines:
            if re.match(version_pattern, line):
                return True

        log.error("Invalid requirements.txt", {
            "reason": "SDK version not specified"
        })
        return False

    except (FileNotFoundError, PermissionError) as e:
        log.error("Requirements file error", {
            "error": str(e)
        })
        return False

def validate_main_py(main_py_file: Path) -> bool:
    """
    Validate main.py file structure and content.
    
    Args:
        main_py_file: Path to main.py
        
    Returns:
        True if valid, False otherwise
    """
    try:
        main_py_text = main_py_file.read_text()
        
        # Check imports
        if "import truffle" not in main_py_text:
            log.error("Invalid main.py file", {
                "reason": "Missing truffle import"
            })
            return False
            
        # Check launch call
        if ".launch()" not in main_py_text:
            log.error("Invalid main.py file", {
                "reason": "Missing .launch() call"
            })
            return False
            
        # Parse AST to validate structure
        tree = ast.parse(main_py_text)
        visitor = MethodVisitor()
        visitor.visit(tree)
        
        if not visitor.has_valid_tool:
            log.error("Invalid main.py file", {
                "reason": "No valid tool class found"
            })
            return False
            
        return True
        
    except Exception as e:
        log.error("Failed to validate main.py", {
            "error": str(e)
        })
        return False

class MethodVisitor(ast.NodeVisitor):
    """AST visitor that validates tool class structure."""
    
    def __init__(self):
        self.has_valid_tool = False
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition and validate structure."""
        has_tool_method = False
        has_launch_call = False
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        if (
                            isinstance(decorator.value, ast.Name)
                            and decorator.value.id == "truffle"
                            and decorator.attr == "tool"
                        ):
                            has_tool_method = True
                            
            elif isinstance(item, ast.Expr):
                if isinstance(item.value, ast.Call):
                    if isinstance(item.value.func, ast.Attribute):
                        if item.value.func.attr == "launch":
                            has_launch_call = True
                            
        self.has_valid_tool = has_tool_method and has_launch_call
