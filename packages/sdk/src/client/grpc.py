"""
gRPC Client Implementation

Core implementation of the gRPC client for the Truffle platform:
- Secure connection management
- Request/response handling
- Error handling and retries
- Type-safe interfaces
"""

import typing
import grpc
from typing import Iterator, List, Optional, Dict, Union, Tuple

from ..platform import sdk_pb2, sdk_pb2_grpc
from .base import TruffleClient, SDK_SOCK
from .types import (
    ClientConfig,
    ModelConfig,
    ContextConfig,
    RuntimeValidator,
    ResponseValidator,
)
from .exceptions import (
    ConnectionError,
    ValidationError,
    ModelError,
    GenerationError,
)


class GRPCClient(TruffleClient):
    """gRPC implementation of the Truffle client."""
    
    def __init__(self, host: str = SDK_SOCK):
        """
        Initialize the gRPC client.
        
        Args:
            host: gRPC server address
            
        Raises:
            ConnectionError: If connection fails
            ValidationError: If client validation fails
        """
        self.config = ClientConfig(host=host)
        self.channel = grpc.insecure_channel(host)
        self.stub = sdk_pb2_grpc.TruffleStub(self.channel)
        
        # Validate client on initialization
        RuntimeValidator.validate_client(self)

    def perplexity_search(
        self,
        query: str,
        model: str = "sonar",
        response_fmt: typing.Optional[dict] = None,
        system_prompt: str = "",
    ) -> str:
        """
        Perform a perplexity search.
        
        Args:
            query: Search query
            model: Model to use
            response_fmt: Optional response format
            system_prompt: Optional system prompt
            
        Returns:
            Search response
            
        Raises:
            ValidationError: If parameters are invalid
            ConnectionError: If request fails
        """
        try:
            request = sdk_pb2.PerplexityRequest(
                query=query,
                model=model,
                system_prompt=system_prompt,
            )
            if response_fmt:
                request.response_format.update(response_fmt)
                
            response = self.stub.PerplexitySearch(request)
            
            if response.error:
                raise ValidationError(response.error)
                
            return response.response
            
        except grpc.RpcError as e:
            raise ConnectionError("Perplexity search failed", str(e))

    def get_models(self) -> List[sdk_pb2.ModelDescription]:
        """
        Get available models.
        
        Returns:
            List of model descriptions
            
        Raises:
            ConnectionError: If request fails
        """
        try:
            response = self.stub.GetModels(sdk_pb2.GetModelsRequest())
            
            # Validate each model
            models = []
            for model in response.models:
                if ResponseValidator.validate_model_response(model):
                    models.append(model)
                    
            return models
            
        except grpc.RpcError as e:
            raise ConnectionError("Failed to get models", str(e))

    def tool_update(self, message: str) -> None:
        """
        Send a tool update.
        
        Args:
            message: Update message
            
        Raises:
            ConnectionError: If update fails
        """
        try:
            self.stub.ToolUpdate(sdk_pb2.ToolUpdateRequest(message=message))
        except grpc.RpcError as e:
            raise ConnectionError("Tool update failed", str(e))

    def ask_user(
        self, 
        message: str, 
        reason: str = "Tool needs input to continue."
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Request input from the user.
        
        Args:
            message: Question to ask
            reason: Reason for asking
            
        Returns:
            User response
            
        Raises:
            ConnectionError: If request fails
        """
        try:
            request = sdk_pb2.UserRequest(
                message=message,
                reason=reason
            )
            response = self.stub.AskUser(request)
            
            if response.error:
                raise ValidationError(response.error)
                
            return {
                "response": response.response,
                "options": list(response.options)
            }
            
        except grpc.RpcError as e:
            raise ConnectionError("User request failed", str(e))

    def query_embed(
        self, 
        query: str, 
        documents: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Perform embedding query.
        
        Args:
            query: Query string
            documents: Documents to search
            
        Returns:
            List of (document, score) tuples
            
        Raises:
            ConnectionError: If request fails
            ValidationError: If response is invalid
        """
        try:
            request = sdk_pb2.EmbedRequest(
                query=query,
                documents=documents
            )
            response = self.stub.QueryEmbed(request)
            
            if not ResponseValidator.validate_embed_response(response):
                raise ValidationError("Invalid embedding response")
                
            return [(r.text, r.score) for r in response.results]
            
        except grpc.RpcError as e:
            raise ConnectionError("Embedding query failed", str(e))

    def infer(
        self,
        prompt: str,
        model_id: int = 0,
        system_prompt: Optional[str] = None,
        context_idx: Optional[int] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        format_type: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Perform model inference.
        
        Args:
            prompt: Input prompt
            model_id: Model ID to use
            system_prompt: Optional system prompt
            context_idx: Optional context index
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            format_type: Optional output format
            schema: Optional output schema
            
        Yields:
            Generated tokens
            
        Raises:
            ConnectionError: If request fails
            ValidationError: If parameters are invalid
            ModelError: If model errors occur
            GenerationError: If generation fails
        """
        # Validate configurations
        model_config = ModelConfig(
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            format_type=format_type,
            schema=schema
        )
        validate_model_config(model_config)
        
        context_config = ContextConfig(
            system_prompt=system_prompt,
            context_idx=context_idx
        )
        validate_context_config(context_config)
        
        try:
            request = sdk_pb2.GenerateRequest(
                prompt=prompt,
                model_id=model_id,
                system_prompt=system_prompt or "",
                context_idx=context_idx or 0,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if format_type:
                request.format_type = format_type
            if schema:
                request.schema = schema
                
            for response in self.stub.Generate(request):
                if response.error:
                    raise GenerationError(response.error)
                    
                if not ResponseValidator.validate_generation_response(response):
                    raise ValidationError("Invalid generation response")
                    
                if response.token:
                    yield response.token
                    
        except grpc.RpcError as e:
            raise ConnectionError("Generation failed", str(e))

    def close(self) -> None:
        """Close the client connection."""
        if self.channel:
            self.channel.close()
