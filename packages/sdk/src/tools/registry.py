"""
Tool Registry Module

Core implementation of the Truffle tool registry system, providing:

Features:
- Tool registration and discovery
- Metadata management
- Type validation
- Error handling
"""

import inspect
import typing
from pathlib import Path
import importlib.util

from ..types.models import ToolMetadata
from ..client.exceptions import ValidationError
from .decorators import ToolConfig

class ToolRegistry:
    """Registry for managing and discovering Truffle tools."""
    
    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: typing.Dict[str, typing.Callable] = {}
        self._metadata: typing.Dict[str, ToolMetadata] = {}

    def register(
        self,
        func: typing.Callable,
        name: str = None,
        description: str = None,
        icon: str = None,
    ) -> None:
        """
        Register a function as a tool.
        
        Args:
            func: The function to register
            name: Optional name override
            description: Optional description override
            icon: Optional icon override
        """
        # Validate function is a tool
        if not hasattr(func, "__truffle_tool__"):
            raise ValidationError(
                f"Function {func.__name__} must be decorated with @tool"
            )
        
        # Get tool configuration
        config: ToolConfig = func.__truffle_tool__
        
        # Create tool metadata
        tool_name = name or config.name
        tool_desc = description or config.description
        tool_icon = icon or config.icon
        
        # Validate name uniqueness
        if tool_name in self._tools:
            raise ValidationError(f"Tool {tool_name} is already registered")
        
        # Store tool and metadata
        self._tools[tool_name] = func
        self._metadata[tool_name] = ToolMetadata(
            name=tool_name,
            description=tool_desc,
            icon=tool_icon,
            args=config.args,
        )

    def get_tool(self, name: str) -> typing.Tuple[typing.Callable, ToolMetadata]:
        """
        Get a tool and its metadata by name.
        
        Args:
            name: The name of the tool to get
            
        Returns:
            Tuple of (tool_function, tool_metadata)
        """
        if name not in self._tools:
            raise ValidationError(f"Tool {name} not found")
        return self._tools[name], self._metadata[name]

    def list_tools(self) -> typing.List[ToolMetadata]:
        """Get metadata for all registered tools."""
        return list(self._metadata.values())

    def discover_tools(self, directory: typing.Union[str, Path]) -> None:
        """
        Discover and register tools from Python files in a directory.
        
        Args:
            directory: Directory path to scan for tools
        """
        directory = Path(directory)
        if not directory.exists():
            raise ValidationError(f"Directory {directory} does not exist")
        
        # Scan for Python files
        for file in directory.rglob("*.py"):
            # Import module
            spec = importlib.util.spec_from_file_location(
                file.stem, str(file)
            )
            if spec is None or spec.loader is None:
                continue
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find tool functions
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isfunction(obj) and
                    hasattr(obj, "__truffle_tool__")
                ):
                    self.register(obj)
