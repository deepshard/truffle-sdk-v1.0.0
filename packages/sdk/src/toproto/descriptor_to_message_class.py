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
from typing import Any, Dict, List, Optional, Type, get_type_hints

from google.protobuf.descriptor import (
    Descriptor,
    EnumDescriptor,
    FieldDescriptor,
    FileDescriptor
)
from google.protobuf.message import Message

from .utils import (
    get_field_type,
    get_python_type,
    get_field_default,
    is_message_type,
    is_enum_type,
    get_message_fields,
    get_nested_messages,
    get_nested_enums
)

@dataclass
class FieldInfo:
    """Information about a protocol buffer field."""
    name: str
    number: int
    type: Type
    label: int = FieldDescriptor.LABEL_OPTIONAL
    default: Any = None
    message_type: Optional[Type[Message]] = None
    enum_type: Optional[Type] = None
    options: Dict[str, Any] = field(default_factory=dict)

class DescriptorToMessageClass:
    """Converts protocol buffer descriptors to Python message classes."""
    
    def __init__(self):
        self.type_registry: Dict[str, Type] = {}
        self.enum_registry: Dict[str, Type] = {}
        
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
        """Process nested message and enum types."""
        # Process nested messages
        for nested in get_nested_messages(desc):
            message_class = self._create_message_class(nested)
            self.type_registry[nested.full_name] = message_class
            
        # Process nested enums
        for enum in get_nested_enums(desc):
            enum_class = self._create_enum_class(enum)
            self.enum_registry[enum.full_name] = enum_class
            
    def _create_message_class(self, desc: Descriptor) -> Type[Message]:
        """Create a message class from a descriptor."""
        fields: Dict[str, FieldInfo] = {}
        
        # Process fields
        for field_desc in get_message_fields(desc):
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
        
    def _create_enum_class(self, desc: EnumDescriptor) -> Type:
        """Create an enum class from a descriptor."""
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
        """Create field info from a field descriptor."""
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
            python_type = get_python_type(desc.type)
            
        # Create field info
        return FieldInfo(
            name=desc.name,
            number=desc.number,
            type=python_type,
            label=desc.label,
            default=get_field_default(desc.type),
            message_type=(
                desc.message_type if desc.type == FieldDescriptor.TYPE_MESSAGE
                else None
            ),
            enum_type=(
                desc.enum_type if desc.type == FieldDescriptor.TYPE_ENUM
                else None
            ),
            options=dict(desc.options.Items()) if desc.options else {}
        )
        
    def _create_field_property(
        self,
        name: str,
        info: FieldInfo
    ) -> property:
        """Create a property for a field."""
        
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
        """Validate and convert a field value."""
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