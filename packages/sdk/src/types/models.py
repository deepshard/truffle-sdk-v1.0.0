"""
Core Type System Implementation

Core types and classes for the Truffle SDK:

Features:
- TruffleReturnType: Base class for all return types
- TruffleFile: File handling and operations
- TruffleImage: Image handling (url, base64, raw)
- ToolMetadata: Tool registration and metadata
- ToolRegistry: Tool management and validation
"""

import base64
import os
import typing
from dataclasses import dataclass
import inspect
import requests
from ..platform import sdk_pb2

class TruffleReturnType:
    """Base class for all Truffle return types."""
    def __init__(self, type: sdk_pb2.TruffleType):
        self.type = type

class TruffleFile(TruffleReturnType):
    """Represents a file in the Truffle system."""
    def __init__(self, path: str, name: str):
        super().__init__(sdk_pb2.TruffleType.TRUFFLE_TYPE_FILE)
        self.path = path
        self.name = name

    def __repr__(self) -> str:
        return f"TruffleFile(path='{self.path}', name='{self.name}')"

    def save(self, destination: str) -> str:
        """
        Save the file to the specified destination.
        
        Args:
            destination: Path where the file should be saved
            
        Returns:
            The path where the file was saved
        """
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        if os.path.exists(self.path):
            with open(self.path, "rb") as src, open(destination, "wb") as dst:
                dst.write(src.read())
        return destination

class TruffleImage(TruffleReturnType):
    """Represents an image in the Truffle system."""
    def __init__(
        self, 
        name: str, 
        url: str = None, 
        base64_data: str = None, 
        data: bytes = None
    ):
        super().__init__(sdk_pb2.TruffleType.TRUFFLE_TYPE_IMAGE)
        self.name = name
        self.url = url
        self.base64_data = base64_data
        self.data = data

        if not any([url, base64_data, data]):
            raise ValueError("Must provide either url, base64_data, or data")

    def __repr__(self) -> str:
        return f"TruffleImage(name='{self.name}', url='{self.url}')"

    def save(self, destination: str) -> str:
        """
        Save the image to the specified destination.
        
        Args:
            destination: Path where the image should be saved
            
        Returns:
            The path where the image was saved
        """
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        if self.data:
            with open(destination, "wb") as f:
                f.write(self.data)
        elif self.base64_data:
            with open(destination, "wb") as f:
                f.write(base64.b64decode(self.base64_data))
        elif self.url:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        return destination

@dataclass
class ToolMetadata:
    """Metadata for a registered tool."""
    name: str
    description: str
    icon: typing.Optional[str] = None
    args: typing.Dict[str, str] = None

    def __post_init__(self):
        if self.args is None:
            self.args = {}

class ToolRegistry:
    """Registry for all available tools."""
    def __init__(self):
        self.tools: typing.Dict[str, ToolMetadata] = {}
        self.registered_functions: typing.Dict[str, typing.Callable] = {}

    def register(self, func: typing.Callable, metadata: ToolMetadata) -> None:
        """Register a tool with its metadata."""
        if not hasattr(func, "__truffle_tool__"):
            raise ValueError(f"Function {func.__name__} is not decorated as a tool")
        
        name = metadata.name or func.__name__
        if name in self.tools:
            raise ValueError(f"Tool {name} is already registered")

        self.tools[name] = metadata
        self.registered_functions[name] = func

    def get_tool(self, name: str) -> typing.Tuple[typing.Callable, ToolMetadata]:
        """Get a tool and its metadata by name."""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return self.registered_functions[name], self.tools[name]

    def list_tools(self) -> typing.List[ToolMetadata]:
        """List all registered tools."""
        return list(self.tools.values())

@dataclass
class AppMetadata:
    """Metadata for a Truffle application."""
    fullname: str
    description: str
    name: str
    goal: str
    icon_url: str = ""

def is_truffle_type(obj: typing.Any) -> bool:
    """Check if an object is a Truffle return type."""
    return isinstance(obj, TruffleReturnType)

def is_file_type(obj: typing.Any) -> bool:
    """Check if an object is a TruffleFile."""
    return isinstance(obj, TruffleFile)

def is_image_type(obj: typing.Any) -> bool:
    """Check if an object is a TruffleImage."""
    return isinstance(obj, TruffleImage)

def validate_type(obj: typing.Any, expected_type: typing.Type[TruffleReturnType]) -> bool:
    """Validate that an object is of the expected Truffle type."""
    return isinstance(obj, expected_type)

def to_proto_type(obj: TruffleReturnType) -> sdk_pb2.TruffleType:
    """Convert a Truffle return type to its proto enum value."""
    return obj.type

def from_proto_type(type_enum: sdk_pb2.TruffleType) -> typing.Type[TruffleReturnType]:
    """Get the appropriate Truffle return type class from a proto enum value."""
    type_map = {
        sdk_pb2.TruffleType.TRUFFLE_FILE: TruffleFile,
        sdk_pb2.TruffleType.TRUFFLE_IMAGE: TruffleImage,
    }
    return type_map.get(type_enum, TruffleReturnType)
