"""
Exception Classes Module

This module provides a comprehensive set of exceptions for the SDK client:
- Structured error hierarchy for different failure modes
- Rich error context and details preservation
- Integration with gRPC error handling
- Type-safe error construction and handling
"""

import typing
import grpc


class TruffleError(Exception):
    """Base class for all Truffle SDK exceptions."""
    pass


class ConnectionError(TruffleError):
    """Raised when there are issues connecting to the gRPC service."""
    def __init__(self, message: str, details: typing.Optional[str] = None):
        super().__init__(f"{message}: {details}" if details else message)
        self.details = details


class RPCError(TruffleError):
    """Raised when a gRPC call fails."""
    def __init__(self, method: str, details: str):
        super().__init__(f"RPC error in {method}: {details}")
        self.method = method
        self.details = details

    @classmethod
    def from_grpc_error(cls, method: str, error: grpc.RpcError) -> 'RPCError':
        """Create an RPCError from a gRPC error."""
        return cls(method, error.details())


class ValidationError(TruffleError):
    """Raised when input validation fails."""
    pass


class ModelError(TruffleError):
    """Raised when there are issues with model operations."""
    pass


class GenerationError(TruffleError):
    """Raised when text generation fails."""
    def __init__(self, message: str, finish_reason: typing.Optional[str] = None):
        super().__init__(message)
        self.finish_reason = finish_reason


class ContextError(TruffleError):
    """Raised when there are issues with conversation context."""
    pass


class ToolError(TruffleError):
    """Raised when tool operations fail."""
    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Tool '{tool_name}' error: {message}")
        self.tool_name = tool_name


class ResponseError(TruffleError):
    """Raised when response parsing or handling fails."""
    pass


class ConfigurationError(TruffleError):
    """Raised when there are issues with SDK configuration."""
    pass
