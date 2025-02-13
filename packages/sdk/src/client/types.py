"""
Type Definitions Module

This module provides type definitions and utilities for the SDK client:
- Configuration dataclasses for client settings
- Response validation and type checking
- Protocol buffer type conversion
- Type-safe data handling utilities
- Runtime validation system
"""

import typing
import dataclasses
import grpc
from typing import TYPE_CHECKING

from ..platform import sdk_pb2
from .exceptions import ValidationError, ConnectionError

if TYPE_CHECKING:
    from ..types.models import TruffleReturnType
    from .base import TruffleClient


@dataclasses.dataclass
class ClientConfig:
    """Client configuration settings."""
    host: str
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclasses.dataclass
class ModelConfig:
    """Model configuration for inference."""
    model_id: int
    max_tokens: int = 1000
    temperature: float = 0.7
    format_type: typing.Optional[str] = None
    schema: typing.Optional[str] = None


@dataclasses.dataclass
class ContextConfig:
    """Configuration for conversation context."""
    system_prompt: typing.Optional[str] = None
    context_idx: typing.Optional[int] = None
    preserve_history: bool = True


class ResponseValidator:
    """Utilities for validating responses."""

    @staticmethod
    def validate_model_response(response: sdk_pb2.ModelDescription) -> bool:
        """Validate a model description response."""
        return (
            response.model_id >= 0 and
            bool(response.name) and
            bool(response.description) and
            response.type != sdk_pb2.ModelDescription.MODEL_UNSPECIFIED
        )

    @staticmethod
    def validate_generation_response(response: sdk_pb2.TokenResponse) -> bool:
        """Validate a generation response."""
        if response.error:
            return False
        if response.finish_reason == sdk_pb2.GenerateFinishReason.FINISH_REASON_ERROR:
            return False
        return True

    @staticmethod
    def validate_embed_response(response: sdk_pb2.EmbedResponse) -> bool:
        """Validate an embedding response."""
        return len(response.results) > 0 and all(
            r.text and 0 <= r.score <= 1 for r in response.results
        )


class TypeConverter:
    """Utilities for type conversion."""

    @staticmethod
    def to_proto_type(obj: 'TruffleReturnType') -> sdk_pb2.TruffleType:
        """Convert to proto type enum."""
        return obj.type

    @staticmethod
    def from_proto_type(type_enum: sdk_pb2.TruffleType) -> typing.Type['TruffleReturnType']:
        """Get Python type from proto enum."""
        from ..types.models import TruffleFile, TruffleImage, TruffleReturnType
        type_map = {
            sdk_pb2.TruffleType.TRUFFLE_TYPE_FILE: TruffleFile,
            sdk_pb2.TruffleType.TRUFFLE_TYPE_IMAGE: TruffleImage,
        }
        return type_map.get(type_enum, TruffleReturnType)


def validate_client_config(config: ClientConfig) -> None:
    """Validate client configuration."""
    if not config.host:
        raise ValueError("Host cannot be empty")
    if config.timeout <= 0:
        raise ValueError("Timeout must be positive")
    if config.max_retries < 0:
        raise ValueError("Max retries cannot be negative")
    if config.retry_delay <= 0:
        raise ValueError("Retry delay must be positive")


def validate_model_config(config: ModelConfig) -> None:
    """Validate model configuration."""
    if config.model_id < 0:
        raise ValueError("Model ID cannot be negative")
    if config.max_tokens <= 0:
        raise ValueError("Max tokens must be positive")
    if not 0 <= config.temperature <= 1:
        raise ValueError("Temperature must be between 0 and 1")


def validate_context_config(config: ContextConfig) -> None:
    """Validate context configuration."""
    if config.context_idx is not None and config.context_idx < 0:
        raise ValueError("Context index cannot be negative")
    if config.system_prompt is not None and not config.system_prompt.strip():
        raise ValueError("System prompt cannot be empty if provided") 


@dataclasses.dataclass
class RuntimeValidator:
    """Runtime validation utilities for client operations."""
    
    @staticmethod
    def validate_client(client: 'TruffleClient') -> None:
        """
        Validate client configuration and connection.
        
        Args:
            client: TruffleClient instance to validate
            
        Raises:
            ValidationError: If client configuration is invalid
            ConnectionError: If client connection fails
        """
        # Validate client setup
        if not client.channel:
            raise ValidationError("Client channel not initialized")
        if not client.stub:
            raise ValidationError("Client stub not initialized")
            
        # Test connection
        try:
            # Attempt to list models as connection test
            client.get_models()
        except grpc.RpcError as e:
            raise ConnectionError(
                "Failed to connect to Truffle service",
                str(e)
            )
        except Exception as e:
            raise ValidationError(f"Client validation failed: {str(e)}") 