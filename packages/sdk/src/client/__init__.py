"""
Client Package Module

This package provides the main interface to the Truffle platform:
- Complete SDK client implementation
- Type-safe configuration and validation
- Comprehensive error handling
- Clean and documented interfaces
"""

from .base import TruffleClient, APP_SOCK, SDK_SOCK, SHARED_FILES_DIR
from .exceptions import (
    TruffleError,
    ConnectionError,
    RPCError,
    ValidationError,
    ModelError,
    GenerationError,
    ContextError,
    ToolError,
    ResponseError,
    ConfigurationError,
)
from .types import (
    ClientConfig,
    ModelConfig,
    ContextConfig,
    ResponseValidator,
    TypeConverter,
    validate_client_config,
    validate_model_config,
    validate_context_config,
)

__all__ = [
    # Main client
    "TruffleClient",
    
    # Configuration
    "APP_SOCK",
    "SDK_SOCK",
    "SHARED_FILES_DIR",
    
    # Exceptions
    "TruffleError",
    "ConnectionError",
    "RPCError",
    "ValidationError",
    "ModelError",
    "GenerationError",
    "ContextError",
    "ToolError",
    "ResponseError",
    "ConfigurationError",
    
    # Types and Configuration
    "ClientConfig",
    "ModelConfig",
    "ContextConfig",
    "ResponseValidator",
    "TypeConverter",
    
    # Validation Functions
    "validate_client_config",
    "validate_model_config",
    "validate_context_config",
]
