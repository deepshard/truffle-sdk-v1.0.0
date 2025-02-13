"""
Base Client Implementation Module

This module implements the core TruffleClient class that provides:
- Platform API access and method implementations
- Socket configuration and management
- Context and conversation handling
- Type-safe interface to platform features
"""

import os
import json
import typing
import grpc
from ..platform import sdk_pb2, sdk_pb2_grpc

# Socket configuration
APP_SOCK = os.getenv("TRUFFLE_APP_SOCKET", "unix:///tmp/truffle_app.sock")
SDK_SOCK = os.getenv("TRUFFLE_SDK_SOCKET", "unix:///tmp/truffle_sdk.sock")
SHARED_FILES_DIR = os.getenv("TRUFFLE_SHARED_DIR", "/root/shared")  # container default 1.31.25

class TruffleClient:
    """Provides a pythonic interface to access the core functionality of the platform."""
    
    def __init__(self, host: str = SDK_SOCK):
        """Initialize the client with an optional host address."""
        self.channel = grpc.insecure_channel(host)
        self.stub = sdk_pb2_grpc.TruffleSDKStub(self.channel)
        self.model_contexts: typing.List[sdk_pb2.Context] = []

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
        """
        perplexity_models_feb24 = [
            "sonar-reasoning",  # Chat Completion - 127k context length
            "sonar-pro",        # Chat Completion - 200k 
            "sonar",            # Chat Completion - 127k 
        ]
        if model not in perplexity_models_feb24:
            raise ValueError(
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
                raise RuntimeError(f"SystemToolError: {response.error}")

            results = json.loads(response.response)
            return results["choices"][0]["message"]["content"]
        except grpc.RpcError as e:
            raise RuntimeError(f"RPC error: {e.details()}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON error: {e}")

    def get_models(self) -> typing.List[sdk_pb2.ModelDescription]:
        """Get the models which are available on the platform."""
        try:
            response = self.stub.GetModels(sdk_pb2.GetModelsRequest())
            return response.models
        except grpc.RpcError as e:
            raise RuntimeError(f"RPC error: {e.details()}")

    def tool_update(self, message: str) -> None:
        """
        Update tool status with a message.

        Args:
            message: The status message to send
        """
        try:
            response: sdk_pb2.SDKResponse = self.stub.ToolUpdate(
                sdk_pb2.ToolUpdateRequest(friendly_description=message)
            )
            if response.error:
                raise RuntimeError(f"RPC error: {response.error}")
        except grpc.RpcError as e:
            raise RuntimeError(f"RPC error: {e.details()}")

    def ask_user(
        self, 
        message: str, 
        reason: str = "Tool needs input to continue."
    ) -> typing.Dict[str, typing.Union[str, typing.List[str]]]:
        """
        Ask the user for input.

        Args:
            message: The message to display to the user
            reason: The reason for the input

        Returns:
            A dictionary with the user's response:
                - 'response': The user's response as a string
                - 'error': Optional error message if the user input failed
                - 'files': Optional list of file paths if the user uploaded files
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
            raise RuntimeError(f"RPC error: {e.details()}")

    def query_embed(
        self, 
        query: str, 
        documents: typing.List[str]
    ) -> typing.List[typing.Tuple[str, float]]:
        """
        Perform semantic search using text embeddings.

        Args:
            query: The query string
            documents: A list of document strings to search

        Returns:
            A list of (document, score) tuples sorted by cosine similarity
        """
        try:
            request = sdk_pb2.EmbedRequest(query=query, documents=documents)
            response: sdk_pb2.EmbedResponse = self.stub.Embed(request)
            
            if len(response.results) == 0:
                raise ValueError("No results returned")
                
            return [(r.text, r.score) for r in response.results]
        except grpc.RpcError as e:
            raise RuntimeError(f"Embed RPC error: {e.details()}")
        except ValueError as e:
            raise RuntimeError(f"Embed Value error: {e}")

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
        Make a streaming inference request to the TruffleSDK service.

        Args:
            prompt: The input prompt for generation
            model_id: ID of the model to use
            system_prompt: Optional system prompt for context
            context_idx: Optional index into existing conversation context
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            format_type: Optional response format (TEXT, JSON)
            schema: Optional schema for structured output

        Returns:
            Iterator yielding generated tokens
        """
        format_spec = None
        if format_type:
            format_spec = sdk_pb2.GenerateResponseFormat(
                format=sdk_pb2.GenerateResponseFormat.ResponseFormat.Value(
                    f"RESPONSE_{format_type}"
                ),
                schema=schema,
            )

        # Fetch or build the context for the chat
        if context_idx is not None:
            if context_idx is not None and system_prompt is not None:
                raise ValueError("Only pass system_prompt or context_idx, but not both!")
            current_context = self.model_contexts[context_idx]
        else:
            self.model_contexts.append(sdk_pb2.Context())
            current_context = self.model_contexts[-1]
            if system_prompt is not None:
                current_context.history.append(
                    sdk_pb2.Content(
                        role=sdk_pb2.Content.ROLE_SYSTEM,
                        content=system_prompt
                    )
                )

        current_context.history.append(
            sdk_pb2.Content(
                role=sdk_pb2.Content.Role.ROLE_USER,
                content=prompt
            )
        )

        # Create the generation request
        request = sdk_pb2.GenerateRequest(
            model_id=model_id,
            context=current_context,
            max_tokens=max_tokens,
            temperature=temperature,
            fmt=format_spec,
        )

        try:
            for response in self.stub.Infer(request):
                if response.error:
                    raise RuntimeError(f"Generation error: {response.error}")

                if response.finish_reason:
                    if response.finish_reason == sdk_pb2.GenerateFinishReason.FINISH_REASON_ERROR:
                        raise RuntimeError("Generation terminated with error")
                    break

                if response.token:
                    yield response.token

        except grpc.RpcError as e:
            raise RuntimeError(f"RPC error: {e.details()}")

    def close(self) -> None:
        """Close the gRPC channel."""
        self.channel.close()
