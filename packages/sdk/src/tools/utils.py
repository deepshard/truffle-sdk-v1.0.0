"""
Tool Utilities Module

Core utility functions for tool management and validation:

Features:
- Type validation and conversion
- Function inspection and metadata
- Path operations and validation
- String processing and sanitization
"""

import inspect
import typing
import warnings
import os
from pathlib import Path
from typing import (
    Any, Dict, Optional, Tuple, Type, Union,
    get_type_hints, get_origin, get_args
)

from ..platform import sdk_pb2

# Type definitions
ArgSpec = Dict[str, Any]
TypeSpec = Union[Type, str]
MetadataDict = Dict[str, Any]

# Constants
MAX_STRING_LENGTH = 1000
TRUFFLE_TYPES = {
    'string': str,
    'integer': int,
    'float': float,
    'boolean': bool,
    'array': list,
    'object': dict,
    'null': type(None)
}

def get_type_origin(type_hint: Any) -> Optional[Any]:
    """
    Get the origin of a type hint safely.
    
    Args:
        type_hint: Type hint to inspect
        
    Returns:
        Type origin or None
    """
    try:
        return get_origin(type_hint) or type_hint
    except Exception:
        return None

def get_type_args(type_hint: Any) -> Tuple[Any, ...]:
    """
    Get the arguments of a type hint safely.
    
    Args:
        type_hint: Type hint to inspect
        
    Returns:
        Tuple of type arguments
    """
    try:
        return get_args(type_hint)
    except Exception:
        return ()

