"""
Proto Converter Base

Core implementation of the base converter class for proto generation:

Features:
- Type system for Python to proto conversion
- Message and field descriptor generation
- Service and method descriptor creation
- Proto file generation utilities
"""

import typing
import inspect
from dataclasses import dataclass
from google.protobuf import descriptor_pb2
from google.protobuf.descriptor import (
    Descriptor,
    FieldDescriptor,
    ServiceDescriptor,
    MethodDescriptor,
)

from ..platform import sdk_pb2
from ..client.exceptions import ValidationError

@dataclass
class ProtoField:
    """Field definition for proto generation."""
    name: str
    type: typing.Type
    label: int = FieldDescriptor.LABEL_OPTIONAL
    number: int = None
    default_value: typing.Any = None
    message_type: typing.Optional[Descriptor] = None
    enum_type: typing.Optional[Descriptor] = None

@dataclass
class ProtoMessage:
    """Message definition for proto generation."""
    name: str
    fields: typing.List[ProtoField]
    nested_types: typing.List['ProtoMessage'] = None
    enum_types: typing.List[Descriptor] = None

@dataclass
class ProtoMethod:
    """Method definition for proto generation."""
    name: str
    input_type: typing.Union[str, Descriptor]
    output_type: typing.Union[str, Descriptor]
    client_streaming: bool = False
    server_streaming: bool = False

@dataclass
class ProtoService:
    """Service definition for proto generation."""
    name: str
    methods: typing.List[ProtoMethod]

class ConverterBase:
    """Base class for proto conversion."""
    
    def __init__(self):
        """Initialize the converter."""
        self._type_map = {
            str: FieldDescriptor.TYPE_STRING,
            int: FieldDescriptor.TYPE_INT32,
            float: FieldDescriptor.TYPE_FLOAT,
            bool: FieldDescriptor.TYPE_BOOL,
            bytes: FieldDescriptor.TYPE_BYTES,
        }
        self._messages: typing.Dict[str, ProtoMessage] = {}
        self._services: typing.Dict[str, ProtoService] = {}
        self._package: str = ""

    def set_package(self, package: str) -> None:
        """Set the proto package name."""
        self._package = package

    def add_message(self, message: ProtoMessage) -> None:
        """Add a message definition."""
        if message.name in self._messages:
            raise ValidationError(f"Message {message.name} already exists")
        self._messages[message.name] = message

    def add_service(self, service: ProtoService) -> None:
        """Add a service definition."""
        if service.name in self._services:
            raise ValidationError(f"Service {service.name} already exists")
        self._services[service.name] = service

    def get_field_type(self, python_type: typing.Type) -> int:
        """Get the proto field type for a Python type."""
        if python_type in self._type_map:
            return self._type_map[python_type]
        if inspect.isclass(python_type) and python_type.__name__ in self._messages:
            return FieldDescriptor.TYPE_MESSAGE
        raise ValidationError(f"Unsupported type: {python_type}")

    def create_field_descriptor(
        self,
        field: ProtoField,
        containing_type: Descriptor = None
    ) -> FieldDescriptor:
        """Create a FieldDescriptor from a ProtoField."""
        options = descriptor_pb2.FieldOptions()
        
        field_type = self.get_field_type(field.type)
        field_number = field.number or len(containing_type.fields) + 1
        
        return FieldDescriptor(
            name=field.name,
            full_name=f"{containing_type.full_name}.{field.name}" if containing_type else field.name,
            index=field_number - 1,
            number=field_number,
            type=field_type,
            cpp_type=None,  # Set by proto compiler
            label=field.label,
            default_value=field.default_value,
            message_type=field.message_type,
            enum_type=field.enum_type,
            containing_type=containing_type,
            is_extension=False,
            extension_scope=None,
            options=options,
        )

    def create_message_descriptor(
        self,
        message: ProtoMessage,
        package: str = ""
    ) -> Descriptor:
        """Create a Descriptor from a ProtoMessage."""
        options = descriptor_pb2.MessageOptions()
        
        full_name = f"{package}.{message.name}" if package else message.name
        desc = Descriptor(
            name=message.name,
            full_name=full_name,
            filename=None,
            containing_type=None,
            fields=[],
            nested_types=[],
            enum_types=[],
            extensions=[],
            options=options,
        )
        
        # Add fields
        for field in message.fields:
            field_desc = self.create_field_descriptor(field, desc)
            desc.fields.append(field_desc)
        
        # Add nested types
        if message.nested_types:
            for nested in message.nested_types:
                nested_desc = self.create_message_descriptor(nested, full_name)
                desc.nested_types.append(nested_desc)
        
        # Add enum types
        if message.enum_types:
            desc.enum_types.extend(message.enum_types)
        
        return desc

    def create_method_descriptor(
        self,
        method: ProtoMethod,
        service_desc: ServiceDescriptor
    ) -> MethodDescriptor:
        """Create a MethodDescriptor from a ProtoMethod."""
        options = descriptor_pb2.MethodOptions()
        
        return MethodDescriptor(
            name=method.name,
            full_name=f"{service_desc.full_name}.{method.name}",
            index=len(service_desc.methods),
            containing_service=service_desc,
            input_type=method.input_type,
            output_type=method.output_type,
            client_streaming=method.client_streaming,
            server_streaming=method.server_streaming,
            options=options,
        )

    def create_service_descriptor(
        self,
        service: ProtoService,
        package: str = ""
    ) -> ServiceDescriptor:
        """Create a ServiceDescriptor from a ProtoService."""
        options = descriptor_pb2.ServiceOptions()
        
        full_name = f"{package}.{service.name}" if package else service.name
        desc = ServiceDescriptor(
            name=service.name,
            full_name=full_name,
            index=0,
            options=options,
            methods=[],
        )
        
        # Add methods
        for method in service.methods:
            method_desc = self.create_method_descriptor(method, desc)
            desc.methods.append(method_desc)
        
        return desc

    def to_proto(self) -> str:
        """Convert all definitions to a proto file string."""
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