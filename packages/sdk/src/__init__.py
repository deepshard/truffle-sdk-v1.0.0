"""
Truffle SDK

Core SDK implementation for the Truffle platform.

PROPRIETARY CODE - DO NOT DISTRIBUTE
This package contains proprietary implementation details.
Unauthorized copying, modification, distribution, or use of this code is strictly prohibited.

Features:
- Type-safe interfaces
- Tool management
- Platform integration
- Error handling
"""

from .client import TruffleClient
from .types.models import (
    TruffleReturnType,
    ToolMetadata,
    AppMetadata,
)

# Only expose necessary types for public API
__all__ = [
    # Client
    "TruffleClient",
    
    # Types
    "TruffleReturnType",
    "ToolMetadata",
    "AppMetadata",
]

# Proprietary implementation details
__proprietary__ = True
