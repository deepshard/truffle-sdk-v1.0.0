"""
Client Package Module

This package provides the main interface to the Truffle platform:
- Complete SDK client implementation
- Type-safe configuration and validation
- Comprehensive error handling
- Clean and documented interfaces
- Global client management
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

# Global client instance
_global_client: TruffleClient = None

def set_global_client(client: TruffleClient) -> None:
    """
    Set the global TruffleClient instance.
    
    Args:
        client: The TruffleClient instance to use globally
        
    Raises:
        ValidationError: If client validation fails
        ConfigurationError: If client is None
    """
    global _global_client
    if client is None:
        raise ConfigurationError("Cannot set None as global client")
    _global_client = client

def get_client() -> TruffleClient:
    """
    Get the global TruffleClient instance.
    
    Returns:
        The global TruffleClient instance
        
    Raises:
        ConfigurationError: If no global client has been set
    """
    if _global_client is None:
        raise ConfigurationError(
            "No global client set. Call set_global_client() first"
        )
    return _global_client

__all__ = [
    # Main client
    "TruffleClient",
    "set_global_client",
    "get_client",
    
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
