"""
gRPC Client Implementation Module

This module implements the gRPC client for the Truffle SDK, providing:
- Secure and efficient platform communication
- Streaming inference and response handling
- Error handling and recovery
- Socket and channel management
"""

import os
import json
import typing
import grpc
from pathlib import Path

from ..platform import sdk_pb2, sdk_pb2_grpc
from .base import TruffleClient
from .exceptions import (
    ConnectionError,
    RPCError,
    ValidationError,
    ModelError,
    GenerationError,
    ContextError,
    ToolError,
    ResponseError,
    ConfigurationError
)

# Socket configuration
APP_SOCK = os.getenv("TRUFFLE_APP_SOCKET", "unix:///tmp/truffle_app.sock")
SDK_SOCK = os.getenv("TRUFFLE_SDK_SOCKET", "unix:///tmp/truffle_sdk.sock")
SHARED_FILES_DIR = os.getenv("TRUFFLE_SHARED_DIR", "/root/shared")

class GRPCClient(TruffleClient):
    """gRPC implementation of the Truffle client interface."""
    
    def __init__(self, host: str = SDK_SOCK):
        """
        Initialize the gRPC client.
        
        Args:
            host: The socket address to connect to
            
        Raises:
            ConnectionError: If connection fails
        """
        try:
            self.channel = grpc.insecure_channel(host)
            self.stub = sdk_pb2_grpc.TruffleSDKStub(self.channel)
            self.model_contexts: typing.List[sdk_pb2.Context] = []
        except grpc.RpcError as e:
            raise ConnectionError("Failed to initialize gRPC client", e.details())
    
    def perplexity_search(
        self,
        query: str,
        model: str = "sonar",
        response_fmt: typing.Optional[dict] = None,
        system_prompt: str = "",
    ) -> str:
        """
        Perform a search using the Perplexity API.
        
        Args:
            query: The search query
            model: The model to use (sonar, sonar-pro, sonar-reasoning)
            response_fmt: Optional response format specification
            system_prompt: Optional system prompt for context
            
        Returns:
            The search response text
            
        Raises:
            ValidationError: If model is invalid
            ToolError: If search fails
            RPCError: If RPC call fails
        """
        perplexity_models_feb24 = [
            "sonar-reasoning",  # Chat Completion - 127k context length
            "sonar-pro",        # Chat Completion - 200k 
            "sonar",            # Chat Completion - 127k 
        ]
        if model not in perplexity_models_feb24:
            raise ValidationError(
                f"Model '{model}' not found in available models [{perplexity_models_feb24}]. "
                "See https://docs.perplexity.ai/guides/model-cards"
            )

        PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
        }
        if response_fmt is not None:
            payload["response_format"] = response_fmt

        try:
            request = sdk_pb2.SystemToolRequest(tool_name="perplexity_search")
            request.args["url"] = PERPLEXITY_API_URL
            request.args["payload"] = json.dumps(payload)

            response: sdk_pb2.SystemToolResponse = self.stub.SystemTool(request)
            if response.error:
                raise ToolError("perplexity_search", response.error)

            results = json.loads(response.response)
            return results["choices"][0]["message"]["content"]
        except grpc.RpcError as e:
            raise RPCError.from_grpc_error("perplexity_search", e)
        except json.JSONDecodeError as e:
            raise ResponseError(f"Failed to parse search response: {e}")
    
    def get_models(self) -> typing.List[sdk_pb2.ModelDescription]:
        """
        Get available platform models.
        
        Returns:
            List of model descriptions
            
        Raises:
            RPCError: If RPC call fails
        """
        try:
            response = self.stub.GetModels(sdk_pb2.GetModelsRequest())
            return response.models
        except grpc.RpcError as e:
            raise RPCError.from_grpc_error("get_models", e)
    
    def tool_update(self, message: str) -> None:
        """
        Update tool status.
        
        Args:
            message: Status message
            
        Raises:
            RPCError: If RPC call fails
            ToolError: If update fails
        """
        try:
            response: sdk_pb2.SDKResponse = self.stub.ToolUpdate(
                sdk_pb2.ToolUpdateRequest(friendly_description=message)
            )
            if response.error:
                raise ToolError("tool_update", response.error)
        except grpc.RpcError as e:
            raise RPCError.from_grpc_error("tool_update", e)
    
    def ask_user(
        self, 
        message: str, 
        reason: str = "Tool needs input to continue."
    ) -> typing.Dict[str, typing.Union[str, typing.List[str]]]:
        """
        Request user input.
        
        Args:
            message: Message to display
            reason: Reason for input request
            
        Returns:
            Dict with response, optional error, and optional files
            
        Raises:
            RPCError: If RPC call fails
        """
        try:
            response: sdk_pb2.UserResponse = self.stub.AskUser(
                sdk_pb2.UserRequest(message=message, reason=reason)
            )
            ret = {"response": response.response}
            if response.HasField("error"):
                ret["error"] = response.error
            if response.HasField("attached_files") and len(response.attached_files):
                ret["files"] = list(response.attached_files)
            return ret
        except grpc.RpcError as e:
            raise RPCError.from_grpc_error("ask_user", e)
    
    def query_embed(
        self, 
        query: str, 
        documents: typing.List[str]
    ) -> typing.List[typing.Tuple[str, float]]:
        """
        Perform semantic search.
        
        Args:
            query: Search query
            documents: Documents to search
            
        Returns:
            List of (document, score) tuples
            
        Raises:
            RPCError: If RPC call fails
            ValidationError: If no results
        """
        try:
            request = sdk_pb2.EmbedRequest(query=query, documents=documents)
            response: sdk_pb2.EmbedResponse = self.stub.Embed(request)
            
            if len(response.results) == 0:
                raise ValidationError("No embedding results returned")
                
            return [(r.text, r.score) for r in response.results]
        except grpc.RpcError as e:
            raise RPCError.from_grpc_error("query_embed", e)
    
    def infer(
        self,
        prompt: str,
        model_id: int = 0,
        system_prompt: typing.Optional[str] = None,
        context_idx: typing.Optional[int] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        format_type: typing.Optional[str] = None,
        schema: typing.Optional[str] = None,
    ) -> typing.Iterator[str]:
        """
        Make streaming inference request.
        
        Args:
            prompt: Input prompt
            model_id: Model ID
            system_prompt: Optional system prompt
            context_idx: Optional context index
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            format_type: Optional response format
            schema: Optional schema
            
        Returns:
            Token iterator
            
        Raises:
            RPCError: If RPC call fails
            ValidationError: If parameters invalid
            GenerationError: If generation fails
            ContextError: If context invalid
        """
        # Validate parameters
        if temperature < 0.0 or temperature > 1.0:
            raise ValidationError("Temperature must be between 0.0 and 1.0")
            
        if max_tokens < 1:
            raise ValidationError("max_tokens must be positive")
            
        if context_idx is not None and (
            context_idx < 0 or context_idx >= len(self.model_contexts)
        ):
            raise ContextError("Invalid context index")
            
        # Setup format spec
        format_spec = None
        if format_type:
            try:
                format_spec = sdk_pb2.GenerateResponseFormat(
                    format=sdk_pb2.GenerateResponseFormat.ResponseFormat.Value(
                        f"RESPONSE_{format_type}"
                    ),
                    schema=schema,
                )
            except ValueError:
                raise ValidationError(f"Invalid format type: {format_type}")
        
        # Create request
        request = sdk_pb2.GenerateRequest(
            prompt=prompt,
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if system_prompt:
            request.system_prompt = system_prompt
            
        if context_idx is not None:
            request.context.CopyFrom(self.model_contexts[context_idx])
            
        if format_spec:
            request.format.CopyFrom(format_spec)
        
        # Make streaming request
        try:
            for response in self.stub.Generate(request):
                if response.HasField("error"):
                    raise GenerationError(
                        response.error,
                        response.finish_reason if response.HasField("finish_reason") else None
                    )
                    
                if response.HasField("context"):
                    self.model_contexts.append(response.context)
                    
                if response.HasField("text"):
                    yield response.text
                    
        except grpc.RpcError as e:
            raise RPCError.from_grpc_error("infer", e)
    
    def close(self) -> None:
        """
        Close the gRPC channel.
        
        Raises:
            RPCError: If close fails
        """
        try:
            self.channel.close()
        except grpc.RpcError as e:
            raise RPCError.from_grpc_error("close", e)
