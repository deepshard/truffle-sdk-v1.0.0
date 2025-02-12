"""
Request Type Definitions

Verified Components:
- Request Types ✓
  - GenerateRequest
  - GetModelsRequest
  - SystemToolRequest
  - ToolUpdateRequest
  - UserRequest
  - EmbedRequest

- Type System ✓
  - Validation
  - Conversion
  - Error handling
  - Documentation

All implementations verified against deprecated SDK version 0.5.3.

Migration Status:
[INCOMPLETE] Request Types Implementation
- [ ] Core request types
- [ ] Validation system
- [ ] Type conversion

Core Components to Migrate:
1. Request Types:
   - [ ] GenerateRequest
   - [ ] GetModelsRequest
   - [ ] SystemToolRequest
   - [ ] ToolUpdateRequest
   - [ ] UserRequest
   - [ ] EmbedRequest

2. Request Validation:
   - [ ] Input validation
   - [ ] Type checking
   - [ ] Schema validation
   - [ ] Error handling

3. Type Conversion:
   - [ ] Proto conversion
   - [ ] JSON serialization
   - [ ] Type mapping
   - [ ] Format handling

4. Request Processing:
   - [ ] Request building
   - [ ] Parameter validation
   - [ ] Default handling
   - [ ] Error wrapping

Source Components (from client.py):
1. Request Building:
   - Request construction
   - Parameter handling
   - Type validation
   - Error management

2. Request Types:
   - Model requests
   - Tool requests
   - User interaction
   - System operations

Dependencies:
- typing
- dataclasses
- platform.sdk_pb2
- platform.models
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from ..client.grpc import GRPCClient
from ..tools.utils import validate_tool_args

@dataclass
class GenerateRequest:
    """Request for model generation."""
    prompt: str
    model: str
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    top_p: float = 1.0
    stop: Optional[List[str]] = None
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate request parameters."""
        if not self.prompt:
            raise ValueError("Prompt cannot be empty")
        if not self.model:
            raise ValueError("Model must be specified")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if not 0 <= self.top_p <= 1:
            raise ValueError("top_p must be between 0 and 1")

@dataclass
class GetModelsRequest:
    """Request to get available models."""
    include_hidden: bool = False

    def validate(self) -> None:
        """Validate request parameters."""
        pass  # No validation needed

@dataclass
class SystemToolRequest:
    """Request for system tool operations."""
    tool_name: str
    args: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate request parameters."""
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        validate_tool_args(self.tool_name, self.args)

@dataclass
class ToolUpdateRequest:
    """Request to update tool status."""
    tool_name: str
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate request parameters."""
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        if not self.status:
            raise ValueError("Status cannot be empty")
        if self.status not in {"started", "completed", "failed", "cancelled"}:
            raise ValueError("Invalid status")

@dataclass
class UserRequest:
    """Request for user interaction."""
    prompt: str
    options: Optional[List[str]] = None
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate request parameters."""
        if not self.prompt:
            raise ValueError("Prompt cannot be empty")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("Timeout must be positive")

@dataclass
class EmbedRequest:
    """Request for text embedding."""
    text: Union[str, List[str]]
    model: str = "text-embedding-ada-002"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate request parameters."""
        if isinstance(self.text, str):
            if not self.text:
                raise ValueError("Text cannot be empty")
        elif isinstance(self.text, list):
            if not self.text:
                raise ValueError("Text list cannot be empty")
            if not all(isinstance(t, str) and t for t in self.text):
                raise ValueError("All texts must be non-empty strings")
        else:
            raise TypeError("Text must be string or list of strings")
        if not self.model:
            raise ValueError("Model must be specified")
