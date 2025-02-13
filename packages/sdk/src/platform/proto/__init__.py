"""
Proto Conversion Package

This package provides utilities for protobuf message handling:
- Type conversion between Python and protobuf
- Message validation and error checking
- Serialization and deserialization
- Clean interfaces for message handling
"""

from .converters import (
    to_proto_type,
    from_proto_type,
    to_proto_content,
    from_proto_content,
    to_proto_request,
    from_proto_response,
    to_proto_app_metadata,
    from_proto_app_metadata,
    message_to_dict,
    dict_to_message,
)

from .validation import (
    validate_truffle_type,
    validate_proto_type,
    validate_content_role,
    validate_proto_content,
    validate_tool_metadata,
    validate_tool_request,
    validate_tool_response,
    validate_app_metadata,
    validate_generate_request,
    validate_generate_response,
)

__all__ = [
    # Converters
    "to_proto_type",
    "from_proto_type",
    "to_proto_content",
    "from_proto_content",
    "to_proto_request",
    "from_proto_response",
    "to_proto_app_metadata",
    "from_proto_app_metadata",
    "message_to_dict",
    "dict_to_message",
    
    # Validation
    "validate_truffle_type",
    "validate_proto_type",
    "validate_content_role",
    "validate_proto_content",
    "validate_tool_metadata",
    "validate_tool_request",
    "validate_tool_response",
    "validate_app_metadata",
    "validate_generate_request",
    "validate_generate_response",
] 