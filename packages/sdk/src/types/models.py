"""
Core Type System Implementation

Core types and classes for the Truffle SDK:

Features:
- TruffleReturnType: Base class for all return types
- TruffleFile: File handling with validation
- TruffleImage: Image handling (url, base64, raw)
- ToolMetadata: Tool registration and metadata
- ToolRegistry: Tool management and validation
"""

import base64
import os
import shutil
import typing
from dataclasses import dataclass
from pathlib import Path
from ..platform import sdk_pb2
from ..client.exceptions import ValidationError

class TruffleReturnType:
    """Base class for all Truffle return types."""
    def __init__(self, type: sdk_pb2.TruffleType):
        self.type = type

class TruffleFile(TruffleReturnType):
    """
    Represents a file in the Truffle system with enhanced validation.
    
    Features:
    - Path validation and normalization
    - Secure file operations
    - Comprehensive error handling
    - File metadata preservation
    """
    
    def __init__(self, path: typing.Union[str, Path], name: str = None):
        """
        Initialize a TruffleFile.
        
        Args:
            path: Path to the file
            name: Optional custom name (defaults to filename)
            
        Raises:
            ValidationError: If file validation fails
        """
        super().__init__(sdk_pb2.TruffleType.TRUFFLE_TYPE_FILE)
        self.path = Path(path).resolve()
        self.name = name or self.path.name
        self._validate()

    def _validate(self) -> None:
        """
        Validate file existence and permissions.
        
        Raises:
            ValidationError: If validation fails
        """
        if not self.path.exists():
            raise ValidationError(f"File not found: {self.path}")
        if not self.path.is_file():
            raise ValidationError(f"Not a file: {self.path}")
        if not os.access(self.path, os.R_OK):
            raise ValidationError(f"File not readable: {self.path}")

    def __repr__(self) -> str:
        """Get string representation."""
        return f"TruffleFile(path='{self.path}', name='{self.name}')"

    def save(self, destination: typing.Union[str, Path]) -> str:
        """
        Save the file to the specified destination.
        
        Args:
            destination: Path where the file should be saved
            
        Returns:
            The path where the file was saved
            
        Raises:
            ValidationError: If save operation fails
        """
        try:
            dest_path = Path(destination).resolve()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy with metadata preservation
            shutil.copy2(self.path, dest_path)
            
            return str(dest_path)
            
        except (OSError, IOError) as e:
            raise ValidationError(f"Failed to save file: {str(e)}")

    @property
    def size(self) -> int:
        """Get file size in bytes."""
        return self.path.stat().st_size

    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.path.suffix.lower()

    def read_bytes(self) -> bytes:
        """
        Read file contents as bytes.
        
        Returns:
            File contents as bytes
            
        Raises:
            ValidationError: If read operation fails
        """
        try:
            return self.path.read_bytes()
        except (OSError, IOError) as e:
            raise ValidationError(f"Failed to read file: {str(e)}")

    def read_text(self, encoding: str = 'utf-8') -> str:
        """
        Read file contents as text.
        
        Args:
            encoding: Text encoding to use
            
        Returns:
            File contents as string
            
        Raises:
            ValidationError: If read operation fails
        """
        try:
            return self.path.read_text(encoding=encoding)
        except (OSError, IOError) as e:
            raise ValidationError(f"Failed to read file: {str(e)}")

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
