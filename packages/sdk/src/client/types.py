"""
Type Definitions Module

This module provides type definitions and utilities for the SDK client:
- Configuration dataclasses for client settings
- Response validation and type checking
- Protocol buffer type conversion
- Type-safe data handling utilities
"""

import typing
import dataclasses
from ..platform import sdk_pb2
from ..types import TruffleReturnType


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
    def to_proto_content(
        role: str,
        content: str,
        data: typing.Optional[bytes] = None
    ) -> sdk_pb2.Content:
        """Convert to proto Content message."""
        role_map = {
            "system": sdk_pb2.Content.ROLE_SYSTEM,
            "user": sdk_pb2.Content.ROLE_USER,
            "ai": sdk_pb2.Content.ROLE_AI,
        }
        proto_role = role_map.get(role.lower(), sdk_pb2.Content.ROLE_INVALID)
        return sdk_pb2.Content(role=proto_role, content=content, data=data)

    @staticmethod
    def from_proto_content(content: sdk_pb2.Content) -> typing.Dict[str, typing.Any]:
        """Convert from proto Content message."""
        role_map = {
            sdk_pb2.Content.ROLE_SYSTEM: "system",
            sdk_pb2.Content.ROLE_USER: "user",
            sdk_pb2.Content.ROLE_AI: "ai",
        }
        return {
            "role": role_map.get(content.role, "invalid"),
            "content": content.content,
            "data": content.data if content.HasField("data") else None,
        }


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
    if config.format_type and config.format_type not in ["TEXT", "JSON"]:
        raise ValueError("Format type must be either TEXT or JSON")


def validate_context_config(config: ContextConfig) -> None:
    """Validate context configuration."""
    if config.context_idx is not None and config.context_idx < 0:
        raise ValueError("Context index cannot be negative")
    if config.system_prompt is not None and not config.system_prompt.strip():
        raise ValueError("System prompt cannot be empty if provided") 