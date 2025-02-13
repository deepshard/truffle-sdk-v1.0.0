"""
Proto Validation Utilities

This module provides validation functions for protobuf messages:
- Type validation for Truffle and proto types
- Content and role validation
- Request and response message validation
- Metadata validation utilities
"""

import typing
from ...types.models import TruffleReturnType, ToolMetadata, AppMetadata
from .. import sdk_pb2
from ...client.exceptions import ValidationError

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