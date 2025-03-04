"""
Platform Module

This module implements the core platform interface for the Truffle SDK.

PROPRIETARY CODE - DO NOT DISTRIBUTE
This module contains proprietary gRPC tunneling and service implementation logic.
Unauthorized copying, modification, distribution, or use of this code is strictly prohibited.

Features:
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

# Only expose necessary types for public API
__all__ = [
    "sdk_pb2",
    "sdk_pb2_grpc",
]

# Proprietary implementation details
__proprietary__ = True

# Package initialization will go here
