"""
Validation Utilities Module

This module provides core validation utilities for the Truffle CLI:
- Project structure and file validation
- Tool class and method validation
- Import and dependency checking
- Error handling and reporting
"""

import ast
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

from .logger import log

def validate_project_structure(project_path: Path) -> bool:
    """
    Validate the basic structure of a Truffle project.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check directory exists
        if not project_path.exists():
            log.error("Project directory not found", {
                "path": str(project_path)
            })
            return False
            
        if not project_path.is_dir():
            log.error("Path is not a directory", {
                "path": str(project_path)
            })
            return False
            
        # Check required files
        required_files = [
            "main.py",
            "manifest.json",
            "requirements.txt",
            "icon.png"
        ]
        
        for file in required_files:
            file_path = project_path / file
            if not file_path.exists():
                log.error("Missing required file", {
                    "file": file,
                    "path": str(file_path)
                })
                return False
                
            if not file_path.is_file():
                log.error("Invalid file type", {
                    "file": file,
                    "path": str(file_path)
                })
                return False
                
        return True
        
    except Exception as e:
        log.error("Failed to validate project structure", {
            "error": str(e)
        })
        return False

def validate_manifest_json(manifest_path: Path) -> bool:
    """
    Validate manifest.json file.
    Verified against deprecated version's manifest validation.
    
    Args:
        manifest_path: Path to manifest.json
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Load and parse JSON
        manifest = json.loads(manifest_path.read_text())
        
        # Check required fields
        required_fields = {
            "name": str,
            "description": str,
            "example_prompts": list,
            "manifest_version": int,
            "app_bundle_id": str
        }
        
        for field, field_type in required_fields.items():
            if field not in manifest:
                log.error("Missing required field", {
                    "field": field
                })
                return False
                
            if not isinstance(manifest[field], field_type):
                log.error("Invalid field type", {
                    "field": field,
                    "expected": field_type.__name__,
                    "got": type(manifest[field]).__name__
                })
                return False
                
        # Validate values
        if not manifest["name"]:
            log.error("Empty project name")
            return False
            
        if not manifest["description"]:
            log.error("Empty project description")
            return False
            
        if not manifest["example_prompts"]:
            log.error("No example prompts provided")
            return False
            
        return True
        
    except json.JSONDecodeError as e:
        log.error("Invalid JSON in manifest", {
            "error": str(e)
        })
        return False
    except Exception as e:
        log.error("Failed to validate manifest", {
            "error": str(e)
        })
        return False

def validate_main_py(main_py_path: Path) -> bool:
    """
    Validate main.py file.
    Verified against deprecated version's Python validation.
    
    Args:
        main_py_path: Path to main.py
        
    Returns:
        True if valid, False otherwise
    """
    try:
        content = main_py_path.read_text()
        
        # Check basic imports
        if "import truffle" not in content:
            log.error("Missing truffle import")
            return False
            
        if ".launch()" not in content:
            log.error("Missing .launch() call")
            return False
            
        # Parse and validate AST
        tree = ast.parse(content)
        visitor = ToolVisitor()
        visitor.visit(tree)
        
        if not visitor.has_tool_class:
            log.error("No tool class found")
            return False
            
        if not visitor.has_tool_method:
            log.error("No @truffle.tool methods found")
            return False
            
        if not visitor.has_launch_call:
            log.error("No app.launch() call found")
            return False
            
        return True
        
    except SyntaxError as e:
        log.error("Invalid Python syntax", {
            "error": str(e)
        })
        return False
    except Exception as e:
        log.error("Failed to validate main.py", {
            "error": str(e)
        })
        return False

class ToolVisitor(ast.NodeVisitor):
    """AST visitor for validating Truffle tool structure."""
    
    def __init__(self):
        self.has_tool_class = False
        self.has_tool_method = False
        self.has_launch_call = False
        self.tool_methods: Set[str] = set()
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        # Check if this is a tool class
        if node.name.endswith("Tool"):
            self.has_tool_class = True
            
        # Visit class body
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        if (
                            isinstance(decorator.value, ast.Name)
                            and decorator.value.id == "truffle"
                            and decorator.attr == "tool"
                        ):
                            self.has_tool_method = True
                            self.tool_methods.add(item.name)
                            
    def visit_Expr(self, node: ast.Expr) -> None:
        """Visit expression."""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                if node.value.func.attr == "launch":
                    self.has_launch_call = True

def validate_requirements_txt(requirements_path: Path) -> bool:
    """
    Validate requirements.txt file.
    Verified against deprecated version's requirements validation.
    
    Args:
        requirements_path: Path to requirements.txt
        
    Returns:
        True if valid, False otherwise
    """
    try:
        content = requirements_path.read_text()
        lines = [line.strip() for line in content.splitlines()]
        package_lines = [line for line in lines if line and not line.startswith("#")]
        
        # Check for truffle package
        truffle_lines = [line for line in package_lines if line.startswith("truffle")]
        if not truffle_lines:
            log.error("truffle package not found")
            return False
            
        # Check version specification
        version_pattern = r"truffle\s*(?:[><=!~]=|[><])\s*[\d\.]+"
        for line in truffle_lines:
            if re.match(version_pattern, line):
                return True
                
        log.error("truffle package version not specified")
        return False
        
    except Exception as e:
        log.error("Failed to validate requirements.txt", {
            "error": str(e)
        })
        return False
