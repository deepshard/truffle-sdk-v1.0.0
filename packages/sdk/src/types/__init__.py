"""
Type System Module

Core type system for the Truffle SDK:

Features:
- Return Types: TruffleReturnType, TruffleFile, TruffleImage
- Tool Types: ToolMetadata, ToolRegistry
- Application Types: AppMetadata
- Type Utilities: Validation and conversion
"""

from .models import (
    TruffleReturnType,
    TruffleFile,
    TruffleImage,
    ToolMetadata,
    ToolRegistry,
    AppMetadata,
    is_truffle_type,
    is_file_type,
    is_image_type,
    validate_type,
    to_proto_type,
    from_proto_type,
)

__all__ = [
    "TruffleReturnType",
    "TruffleFile",
    "TruffleImage",
    "ToolMetadata",
    "ToolRegistry",
    "AppMetadata",
    "is_truffle_type",
    "is_file_type",
    "is_image_type",
    "validate_type",
    "to_proto_type",
    "from_proto_type",
]
