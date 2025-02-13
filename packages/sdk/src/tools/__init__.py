"""
Tools Package

Core implementation of the Truffle tool system:

Features:
- Tool decorators for function wrapping
- Argument specification and validation
- Tool registry and discovery
- Type-safe interfaces
"""

from .decorators import tool, args, ToolConfig
from .registry import ToolRegistry

# Create default registry instance
registry = ToolRegistry()

# Public exports
__all__ = [
    # Decorators
    "tool",
    "args",
    
    # Registry
    "ToolRegistry",
    "registry",
    
    # Types
    "ToolConfig",
]
