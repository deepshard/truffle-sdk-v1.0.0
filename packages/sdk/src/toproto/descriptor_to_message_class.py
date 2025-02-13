"""
Descriptor to Message Class Converter Module

Converts protocol buffer descriptors to Python message classes:

Features:
- Message class generation
- Field property creation
- Type validation and conversion
- Nested type handling
"""

import typing
from dataclasses import dataclass, field
from typing import Any, Type
from google.protobuf.descriptor import (
    Descriptor,
    FieldDescriptor
)
from google.protobuf.message import Message

@dataclass
class FieldInfo:
    """Information about a protocol buffer field."""
    name: str
    number: int
    type: Type
    label: int = FieldDescriptor.LABEL_OPTIONAL
    default: Any = None
    message_type: typing.Optional[Type[Message]] = None
    enum_type: typing.Optional[Type] = None
    options: typing.Dict[str, Any] = field(default_factory=dict)

class DescriptorToMessageClass:
    """Converts protocol buffer descriptors to Python message classes."""
    
    def __init__(self):
        """Initialize the converter."""
        self.type_registry: typing.Dict[str, Type] = {}
        self.enum_registry: typing.Dict[str, Type] = {}
        
    def convert(self, desc: Descriptor) -> Type[Message]:
        """
        Convert descriptor to message class.
        
        Args:
            desc: Message descriptor to convert
            
        Returns:
            Generated message class
            
        Raises:
            ValueError: If conversion fails
        """
        # Clear registries
        self.type_registry.clear()
        self.enum_registry.clear()
        
        # Process nested types first
        self._process_nested_types(desc)
        
        # Create class
        return self._create_message_class(desc)
        
    def _process_nested_types(self, desc: Descriptor) -> None:
        """
        Process nested message and enum types.
        
        Args:
            desc: Message descriptor to process
        """
        # Process nested messages
        for nested in desc.nested_types:
            message_class = self._create_message_class(nested)
            self.type_registry[nested.full_name] = message_class
            
        # Process nested enums
        for enum in desc.enum_types:
            enum_class = self._create_enum_class(enum)
            self.enum_registry[enum.full_name] = enum_class
            
    def _create_message_class(self, desc: Descriptor) -> Type[Message]:
        """
        Create a message class from a descriptor.
        
        Args:
            desc: Message descriptor
            
        Returns:
            Generated message class
        """
        fields: typing.Dict[str, FieldInfo] = {}
        
        # Process fields
        for field_desc in desc.fields:
            field_info = self._create_field_info(field_desc)
            fields[field_info.name] = field_info
            
        # Create class attributes
        attrs = {
            '__module__': desc.file.package,
            '__qualname__': desc.name,
            'DESCRIPTOR': desc,
            '_fields': fields,
        }
        
        # Add field properties
        for name, info in fields.items():
            attrs[name] = self._create_field_property(name, info)
            
        # Create class
        return type(desc.name, (Message,), attrs)
        
    def _create_enum_class(self, desc: Descriptor) -> Type:
        """
        Create an enum class from a descriptor.
        
        Args:
            desc: Enum descriptor
            
        Returns:
            Generated enum class
        """
        values = {
            value.name: value.number
            for value in desc.values
        }
        
        # Create class attributes
        attrs = {
            '__module__': desc.file.package,
            '__qualname__': desc.name,
            'DESCRIPTOR': desc,
            '_values_': values,
            **values
        }
        
        # Create class
        return type(desc.name, (), attrs)
        
    def _create_field_info(self, desc: FieldDescriptor) -> FieldInfo:
        """
        Create field info from a field descriptor.
        
        Args:
            desc: Field descriptor
            
        Returns:
            Field info instance
        """
        # Get Python type
        if desc.type == FieldDescriptor.TYPE_MESSAGE:
            python_type = self.type_registry.get(
                desc.message_type.full_name,
                Message
            )
        elif desc.type == FieldDescriptor.TYPE_ENUM:
            python_type = self.enum_registry.get(
                desc.enum_type.full_name,
                int
            )
        else:
            python_type = self._get_python_type(desc.type)
            
        # Create field info
        return FieldInfo(
            name=desc.name,
            number=desc.number,
            type=python_type,
            label=desc.label,
            default=self._get_field_default(desc.type),
            message_type=(
                desc.message_type if desc.type == FieldDescriptor.TYPE_MESSAGE
                else None
            ),
            enum_type=(
                desc.enum_type if desc.type == FieldDescriptor.TYPE_ENUM
                else None
            ),
            options=dict(desc.options.ListFields()) if desc.options else {}
        )
        
    def _create_field_property(
        self,
        name: str,
        info: FieldInfo
    ) -> property:
        """
        Create a property for a field.
        
        Args:
            name: Field name
            info: Field info
            
        Returns:
            Property descriptor
        """
        def getter(msg):
            if not hasattr(msg, f'_{name}'):
                setattr(msg, f'_{name}', info.default)
            return getattr(msg, f'_{name}')
            
        def setter(msg, value):
            # Validate type
            if info.label == FieldDescriptor.LABEL_REPEATED:
                if not isinstance(value, (list, tuple)):
                    raise TypeError(f"Field {name} must be a list")
                value = [self._validate_value(v, info) for v in value]
            else:
                value = self._validate_value(value, info)
                
            setattr(msg, f'_{name}', value)
            
        def deleter(msg):
            if hasattr(msg, f'_{name}'):
                delattr(msg, f'_{name}')
                
        return property(getter, setter, deleter)
        
    def _validate_value(self, value: Any, info: FieldInfo) -> Any:
        """
        Validate and convert a field value.
        
        Args:
            value: Value to validate
            info: Field info
            
        Returns:
            Validated value
            
        Raises:
            TypeError: If value has invalid type
            ValueError: If value is invalid
        """
        if value is None:
            if info.label == FieldDescriptor.LABEL_REQUIRED:
                raise ValueError(f"Field {info.name} is required")
            return info.default
            
        # Handle message types
        if info.message_type is not None:
            if not isinstance(value, (dict, info.type)):
                raise TypeError(
                    f"Field {info.name} must be a {info.type.__name__} or dict"
                )
            if isinstance(value, dict):
                msg = info.type()
                for k, v in value.items():
                    setattr(msg, k, v)
                return msg
            return value
            
        # Handle enum types
        if info.enum_type is not None:
            if isinstance(value, str):
                if not hasattr(info.type, value):
                    raise ValueError(
                        f"Invalid enum value '{value}' for field {info.name}"
                    )
                return getattr(info.type, value)
            if not isinstance(value, int):
                raise TypeError(f"Field {info.name} must be an integer or string")
            if value not in info.type._values_.values():
                raise ValueError(
                    f"Invalid enum value {value} for field {info.name}"
                )
            return value
            
        # Handle basic types
        try:
            return info.type(value)
        except (TypeError, ValueError) as e:
            raise TypeError(
                f"Cannot convert value '{value}' to {info.type.__name__} "
                f"for field {info.name}: {e}"
            ) 
            
    def _get_python_type(self, field_type: int) -> Type:
        """
        Get Python type for protocol buffer field type.
        
        Args:
            field_type: Field type enum value
            
        Returns:
            Python type
            
        Raises:
            ValueError: If field type is invalid
        """
        type_map = {
            FieldDescriptor.TYPE_DOUBLE: float,
            FieldDescriptor.TYPE_FLOAT: float,
            FieldDescriptor.TYPE_INT64: int,
            FieldDescriptor.TYPE_UINT64: int,
            FieldDescriptor.TYPE_INT32: int,
            FieldDescriptor.TYPE_UINT32: int,
            FieldDescriptor.TYPE_BOOL: bool,
            FieldDescriptor.TYPE_STRING: str,
            FieldDescriptor.TYPE_BYTES: bytes,
            FieldDescriptor.TYPE_MESSAGE: Message,
            FieldDescriptor.TYPE_ENUM: int,
        }
        if field_type not in type_map:
            raise ValueError(f"Unsupported field type: {field_type}")
        return type_map[field_type]
        
    def _get_field_default(self, field_type: int) -> Any:
        """
        Get default value for protocol buffer field type.
        
        Args:
            field_type: Field type enum value
            
        Returns:
            Default value
        """
        if field_type in {
            FieldDescriptor.TYPE_DOUBLE,
            FieldDescriptor.TYPE_FLOAT,
            FieldDescriptor.TYPE_INT64,
            FieldDescriptor.TYPE_UINT64,
            FieldDescriptor.TYPE_INT32,
            FieldDescriptor.TYPE_UINT32,
        }:
            return 0
            
        if field_type == FieldDescriptor.TYPE_BOOL:
            return False
            
        if field_type == FieldDescriptor.TYPE_STRING:
            return ""
            
        if field_type == FieldDescriptor.TYPE_BYTES:
            return b""
            
        if field_type == FieldDescriptor.TYPE_ENUM:
            return 0
            
        return None 