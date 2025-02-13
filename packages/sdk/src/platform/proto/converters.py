"""
Proto Conversion Utilities

This module provides conversion functions between Python types and protobuf messages:
- Type conversion between Truffle types and proto enums
- Content message serialization and deserialization
- Tool request/response message handling
- Metadata conversion utilities
"""

import typing
from dataclasses import asdict as dataclass_asdict
from google.protobuf import json_format

from ...types.models import (
    TruffleReturnType,
    TruffleFile,
    TruffleImage,
    ToolMetadata,
    AppMetadata,
)
from .. import sdk_pb2
from ...client.exceptions import ValidationError

def to_proto_type(obj: TruffleReturnType) -> sdk_pb2.TruffleType:
    """
    Convert a Python Truffle type to its proto enum value.
    
    Args:
        obj: Truffle type instance to convert
        
    Returns:
        Corresponding proto enum value
        
    Raises:
        ValidationError: If type conversion fails
    """
    type_map = {
        TruffleFile: sdk_pb2.TruffleType.TRUFFLE_TYPE_FILE,
        TruffleImage: sdk_pb2.TruffleType.TRUFFLE_TYPE_IMAGE,
    }
    return type_map.get(type(obj), sdk_pb2.TruffleType.TRUFFLE_TYPE_UNSPECIFIED)

def from_proto_type(type_enum: sdk_pb2.TruffleType) -> typing.Type[TruffleReturnType]:
    """
    Convert a proto enum value to its corresponding Python Truffle type.
    
    Args:
        type_enum: Proto type enum value
        
    Returns:
        Corresponding Python type class
        
    Raises:
        ValidationError: If type conversion fails
    """
    type_map = {
        sdk_pb2.TruffleType.TRUFFLE_TYPE_FILE: TruffleFile,
        sdk_pb2.TruffleType.TRUFFLE_TYPE_IMAGE: TruffleImage,
    }
    return type_map.get(type_enum, TruffleReturnType)

def to_proto_content(
    role: str,
    content: str,
    data: typing.Optional[bytes] = None
) -> sdk_pb2.Content:
    """
    Convert Python content to a proto Content message.
    
    Args:
        role: Content role (system, user, ai)
        content: Content text
        data: Optional binary data
        
    Returns:
        Proto Content message
        
    Raises:
        ValidationError: If role is invalid
    """
    role_map = {
        "system": sdk_pb2.Content.ROLE_SYSTEM,
        "user": sdk_pb2.Content.ROLE_USER,
        "ai": sdk_pb2.Content.ROLE_AI,
    }
    proto_role = role_map.get(role.lower())
    if proto_role is None:
        raise ValidationError(f"Invalid content role: {role}")
        
    return sdk_pb2.Content(
        role=proto_role,
        content=content,
        data=data
    )

def from_proto_content(content: sdk_pb2.Content) -> typing.Dict[str, typing.Any]:
    """
    Convert a proto Content message to a Python dictionary.
    
    Args:
        content: Proto Content message
        
    Returns:
        Dictionary with role, content, and optional data
        
    Raises:
        ValidationError: If content is invalid
    """
    role_map = {
        sdk_pb2.Content.ROLE_SYSTEM: "system",
        sdk_pb2.Content.ROLE_USER: "user",
        sdk_pb2.Content.ROLE_AI: "ai",
    }
    role = role_map.get(content.role)
    if role is None:
        raise ValidationError(f"Invalid content role enum: {content.role}")
        
    result = {
        "role": role,
        "content": content.content,
    }
    if content.HasField("data"):
        result["data"] = content.data
    return result

def to_proto_request(tool: ToolMetadata) -> sdk_pb2.ToolRequest:
    """
    Convert Python tool metadata to a proto ToolRequest message.
    
    Args:
        tool: Tool metadata to convert
        
    Returns:
        Proto ToolRequest message
        
    Raises:
        ValidationError: If tool metadata is invalid
    """
    if not tool.name:
        raise ValidationError("Tool name cannot be empty")
    if not tool.description:
        raise ValidationError("Tool description cannot be empty")
        
    return sdk_pb2.ToolRequest(
        tool_name=tool.name,
        description=tool.description,
        icon=tool.icon or "",
        args=dataclass_asdict(tool).get("args", {})
    )

def from_proto_response(response: sdk_pb2.ToolResponse) -> typing.Dict[str, typing.Any]:
    """
    Convert a proto ToolResponse message to a Python dictionary.
    
    Args:
        response: Proto ToolResponse message
        
    Returns:
        Dictionary with response data
        
    Raises:
        ValidationError: If response is invalid
    """
    if not response.response and not response.error:
        raise ValidationError("Response must have either response or error")
        
    result = {
        "success": not bool(response.error),
        "response": response.response,
    }
    if response.HasField("error"):
        result["error"] = response.error
    if response.HasField("data"):
        result["data"] = response.data
    return result

def to_proto_app_metadata(app: AppMetadata) -> sdk_pb2.AppMetadata:
    """
    Convert Python AppMetadata to a proto AppMetadata message.
    
    Args:
        app: App metadata to convert
        
    Returns:
        Proto AppMetadata message
        
    Raises:
        ValidationError: If app metadata is invalid
    """
    if not app.name:
        raise ValidationError("App name cannot be empty")
    if not app.description:
        raise ValidationError("App description cannot be empty")
        
    return sdk_pb2.AppMetadata(
        **dataclass_asdict(app)
    )

def from_proto_app_metadata(metadata: sdk_pb2.AppMetadata) -> AppMetadata:
    """
    Convert a proto AppMetadata message to a Python AppMetadata object.
    
    Args:
        metadata: Proto AppMetadata message
        
    Returns:
        AppMetadata instance
        
    Raises:
        ValidationError: If metadata is invalid
    """
    if not metadata.name:
        raise ValidationError("App name cannot be empty")
    if not metadata.description:
        raise ValidationError("App description cannot be empty")
        
    return AppMetadata(
        fullname=metadata.fullname,
        description=metadata.description,
        name=metadata.name,
        goal=metadata.goal,
        icon_url=metadata.icon_url,
    )

def message_to_dict(message) -> dict:
    """
    Convert a protobuf message to a Python dictionary.
    
    Args:
        message: Proto message to convert
        
    Returns:
        Dictionary representation
        
    Raises:
        ValidationError: If conversion fails
    """
    try:
        return json_format.MessageToDict(
            message,
            preserving_proto_field_name=True,
            including_default_value_fields=True,
        )
    except Exception as e:
        raise ValidationError(f"Failed to convert message to dict: {str(e)}")

def dict_to_message(data: dict, message_type) -> typing.Any:
    """
    Convert a Python dictionary to a protobuf message.
    
    Args:
        data: Dictionary to convert
        message_type: Target proto message type
        
    Returns:
        Proto message instance
        
    Raises:
        ValidationError: If conversion fails
    """
    try:
        return json_format.ParseDict(data, message_type())
    except Exception as e:
        raise ValidationError(f"Failed to convert dict to message: {str(e)}") 