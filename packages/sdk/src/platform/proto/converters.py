"""
Proto Conversion Utilities

This module provides conversion functions between Python types and protobuf messages:
- Type conversion between Truffle types and proto enums
- Content message serialization and deserialization
- Tool request/response message handling
- Metadata conversion utilities
"""

import typing
from dataclasses import asdict
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
    """Convert a Python Truffle type to its proto enum value."""
    type_map = {
        TruffleFile: sdk_pb2.TruffleType.TRUFFLE_TYPE_FILE,
        TruffleImage: sdk_pb2.TruffleType.TRUFFLE_TYPE_IMAGE,
    }
    return type_map.get(type(obj), sdk_pb2.TruffleType.TRUFFLE_TYPE_UNSPECIFIED)

def from_proto_type(type_enum: sdk_pb2.TruffleType) -> typing.Type[TruffleReturnType]:
    """Convert a proto enum value to its corresponding Python Truffle type."""
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
    """Convert Python content to a proto Content message."""
    role_map = {
        "system": sdk_pb2.Content.ROLE_SYSTEM,
        "user": sdk_pb2.Content.ROLE_USER,
        "ai": sdk_pb2.Content.ROLE_AI,
    }
    proto_role = role_map.get(role.lower(), sdk_pb2.Content.ROLE_INVALID)
    return sdk_pb2.Content(role=proto_role, content=content, data=data)

def from_proto_content(content: sdk_pb2.Content) -> typing.Dict[str, typing.Any]:
    """Convert a proto Content message to a Python dictionary."""
    role_map = {
        sdk_pb2.Content.ROLE_SYSTEM: "system",
        sdk_pb2.Content.ROLE_USER: "user",
        sdk_pb2.Content.ROLE_AI: "ai",
    }
    return {
        "role": role_map.get(content.role, "invalid"),
        "content": content.content,
        "data": content.data if content.HasField("data") else None,
    }

def to_proto_request(
    tool: ToolMetadata,
    args: typing.Dict[str, str]
) -> sdk_pb2.ToolRequest:
    """Convert Python tool metadata to a proto ToolRequest message."""
    return sdk_pb2.ToolRequest(
        tool_name=tool.name,
        description=tool.description,
        icon=tool.icon or "",
        args=args,
    )

def from_proto_response(response: sdk_pb2.ToolResponse) -> typing.Dict[str, typing.Any]:
    """Convert a proto ToolResponse message to a Python dictionary."""
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
    """Convert Python AppMetadata to a proto AppMetadata message."""
    return sdk_pb2.AppMetadata(
        fullname=app.fullname,
        description=app.description,
        name=app.name,
        goal=app.goal,
        icon_url=app.icon_url,
    )

def from_proto_app_metadata(metadata: sdk_pb2.AppMetadata) -> AppMetadata:
    """Convert a proto AppMetadata message to a Python AppMetadata object."""
    return AppMetadata(
        fullname=metadata.fullname,
        description=metadata.description,
        name=metadata.name,
        goal=metadata.goal,
        icon_url=metadata.icon_url,
    )

def message_to_dict(message) -> dict:
    """Convert a protobuf message to a Python dictionary."""
    return json_format.MessageToDict(
        message,
        preserving_proto_field_name=True,
        including_default_value_fields=True,
    )

def dict_to_message(data: dict, message_type) -> typing.Any:
    """Convert a Python dictionary to a protobuf message."""
    return json_format.ParseDict(data, message_type()) 