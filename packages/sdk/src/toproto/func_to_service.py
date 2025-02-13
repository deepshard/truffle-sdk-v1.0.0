"""
Function to Service Converter

Core implementation of Python function to gRPC service conversion:

Features:
- Service and method generation
- Class and function parsing
- Stream handling support
- gRPC descriptor creation
"""

import typing
import inspect
from dataclasses import dataclass
from google.protobuf.descriptor import ServiceDescriptor, MethodDescriptor

from .converter_base import ConverterBase, ProtoService, ProtoMethod
from .func_to_proto import FunctionConverter, FunctionSpec
from ..client.exceptions import ValidationError

@dataclass
class ServiceSpec:
    """Service specification for gRPC generation."""
    name: str
    methods: typing.List[FunctionSpec]
    docstring: str = ""

class ServiceConverter(FunctionConverter):
    """Converter for Python functions to gRPC services."""
    
    def __init__(self):
        """Initialize the service converter."""
        super().__init__()
        self._services: typing.Dict[str, ServiceSpec] = {}

    def parse_service(
        self,
        cls: typing.Type,
        service_name: str = None
    ) -> ServiceSpec:
        """Parse a class into a ServiceSpec."""
        # Get service name
        name = service_name or cls.__name__
        
        # Get docstring
        doc = inspect.getdoc(cls) or ""
        
        # Get methods
        methods = []
        for method_name, method in inspect.getmembers(cls, inspect.isfunction):
            if not method_name.startswith("_"):
                try:
                    methods.append(self.parse_function(method))
                except ValidationError:
                    # Skip methods without proper type annotations
                    continue
        
        return ServiceSpec(
            name=name,
            methods=methods,
            docstring=doc,
        )

    def create_service_from_functions(
        self,
        functions: typing.List[typing.Callable],
        service_name: str
    ) -> ProtoService:
        """Create a service from a list of functions."""
        methods = []
        
        for func in functions:
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
            methods.append(method)
        
        return ProtoService(name=service_name, methods=methods)

    def create_service_from_class(
        self,
        cls: typing.Type,
        service_name: str = None
    ) -> ProtoService:
        """Create a service from a class."""
        # Parse service
        service_spec = self.parse_service(cls, service_name)
        
        methods = []
        for method_spec in service_spec.methods:
            # Create request/response messages
            request_msg = self.create_request_message(method_spec)
            response_msg = self.create_response_message(method_spec)
            
            # Add messages
            self.add_message(request_msg)
            self.add_message(response_msg)
            
            # Create method
            method = ProtoMethod(
                name=method_spec.name,
                input_type=request_msg.name,
                output_type=response_msg.name,
                client_streaming=False,
                server_streaming=method_spec.is_generator,
            )
            methods.append(method)
        
        return ProtoService(name=service_spec.name, methods=methods)

    def create_service_descriptor(
        self,
        service: ProtoService,
        package: str = ""
    ) -> ServiceDescriptor:
        """Create a ServiceDescriptor from a ProtoService."""
        # Create methods
        methods = []
        for method in service.methods:
            method_desc = self.create_method_descriptor(method, None)  # Parent set later
            methods.append(method_desc)
        
        # Create service descriptor
        full_name = f"{package}.{service.name}" if package else service.name
        desc = ServiceDescriptor(
            name=service.name,
            full_name=full_name,
            index=0,
            methods=methods,
            options=None,
        )
        
        # Set parent service for methods
        for method in methods:
            method.containing_service = desc
        
        return desc

    def to_grpc(self) -> str:
        """Convert all definitions to a gRPC service file string."""
        output = []
        
        # Add syntax
        output.append('syntax = "proto3";\n')
        
        # Add package
        if self._package:
            output.append(f'package {self._package};\n')
        
        # Add messages
        for message in self._messages.values():
            desc = self.create_message_descriptor(message, self._package)
            output.append(str(desc))
        
        # Add services
        for service in self._services.values():
            desc = self.create_service_descriptor(service, self._package)
            output.append(str(desc))
        
        return "\n".join(output) 