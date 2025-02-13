"""
Response Type Definitions

Core response types for the Truffle SDK:

Features:
- GenerateResponse: Model generation results
- GetModelsResponse: Available model listing
- SystemToolResponse: Tool operation results
- SDKResponse: Generic SDK responses
- UserResponse: User interaction results
- EmbedResponse: Text embedding results
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

@dataclass
class GenerateResponse:
    """Response from model generation."""
    text: str
    model: str
    finish_reason: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate response data."""
        if not self.text:
            raise ValueError("Response text cannot be empty")
        if not self.model:
            raise ValueError("Model must be specified")
        if self.finish_reason not in {None, "stop", "length", "content_filter"}:
            raise ValueError("Invalid finish_reason")

@dataclass
class GetModelsResponse:
    """Response containing available models."""
    models: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate response data."""
        if not isinstance(self.models, list):
            raise TypeError("Models must be a list")
        for model in self.models:
            if not isinstance(model, dict):
                raise TypeError("Each model must be a dictionary")
            if "id" not in model:
                raise ValueError("Each model must have an id")

@dataclass
class SystemToolResponse:
    """Response from system tool operations."""
    tool_name: str
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate response data."""
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        if self.error and not isinstance(self.error, str):
            raise TypeError("Error must be a string")

@dataclass
class SDKResponse:
    """Generic SDK response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate response data."""
        if not isinstance(self.success, bool):
            raise TypeError("Success must be a boolean")
        if not self.message:
            raise ValueError("Message cannot be empty")
        if self.error and not isinstance(self.error, str):
            raise TypeError("Error must be a string")

@dataclass
class UserResponse:
    """Response from user interaction."""
    response: str
    cancelled: bool = False
    timeout: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate response data."""
        if not self.cancelled and not self.timeout and not self.response:
            raise ValueError("Response cannot be empty unless cancelled or timed out")
        if self.cancelled and self.timeout:
            raise ValueError("Response cannot be both cancelled and timed out")

@dataclass
class EmbedResponse:
    """Response from text embedding."""
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate response data."""
        if not self.embeddings:
            raise ValueError("Embeddings cannot be empty")
        if not all(isinstance(e, list) and e and all(isinstance(v, float) for v in e) 
                  for e in self.embeddings):
            raise TypeError("Embeddings must be a list of lists of floats")
        if not self.model:
            raise ValueError("Model must be specified")
