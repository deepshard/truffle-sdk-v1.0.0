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
            log.error("Oops! The project folder seems to be missing. Try running the command again!", {
                "path": str(project_path)
            })
            return False
            
        if not project_path.is_dir():
            log.error("Hmm, that's not a folder. Please specify a valid project folder!", {
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
                log.error(f"Looks like {file} is missing! Your project might be corrupted - try initializing it again.", {
                    "file": file,
                    "path": str(file_path)
                })
                return False
                
            if not file_path.is_file():
                log.error(f"There's something wrong with {file}. Try initializing your project again!", {
                    "file": file,
                    "path": str(file_path)
                })
                return False
                
        return True
        
    except Exception as e:
        log.error("Something went wrong while checking your project structure. Try again!", {
            "error": str(e)
        })
        return False

def validate_manifest_json(manifest_path: Path) -> bool:
    """
    Validate manifest.json file.
    
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
                log.error(f"Your manifest.json is missing the {field} field. Try initializing your project again!", {
                    "field": field
                })
                return False
                
            if not isinstance(manifest[field], field_type):
                log.error(f"The {field} field in manifest.json looks wrong. Try initializing your project again!", {
                    "field": field,
                    "expected": field_type.__name__,
                    "got": type(manifest[field]).__name__
                })
                return False
                
        # Validate values
        if not manifest["name"]:
            log.error("Your project needs a name in manifest.json!")
            return False
            
        if not manifest["description"]:
            log.error("Don't forget to add a description in manifest.json!")
            return False
            
        if not manifest["example_prompts"]:
            log.error("Your manifest.json needs some example prompts!")
            return False
            
        return True
        
    except json.JSONDecodeError as e:
        log.error("Your manifest.json file seems corrupted. Try initializing your project again!", {
            "error": str(e)
        })
        return False
    except Exception as e:
        log.error("Something went wrong with manifest.json. Try initializing your project again!", {
            "error": str(e)
        })
        return False

def validate_main_py(main_py_path: Path) -> bool:
    """
    Validate main.py file.
    
    Args:
        main_py_path: Path to main.py
        
    Returns:
        True if valid, False otherwise
    """
    try:
        content = main_py_path.read_text()
        
        # Check basic imports
        if "import truffle" not in content:
            log.error("Don't forget to import truffle in your main.py!")
            return False
            
        if ".launch()" not in content:
            log.error("Your main.py needs to call .launch() to start your tool!")
            return False
            
        # Parse and validate AST
        tree = ast.parse(content)
        visitor = ToolVisitor()
        visitor.visit(tree)
        
        if not visitor.has_tool_method:
            log.error("Looks like you haven't created your tool yet! Add a function with @truffle.tool decorator.")
            return False
            
        if not visitor.has_launch_call:
            log.error("Don't forget to launch your app with app.launch()!")
            return False
            
        return True
        
    except SyntaxError as e:
        log.error("There's a syntax error in your main.py. Check your code!", {
            "error": str(e)
        })
        return False
    except Exception as e:
        log.error("Something's wrong with your main.py. Try initializing your project again!", {
            "error": str(e)
        })
        return False

class ToolVisitor(ast.NodeVisitor):
    """AST visitor for validating Truffle tool structure."""
    
    def __init__(self):
        self.has_tool_method = False
        self.has_launch_call = False
        self.tool_methods: Set[str] = set()

    def _check_truffle_decorator(self, decorator: ast.AST, attr_name: str) -> bool:
        """Check if a decorator is a truffle.{attr_name} decorator."""
        if isinstance(decorator, ast.Call):
            # Handle @truffle.tool() or @truffle.args() with arguments
            return (
                isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "truffle"
                and decorator.func.attr == attr_name
            )
        elif isinstance(decorator, ast.Attribute):
            # Handle @truffle.tool or @truffle.args without arguments
            return (
                isinstance(decorator.value, ast.Name)
                and decorator.value.id == "truffle"
                and decorator.attr == attr_name
            )
        return False

    def _validate_tool_decorators(self, decorators: List[ast.AST]) -> bool:
        """Validate that a function/method has the required truffle decorators."""
        has_tool = False
        has_args = False
        
        for decorator in decorators:
            if self._check_truffle_decorator(decorator, "tool"):
                has_tool = True
            elif self._check_truffle_decorator(decorator, "args"):
                has_args = True
                
        return has_tool  # args decorator is optional

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        if self._validate_tool_decorators(node.decorator_list):
            self.has_tool_method = True
            self.tool_methods.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        # Visit class body for methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if self._validate_tool_decorators(item.decorator_list):
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
