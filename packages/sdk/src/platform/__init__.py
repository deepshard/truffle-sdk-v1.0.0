"""
Platform Module

This module implements the core platform interface for the Truffle SDK:
- gRPC service definitions and proto types
- Service interfaces and message types
- RPC method implementations
- Platform tool management and execution
- Type conversion and message handling
- Error handling and validation

The platform module provides a robust foundation for SDK functionality
while maintaining clean interfaces and type safety.
"""

from . import sdk_pb2
from . import sdk_pb2_grpc

__all__ = ["sdk_pb2", "sdk_pb2_grpc"]

# Package initialization will go here
