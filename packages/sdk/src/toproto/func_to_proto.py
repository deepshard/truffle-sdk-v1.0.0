"""
Function to Proto Converter

Core implementation of Python function to protobuf message conversion:

Features:
- Function signature analysis and parsing
- Request/response message generation
- Type annotation handling and validation
- Async and generator function support
"""

import typing
import inspect
from dataclasses import dataclass
from google.protobuf.descriptor import FieldDescriptor

from .converter_base import (
    ConverterBase,
    ProtoField,
    ProtoMessage,
    ProtoMethod,
    ProtoService,
)
from ..client.exceptions import ValidationError

@dataclass
class FunctionSpec:
    """Function specification for proto generation."""
    name: str
    args: typing.Dict[str, typing.Type]
    return_type: typing.Type
    docstring: str = ""
    is_async: bool = False
    is_generator: bool = False

class FunctionConverter(ConverterBase):
    """Converter for Python functions to proto definitions."""
    
    def __init__(self):
        """Initialize the function converter."""
        super().__init__()
        self._type_map.update({
            typing.List: FieldDescriptor.TYPE_REPEATED,
            typing.Dict: FieldDescriptor.TYPE_MESSAGE,
            typing.Optional: FieldDescriptor.TYPE_OPTIONAL,
        })

    def parse_function(self, func: typing.Callable) -> FunctionSpec:
        """Parse a function into a FunctionSpec."""
        # Get signature
        sig = inspect.signature(func)
        
        # Get docstring
        doc = inspect.getdoc(func) or ""
        
        # Get return type
        return_type = sig.return_annotation
        if return_type is inspect.Signature.empty:
            raise ValidationError(f"Function {func.__name__} must have return type annotation")
        
        # Get arguments
        args = {}
        for name, param in sig.parameters.items():
            if param.annotation is inspect.Parameter.empty:
                raise ValidationError(f"Argument {name} must have type annotation")
            args[name] = param.annotation
        
        # Check if async
        is_async = inspect.iscoroutinefunction(func)
        
        # Check if generator
        is_generator = inspect.isgeneratorfunction(func)
        
        return FunctionSpec(
            name=func.__name__,
            args=args,
            return_type=return_type,
            docstring=doc,
            is_async=is_async,
            is_generator=is_generator,
        )

    def _get_field_type_from_annotation(
        self,
        annotation: typing.Type
    ) -> typing.Tuple[typing.Type, int]:
        """Get the proto field type from a type annotation."""
        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)
        
        if origin is None:
            return annotation, FieldDescriptor.LABEL_OPTIONAL
        
        if origin is typing.Union and type(None) in args:
            # Optional type
            return args[0], FieldDescriptor.LABEL_OPTIONAL
        
        if origin is list:
            # Repeated field
            return args[0], FieldDescriptor.LABEL_REPEATED
        
        if origin is dict:
            # Map field
            key_type, value_type = args
            if key_type is not str:
                raise ValidationError("Dict keys must be strings")
            return value_type, FieldDescriptor.LABEL_REPEATED
        
        raise ValidationError(f"Unsupported type annotation: {annotation}")

    def create_message_from_type(
        self,
        type_hint: typing.Type,
        name: str
    ) -> ProtoMessage:
        """Create a ProtoMessage from a type hint."""
        if hasattr(type_hint, "__annotations__"):
            # Create message from dataclass or similar
            fields = []
            for field_name, field_type in type_hint.__annotations__.items():
                base_type, label = self._get_field_type_from_annotation(field_type)
                fields.append(ProtoField(
                    name=field_name,
                    type=base_type,
                    label=label,
                ))
            return ProtoMessage(name=name, fields=fields)
        else:
            # Create message from simple type
            return ProtoMessage(
                name=name,
                fields=[ProtoField(name="value", type=type_hint)],
            )

    def create_request_message(
        self,
        func_spec: FunctionSpec
    ) -> ProtoMessage:
        """Create a request message from a function spec."""
        fields = []
        for arg_name, arg_type in func_spec.args.items():
            base_type, label = self._get_field_type_from_annotation(arg_type)
            fields.append(ProtoField(
                name=arg_name,
                type=base_type,
                label=label,
            ))
        return ProtoMessage(
            name=f"{func_spec.name}Request",
            fields=fields,
        )

    def create_response_message(
        self,
        func_spec: FunctionSpec
    ) -> ProtoMessage:
        """Create a response message from a function spec."""
        base_type, label = self._get_field_type_from_annotation(func_spec.return_type)
        return ProtoMessage(
            name=f"{func_spec.name}Response",
            fields=[ProtoField(
                name="result",
                type=base_type,
                label=label,
            )],
        )

    def function_to_service(
        self,
        func: typing.Callable,
        service_name: str = None
    ) -> ProtoService:
        """Convert a function to a proto service."""
        # Parse function
        func_spec = self.parse_function(func)
        
        # Create request/response messages
        request_msg = self.create_request_message(func_spec)
        response_msg = self.create_response_message(func_spec)
        
        # Add messages
        self.add_message(request_msg)
        self.add_message(response_msg)
        
        # Create method
        method = ProtoMethod(
            name=func_spec.name,
            input_type=request_msg.name,
            output_type=response_msg.name,
            client_streaming=False,
            server_streaming=func_spec.is_generator,
        )
        
        # Create service
        service_name = service_name or f"{func_spec.name}Service"
        return ProtoService(name=service_name, methods=[method]) 