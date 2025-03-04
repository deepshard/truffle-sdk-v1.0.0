"""
Proto Validation Utilities

This module provides validation functions for protobuf messages:
- Type validation for Truffle and proto types
- Content and role validation
- Request and response message validation
- Metadata validation utilities
"""

import typing
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.message import Message
from ...types.models import TruffleReturnType, ToolMetadata, AppMetadata
from .. import sdk_pb2
from ...client.exceptions import ValidationError

def is_numeric_field(field: FieldDescriptor) -> bool:
    """Check if a field is a numeric type."""
    numeric_types = [
        FieldDescriptor.TYPE_DOUBLE,
        FieldDescriptor.TYPE_FLOAT,
        FieldDescriptor.TYPE_INT32,
        FieldDescriptor.TYPE_INT64,
        FieldDescriptor.TYPE_UINT32,
        FieldDescriptor.TYPE_UINT64,
        FieldDescriptor.TYPE_SINT32,
        FieldDescriptor.TYPE_SINT64,
        FieldDescriptor.TYPE_FIXED32,
        FieldDescriptor.TYPE_FIXED64,
        FieldDescriptor.TYPE_SFIXED32,
        FieldDescriptor.TYPE_SFIXED64,
    ]
    return field.type in numeric_types

def is_float_field(field: FieldDescriptor) -> bool:
    """Check if a field is a float type."""
    return field.type in [FieldDescriptor.TYPE_DOUBLE, FieldDescriptor.TYPE_FLOAT]

def validate_field_value(value: Any, field: FieldDescriptor) -> Any:
    """
    Validate and convert a field value.
    
    Args:
        value: Value to validate
        field: Field descriptor
        
    Returns:
        Validated value
        
    Raises:
        TypeError: If value has invalid type
        ValueError: If value is invalid
    """
    if value is None:
        if field.label == FieldDescriptor.LABEL_REQUIRED:
            raise ValueError(f"Field {field.name} is required")
        return get_field_default(field.type)
        
    # Handle message types
    if field.type == FieldDescriptor.TYPE_MESSAGE:
        if not isinstance(value, (dict, Message)):
            raise TypeError(
                f"Field {field.name} must be a Message or dict"
            )
        if isinstance(value, dict):
            msg = field.message_type._concrete_class()
            for k, v in value.items():
                setattr(msg, k, v)
            return msg
        return value
        
    # Handle enum types
    if field.type == FieldDescriptor.TYPE_ENUM:
        if isinstance(value, str):
            if not hasattr(field.enum_type, value):
                raise ValueError(
                    f"Invalid enum value '{value}' for field {field.name}"
                )
            return getattr(field.enum_type, value)
        if not isinstance(value, int):
            raise TypeError(f"Field {field.name} must be an integer or string")
        if value not in field.enum_type._values_.values():
            raise ValueError(
                f"Invalid enum value {value} for field {field.name}"
            )
        return value
        
    # Handle basic types
    try:
        return get_python_type(field.type)(value)
    except (TypeError, ValueError) as e:
        raise TypeError(
            f"Cannot convert value '{value}' to {get_python_type(field.type).__name__} "
            f"for field {field.name}: {e}"
        )

def get_python_type(field_type: int) -> Type:
    """Get Python type for protocol buffer field type."""
    type_map = {
        FieldDescriptor.TYPE_DOUBLE: float,
        FieldDescriptor.TYPE_FLOAT: float,
        FieldDescriptor.TYPE_INT64: int,
        FieldDescriptor.TYPE_UINT64: int,
        FieldDescriptor.TYPE_INT32: int,
        FieldDescriptor.TYPE_UINT32: int,
        FieldDescriptor.TYPE_BOOL: bool,
        FieldDescriptor.TYPE_STRING: str,
        FieldDescriptor.TYPE_BYTES: bytes,
        FieldDescriptor.TYPE_MESSAGE: Message,
        FieldDescriptor.TYPE_ENUM: int,
    }
    if field_type not in type_map:
        raise ValueError(f"Unsupported field type: {field_type}")
    return type_map[field_type]

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

