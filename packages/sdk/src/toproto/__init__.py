"""
Proto Generation Package

Core implementation of protobuf and gRPC service generation utilities:

Features:
- Type system for basic and complex types
- Function and service conversion
- Message and field generation
- Documentation preservation
"""

from .converter_base import (
    ConverterBase,
    ProtoField,
    ProtoMessage,
    ProtoMethod,
    ProtoService,
)

from .func_to_proto import (
    FunctionConverter,
    FunctionSpec,
)

from .func_to_service import (
    ServiceConverter,
    ServiceSpec,
)

__all__ = [
    # Base types
    "ConverterBase",
    "ProtoField",
    "ProtoMessage",
    "ProtoMethod",
    "ProtoService",
    
    # Function conversion
    "FunctionConverter",
    "FunctionSpec",
    
    # Service conversion
    "ServiceConverter",
    "ServiceSpec",
] 