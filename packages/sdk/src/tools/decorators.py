"""
Tool Decorators Module

This module provides decorators for defining and configuring Truffle tools:

Core Features:
- @tool decorator for configuring tool name, description, and icon
- @args decorator for specifying argument descriptions
- Type validation and safety checks
- Function metadata handling
"""

import functools
import inspect
import typing
from dataclasses import dataclass

from ..types.models import TruffleReturnType, ToolMetadata
from ..client.exceptions import ValidationError

@dataclass
class ToolConfig:
    """Configuration for a tool function."""
    name: str
    description: str
    icon: typing.Optional[str] = None
    args: typing.Dict[str, str] = None

def tool(
    name: str = None,
    description: str = None,
    icon: str = None,
) -> typing.Callable:
    """
    Decorator to register a function as a Truffle tool.
    
    Args:
        name: Optional name for the tool (defaults to function name)
        description: Optional description of what the tool does
        icon: Optional icon URL or emoji for the tool
    """
    def decorator(func: typing.Callable) -> typing.Callable:
        # Get function signature and docstring
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        
        # Create tool metadata
        tool_name = name or func.__name__
        tool_desc = description or doc.split("\n")[0]
        
        # Validate return type annotation
        return_type = sig.return_annotation
        if return_type is inspect.Signature.empty:
            raise ValidationError(f"Tool {tool_name} must have a return type annotation")
        if not (
            isinstance(return_type, type) and 
            issubclass(return_type, TruffleReturnType)
        ):
            raise ValidationError(
                f"Tool {tool_name} must return a TruffleReturnType, got {return_type}"
            )

        # Store tool configuration
        func.__truffle_tool__ = ToolConfig(
            name=tool_name,
            description=tool_desc,
            icon=icon,
            args={},
        )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def args(**arg_descriptions: str) -> typing.Callable:
    """
    Decorator to add argument descriptions to a tool function.
    
    Args:
        **arg_descriptions: Mapping of argument names to their descriptions
    """
    def decorator(func: typing.Callable) -> typing.Callable:
        # Validate function is a tool
        if not hasattr(func, "__truffle_tool__"):
            raise ValidationError(
                f"@args can only be used on functions decorated with @tool"
            )
        
        # Get function signature
        sig = inspect.signature(func)
        
        # Validate all described args exist
        for arg_name in arg_descriptions:
            if arg_name not in sig.parameters:
                raise ValidationError(
                    f"Argument '{arg_name}' described but not found in function signature"
                )
        
        # Store argument descriptions
        func.__truffle_tool__.args.update(arg_descriptions)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