def validate_truffle_type(obj: typing.Any) -> None:
    """Validate that an object is a valid Truffle type."""
    if not isinstance(obj, TruffleReturnType):
        raise ValidationError(f"Expected TruffleReturnType, got {type(obj)}")

def validate_proto_type(type_enum: sdk_pb2.TruffleType) -> None:
    """Validate that a proto type enum is valid."""
    valid_types = [
        sdk_pb2.TruffleType.TRUFFLE_TYPE_FILE,
        sdk_pb2.TruffleType.TRUFFLE_TYPE_IMAGE,
        sdk_pb2.TruffleType.TRUFFLE_TYPE_UNSPECIFIED,
    ]
    if type_enum not in valid_types:
        raise ValidationError(f"Invalid TruffleType enum value: {type_enum}")

def validate_content_role(role: str) -> None:
    """Validate that a content role string is valid."""
    valid_roles = ["system", "user", "ai"]
    if role.lower() not in valid_roles:
        raise ValidationError(f"Invalid content role: {role}")

def validate_proto_content(content: sdk_pb2.Content) -> None:
    """Validate that a proto Content message is valid."""
    valid_roles = [
        sdk_pb2.Content.ROLE_SYSTEM,
        sdk_pb2.Content.ROLE_USER,
        sdk_pb2.Content.ROLE_AI,
        sdk_pb2.Content.ROLE_INVALID,
    ]
    if content.role not in valid_roles:
        raise ValidationError(f"Invalid Content role: {content.role}")
    if not content.content:
        raise ValidationError("Content message cannot be empty")

def validate_tool_metadata(tool: ToolMetadata) -> None:
    """Validate that tool metadata is valid."""
    if not tool.name:
        raise ValidationError("Tool name cannot be empty")
    if not tool.description:
        raise ValidationError("Tool description cannot be empty")

def validate_tool_request(request: sdk_pb2.ToolRequest) -> None:
    """Validate that a proto ToolRequest message is valid."""
    if not request.tool_name:
        raise ValidationError("Tool name cannot be empty")
    if not request.description:
        raise ValidationError("Tool description cannot be empty")

def validate_tool_response(response: sdk_pb2.ToolResponse) -> None:
    """Validate that a proto ToolResponse message is valid."""
    if not response.response and not response.error:
        raise ValidationError("ToolResponse must have either response or error")

def validate_app_metadata(metadata: AppMetadata) -> None:
    """Validate that app metadata is valid."""
    if not metadata.fullname:
        raise ValidationError("App fullname cannot be empty")
    if not metadata.name:
        raise ValidationError("App name cannot be empty")
    if not metadata.description:
        raise ValidationError("App description cannot be empty")
    if not metadata.goal:
        raise ValidationError("App goal cannot be empty")
    if metadata.manifest_version < 1:
        raise ValidationError("Manifest version must be positive")
    if not isinstance(metadata.example_prompts, list):
        raise ValidationError("Example prompts must be a list")

def validate_generate_request(request: sdk_pb2.GenerateRequest) -> None:
    """Validate that a GenerateRequest message is valid."""
    if request.model_id < 0:
        raise ValidationError("Model ID cannot be negative")
    if request.max_tokens <= 0:
        raise ValidationError("Max tokens must be positive")
    if not 0 <= request.temperature <= 1:
        raise ValidationError("Temperature must be between 0 and 1")

def validate_generate_response(response: sdk_pb2.GenerateResponse) -> None:
    """Validate that a GenerateResponse message is valid."""
    if response.error and response.token:
        raise ValidationError("Response cannot have both error and token")
    if response.finish_reason == sdk_pb2.GenerateFinishReason.FINISH_REASON_ERROR and not response.error:
        raise ValidationError("Error finish reason must have error message") 