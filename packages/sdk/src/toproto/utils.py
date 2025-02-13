"""
Protocol Buffer Utilities Module

Core utilities for protocol buffer operations:

Features:
- Type conversion between Python and Protocol Buffers
- Descriptor handling for messages, fields, services, and files
- Name processing and validation for proto identifiers
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from google.protobuf.descriptor import (
    Descriptor,
    FieldDescriptor,
    FileDescriptor,
    ServiceDescriptor
)

# Type mapping from Python to Proto
PYTHON_TO_PROTO_TYPES = {
    str: FieldDescriptor.TYPE_STRING,
    int: FieldDescriptor.TYPE_INT64,
    float: FieldDescriptor.TYPE_DOUBLE,
    bool: FieldDescriptor.TYPE_BOOL,
    bytes: FieldDescriptor.TYPE_BYTES,
}

# Type mapping from Proto to Python
PROTO_TO_PYTHON_TYPES = {
    FieldDescriptor.TYPE_DOUBLE: float,
    FieldDescriptor.TYPE_FLOAT: float,
    FieldDescriptor.TYPE_INT64: int,
    FieldDescriptor.TYPE_UINT64: int,
    FieldDescriptor.TYPE_INT32: int,
    FieldDescriptor.TYPE_UINT32: int,
    FieldDescriptor.TYPE_BOOL: bool,
    FieldDescriptor.TYPE_STRING: str,
    FieldDescriptor.TYPE_BYTES: bytes,
    FieldDescriptor.TYPE_MESSAGE: object,
    FieldDescriptor.TYPE_ENUM: int,
}

def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', name).lower()

def validate_proto_name(name: str) -> bool:
    """
    Validate a protocol buffer identifier name.
    
    Rules:
    - Must start with letter
    - Can contain letters, numbers, underscores
    - Cannot use proto3 reserved words
    """
    if not name or not name[0].isalpha():
        return False
        
    if not all(c.isalnum() or c == '_' for c in name):
        return False
        
    # Proto3 reserved words
    reserved = {
        'syntax', 'import', 'weak', 'public', 'package', 'option', 'repeated',
        'oneof', 'map', 'reserved', 'to', 'max', 'enum', 'message', 'service',
        'rpc', 'stream', 'returns', 'true', 'false'
    }
    
    return name.lower() not in reserved

def get_field_type(python_type: Type) -> int:
    """Get protocol buffer field type for Python type."""
    if python_type in PYTHON_TO_PROTO_TYPES:
        return PYTHON_TO_PROTO_TYPES[python_type]
    
    if hasattr(python_type, 'DESCRIPTOR'):
        return FieldDescriptor.TYPE_MESSAGE
        
    if hasattr(python_type, '_values_'):
        return FieldDescriptor.TYPE_ENUM
        
    raise ValueError(f"Cannot map Python type {python_type} to proto type")

def get_python_type(field_type: int) -> Type:
    """Get Python type for protocol buffer field type."""
    if field_type in PROTO_TO_PYTHON_TYPES:
        return PROTO_TO_PYTHON_TYPES[field_type]
        
    raise ValueError(f"Cannot map proto type {field_type} to Python type")

def get_field_default(field_type: int) -> Any:
    """Get default value for protocol buffer field type."""
    if field_type in {
        FieldDescriptor.TYPE_DOUBLE,
        FieldDescriptor.TYPE_FLOAT,
        FieldDescriptor.TYPE_INT64,
        FieldDescriptor.TYPE_UINT64,
        FieldDescriptor.TYPE_INT32,
        FieldDescriptor.TYPE_UINT32,
    }:
        return 0
        
    if field_type == FieldDescriptor.TYPE_BOOL:
        return False
        
    if field_type == FieldDescriptor.TYPE_STRING:
        return ""
        
    if field_type == FieldDescriptor.TYPE_BYTES:
        return b""
        
    if field_type == FieldDescriptor.TYPE_ENUM:
        return 0
        
    return None

def is_message_type(python_type: Type) -> bool:
    """Check if a Python type represents a protocol buffer message."""
    return hasattr(python_type, 'DESCRIPTOR')

def is_enum_type(python_type: Type) -> bool:
    """Check if a Python type represents a protocol buffer enum."""
    return hasattr(python_type, '_values_')

def get_message_fields(desc: Descriptor) -> List[FieldDescriptor]:
    """Get all fields from a message descriptor."""
    return list(desc.fields)

def get_nested_messages(desc: Descriptor) -> List[Descriptor]:
    """Get all nested message types from a message descriptor."""
    return list(desc.nested_types)

def get_nested_enums(desc: Descriptor) -> List[Descriptor]:
    """Get all nested enum types from a message descriptor."""
    return list(desc.enum_types)

def get_package_name(desc: FileDescriptor) -> str:
    """
    Get package name from a file descriptor.
    
    Args:
        desc: File descriptor
        
    Returns:
        Package name
    """
    return desc.package or "" 