def validate_return_type(value: Any, expected_type: TypeSpec) -> bool:
    """
    Validate a return value against its expected type.
    
    Args:
        value: The value to validate
        expected_type: The expected type
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Handle Any type
        if expected_type == 'Any' or expected_type == Any:
            return True
            
        # Convert string type specs
        if isinstance(expected_type, str):
            if expected_type in TRUFFLE_TYPES:
                expected_type = TRUFFLE_TYPES[expected_type]
            else:
                # Handle complex string types (e.g. "List[str]")
                try:
                    expected_type = eval(expected_type, globals(), {'typing': typing})
                except Exception:
                    return False
        
        # Get type origin and args
        origin = get_type_origin(expected_type)
        args = get_type_args(expected_type)
        
        # Handle None
        if origin is type(None):
            return value is None
            
        # Handle Union types (including Optional)
        if origin is Union:
            return any(
                validate_return_type(value, arg)
                for arg in args
            )
            
        # Handle container types
        if origin is list:
            if not isinstance(value, list):
                return False
            elem_type = args[0] if args else Any
            return all(validate_return_type(x, elem_type) for x in value)
            
        if origin is dict:
            if not isinstance(value, dict):
                return False
            key_type, val_type = args if len(args) == 2 else (Any, Any)
            return all(
                validate_return_type(k, key_type) and validate_return_type(v, val_type)
                for k, v in value.items()
            )
            
        if origin is tuple:
            if not isinstance(value, tuple):
                return False
            if not args or args == ((),):
                return True
            if len(args) == 2 and args[1] is ...:
                elem_type = args[0]
                return all(validate_return_type(x, elem_type) for x in value)
            return (len(value) == len(args) and
                    all(validate_return_type(v, t) for v, t in zip(value, args)))
            
        if origin is set:
            if not isinstance(value, set):
                return False
            elem_type = args[0] if args else Any
            return all(validate_return_type(x, elem_type) for x in value)
            
        # Handle basic types
        if origin in TRUFFLE_TYPES.values():
            return isinstance(value, origin)
            
        # Handle classes
        if inspect.isclass(origin):
            return isinstance(value, origin)
            
        # Handle protocol buffer messages
        if hasattr(origin, 'DESCRIPTOR'):
            return isinstance(value, origin)
            
        return isinstance(value, expected_type)
        
    except Exception as e:
        warnings.warn(f"Type validation error: {e}")
        return False

def extract_metadata(func: typing.Callable) -> MetadataDict:
    """
    Extract metadata from a tool function.
    
    Args:
        func: The function to extract metadata from
        
    Returns:
        Dictionary of metadata
    """
    # Get basic metadata
    metadata: MetadataDict = {
        'name': func.__name__,
        'doc': inspect.getdoc(func) or '',
        'module': func.__module__,
        'qualname': func.__qualname__,
        'args': {},
        'return_type': None,
        'decorators': []
    }
    
    # Get type hints
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}
    
    # Get signature
    try:
        sig = inspect.signature(func)
    except Exception:
        return metadata
    
    # Process parameters
    for name, param in sig.parameters.items():
        if name == 'self':
            continue
            
        arg_spec: ArgSpec = {
            'name': name,
            'type': hints.get(name, Any),
            'default': ... if param.default is param.empty else param.default,
            'optional': param.default is not param.empty,
            'kind': str(param.kind),
            'description': '',
            'annotations': getattr(param, '__annotations__', {})
        }
        metadata['args'][name] = arg_spec
        
    # Get return type
    metadata['return_type'] = hints.get('return', Any)
    
    # Get decorators
    if hasattr(func, '__truffle_decorators__'):
        metadata['decorators'] = func.__truffle_decorators__
        
    return metadata

def validate_tool_args(
    func: typing.Callable,
    args: Dict[str, Any],
    metadata: Optional[MetadataDict] = None
) -> None:
    """
    Validate arguments for a tool function.
    
    Args:
        func: The tool function
        args: Arguments to validate
        metadata: Optional pre-extracted metadata
        
    Raises:
        ValueError: If validation fails
        TypeError: If type validation fails
    """
    if metadata is None:
        metadata = extract_metadata(func)
        
    # Check required args
    for name, spec in metadata['args'].items():
        if not spec['optional'] and name not in args:
            raise ValueError(f"Missing required argument: {name}")
            
    # Validate types
    for name, value in args.items():
        if name not in metadata['args']:
            raise ValueError(f"Unknown argument: {name}")
            
        expected_type = metadata['args'][name]['type']
        if not validate_return_type(value, expected_type):
            raise TypeError(
                f"Invalid type for argument {name}: "
                f"expected {expected_type}, got {type(value)}"
            )

def format_error(error: Exception, tool_name: str) -> sdk_pb2.SDKResponse:
    """
    Format an error into an SDK response.
    
    Args:
        error: The error to format
        tool_name: Name of the tool that raised the error
        
    Returns:
        Formatted SDK response
    """
    error_msg = str(error)
    if isinstance(error, (ValueError, TypeError)):
        error_type = error.__class__.__name__
        error_msg = f"{error_type}: {error_msg}"
        
    return sdk_pb2.SDKResponse(
        error=f"Tool '{tool_name}' error: {error_msg}",
        error_type=type(error).__name__
    )

def convert_path(path: Union[str, Path]) -> Path:
    """
    Convert a path string to a Path object.
    
    Args:
        path: Path string or object
        
    Returns:
        Path object
        
    Raises:
        ValueError: If path is invalid
    """
    try:
        if isinstance(path, Path):
            return path.resolve()
        return Path(str(path)).resolve()
    except Exception as e:
        raise ValueError(f"Invalid path: {e}")

def validate_path(
    path: Path,
    must_exist: bool = True,
    file_okay: bool = True,
    dir_okay: bool = True,
    writable: bool = False,
    readable: bool = True
) -> None:
    """
    Validate a path.
    
    Args:
        path: Path to validate
        must_exist: Whether path must exist
        file_okay: Whether files are allowed
        dir_okay: Whether directories are allowed
        writable: Whether path must be writable
        readable: Whether path must be readable
        
    Raises:
        ValueError: If validation fails
        PermissionError: If permission check fails
    """
    try:
        if must_exist and not path.exists():
            raise ValueError(f"Path does not exist: {path}")
            
        if path.exists():
            if not file_okay and path.is_file():
                raise ValueError(f"Path must not be a file: {path}")
            if not dir_okay and path.is_dir():
                raise ValueError(f"Path must not be a directory: {path}")
                
            # Check permissions
            if readable and not os.access(path, os.R_OK):
                raise PermissionError(f"Path not readable: {path}")
            if writable and not os.access(path, os.W_OK):
                raise PermissionError(f"Path not writable: {path}")
                
    except (ValueError, PermissionError):
        raise
    except Exception as e:
        raise ValueError(f"Path validation failed: {e}")

def sanitize_string(
    s: str,
    max_length: int = MAX_STRING_LENGTH,
    allow_newlines: bool = True,
    strip: bool = True
) -> str:
    """
    Sanitize a string for safe usage.
    
    Args:
        s: String to sanitize
        max_length: Maximum length
        allow_newlines: Whether to allow newlines
        strip: Whether to strip whitespace
        
    Returns:
        Sanitized string
    """
    if not isinstance(s, str):
        s = str(s)
        
    if strip:
        s = s.strip()
        
    if not allow_newlines:
        s = s.replace('\n', ' ').replace('\r', '')
        
    if len(s) > max_length:
        s = s[:max_length-3] + "..."
        
    return s

def wrap_exceptions(
    func: typing.Callable,
    tool_name: Optional[str] = None
) -> typing.Callable:
    """
    Decorator to wrap exceptions in tool-specific errors.
    
    Args:
        func: Function to wrap
        tool_name: Optional tool name override
        
    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            name = tool_name or getattr(func, '__name__', 'unknown')
            if isinstance(e, (ValueError, TypeError)):
                raise type(e)(f"Tool '{name}' error: {str(e)}") from e
            raise RuntimeError(f"Tool '{name}' failed: {str(e)}") from e
    return wrapper
