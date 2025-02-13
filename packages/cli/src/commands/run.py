"""
Project Run Command

This module handles the execution of Truffle projects. It provides functionality to:
- Load and validate Truffle tool classes
- Set up runtime environments for tools
- Execute tools with optional arguments
- Handle execution errors and logging
"""

import typer
from pathlib import Path
import sys
import ast
import importlib.util
from typing import Optional, List

from utils.logger import log, Symbols
from templates.validation import validate_main_py

class MethodVisitor(ast.NodeVisitor):
    """AST visitor that finds methods decorated with 'truffle.tool'"""
    
    def __init__(self):
        self.exposed_methods: List[str] = []
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition and check its methods."""
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        if (
                            isinstance(decorator.value, ast.Name)
                            and decorator.value.id == "truffle"
                            and decorator.attr == "tool"
                        ):
                            self.exposed_methods.append(item.name)
                    elif (
                        isinstance(decorator, ast.Name)
                        and decorator.id == "expose_tool"
                    ):
                        self.exposed_methods.append(item.name)

def _validate_tool_class(main_py: Path) -> bool:
    """
    Validate that the tool class has proper Truffle decorators.
    """
    try:
        tree = ast.parse(main_py.read_text())
        visitor = MethodVisitor()
        visitor.visit(tree)
        return len(visitor.exposed_methods) > 0
    except Exception:
        return False

def _import_tool(main_py: Path) -> any:
    """
    Import a tool from a main.py file.
    
    Args:
        main_py: Path to the main.py file
        
    Returns:
        The imported tool class
        
    Raises:
        ImportError: If the tool cannot be imported
        AttributeError: If the tool class is not found
    """
    if not main_py.exists():
        raise ImportError(f"File not found: {main_py}")
        
    # Add project directory to path
    sys.path.insert(0, str(main_py.parent))
    
    try:
        # Import the module
        spec = importlib.util.spec_from_file_location("main", main_py)
        if not spec or not spec.loader:
            raise ImportError("Failed to load module specification")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the tool class
        tool_class = None
        for attr in dir(module):
            if attr.lower().endswith("tool"):
                tool_class = getattr(module, attr)
                break
                
        if not tool_class:
            raise AttributeError("No tool class found in main.py")
            
        return tool_class
        
    finally:
        # Remove project directory from path
        sys.path.pop(0)

def run(
    project_path: Path = typer.Argument(
        ".",
        help="Path to the project directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    args: Optional[List[str]] = typer.Option(
        None,
        "--arg", "-a",
        help="Arguments to pass to the tool"
    )
) -> None:
    """Run a Truffle project."""
    with log.group("Running Truffle app", emoji=Symbols.HAMMER):
        log.info("Running Truffle app", version="0.6.5")
        log.detail(f"{Symbols.FOLDER} Source: {project_path}")
        
        try:
            # Validate project
            main_py = project_path / "main.py"
            if not validate_main_py(main_py):
                raise ValueError("Invalid main.py file")
                
            # Validate tool class
            if not _validate_tool_class(main_py):
                raise ValueError("No valid Truffle tool found in main.py")
                
            # Import tool
            with log.group("Loading tool", emoji=Symbols.MAGNIFIER):
                tool_class = _import_tool(main_py)
                log.check("main.py", version="1.0.0")
            
            # Initialize tool
            with log.group("Initializing tool", emoji=Symbols.WRENCH):
                tool = tool_class()
                log.detail(f"{Symbols.ARROW} Tool class: {tool_class.__name__}")
            
            # Run tool
            with log.group("Running tool", emoji=Symbols.SPARKLES):
                if args:
                    log.detail(f"{Symbols.ARROW} Arguments:", dim_suffix=" ".join(args))
                    tool.run(*args)
                else:
                    tool.run()
                
            # Success message
            log.success("Tool execution completed!")
            
        except Exception as e:
            log.error("Tool execution failed", {
                "Error": str(e),
                "Location": str(project_path.absolute())
            })
            raise typer.Exit(1)
