"""
Descriptor to File Converter Module

Converts protocol buffer descriptors to file content:

Features:
- Proto file generation
- Message and field formatting
- Service and RPC method handling
- Option and import management
"""

import textwrap
from typing import List

from google.protobuf.descriptor import (
    Descriptor,
    EnumDescriptor,
    FieldDescriptor,
    FileDescriptor,
    ServiceDescriptor
)

class DescriptorToFile:
    """Converts protocol buffer descriptors to file content."""
    
    def __init__(self):
        """Initialize the converter."""
        self._indent = "  "
        self._current_level = 0
        
    def convert(self, desc: FileDescriptor) -> str:
        """
        Convert a FileDescriptor to proto file content.
        
        Args:
            desc: FileDescriptor to convert
            
        Returns:
            Proto file content as string
        """
        lines = []
        
        # Add syntax
        lines.append('syntax = "proto3";\n')
        
        # Add package
        if desc.package:
            lines.append(f'package {desc.package};\n')
            
        # Add imports
        for dep in desc.dependencies:
            lines.append(f'import "{dep}";\n')
            
        # Add options
        lines.extend(self._format_options(desc.options))
            
        # Add messages
        for message in desc.message_types_by_name.values():
            lines.append(self._format_message(message))
            
        # Add enums
        for enum in desc.enum_types_by_name.values():
            lines.append(self._format_enum(enum))
            
        # Add services
        for service in desc.services_by_name.values():
            lines.append(self._format_service(service))
            
        return "\n".join(lines)
        
    def _format_message(self, desc: Descriptor, level: int = 0) -> str:
        """
        Format a message descriptor.
        
        Args:
            desc: Message descriptor
            level: Indentation level
            
        Returns:
            Formatted message string
        """
        lines = []
        indent = self._indent * level
        
        # Add message declaration
        lines.append(f"{indent}message {desc.name} {{")
            
        # Add nested types
        for nested in desc.nested_types:
            lines.append(self._format_message(nested, level + 1))
            
        # Add enums
        for enum in desc.enum_types:
            lines.append(self._format_enum(enum, level + 1))
            
        # Add fields
        for field in desc.fields:
            lines.append(self._format_field(field, level + 1))
            
        lines.append(f"{indent}}}\n")
        return "\n".join(lines)
        
    def _format_enum(self, desc: EnumDescriptor, level: int = 0) -> str:
        """
        Format an enum descriptor.
        
        Args:
            desc: Enum descriptor
            level: Indentation level
            
        Returns:
            Formatted enum string
        """
        lines = []
        indent = self._indent * level
        
        # Add enum declaration
        lines.append(f"{indent}enum {desc.name} {{")
        
        # Add values
        for value in desc.values:
            lines.append(
                f"{indent}{self._indent}{value.name} = {value.number};"
            )
                
        lines.append(f"{indent}}}\n")
        return "\n".join(lines)
        
    def _format_service(self, desc: ServiceDescriptor, level: int = 0) -> str:
        """
        Format a service descriptor.
        
        Args:
            desc: Service descriptor
            level: Indentation level
            
        Returns:
            Formatted service string
        """
        lines = []
        indent = self._indent * level
        
        # Add service declaration
        lines.append(f"{indent}service {desc.name} {{")
        
        # Add methods
        for method in desc.methods:
            lines.append(self._format_method(method, level + 1))
            
        lines.append(f"{indent}}}\n")
        return "\n".join(lines)
        
    def _format_method(self, method: ServiceDescriptor.Method, level: int) -> str:
        """
        Format a method descriptor.
        
        Args:
            method: Method descriptor
            level: Indentation level
            
        Returns:
            Formatted method string
        """
        indent = self._indent * level
        
        # Build method signature
        parts = [f"{indent}rpc {method.name}"]
        
        # Add request
        parts.append(
            f"({method.input_type.name})"
            if not method.client_streaming else
            f"(stream {method.input_type.name})"
        )
        
        # Add response
        parts.append(
            "returns"
            f" ({method.output_type.name})"
            if not method.server_streaming else
            f" (stream {method.output_type.name})"
        )
        
        # Add options
        if method.options.ListFields():
            parts.append("{")
            parts.extend(self._format_options(method.options, level + 1))
            parts.append(f"{indent}}}")
        else:
            parts.append(";")
            
        return " ".join(parts)
        
    def _format_field(self, field: FieldDescriptor, level: int) -> str:
        """
        Format a field descriptor.
        
        Args:
            field: Field descriptor
            level: Indentation level
            
        Returns:
            Formatted field string
        """
        indent = self._indent * level
        parts = []
        
        # Add label if needed
        if field.label == FieldDescriptor.LABEL_REPEATED:
            parts.append("repeated")
            
        # Add type
        if field.type == FieldDescriptor.TYPE_MESSAGE:
            parts.append(field.message_type.name)
        elif field.type == FieldDescriptor.TYPE_ENUM:
            parts.append(field.enum_type.name)
        else:
            parts.append(field.type_name)
            
        # Add name and number
        parts.extend([field.name, f"= {field.number}"])
        
        # Add options
        if field.options.ListFields():
            parts.append("[")
            option_parts = []
            for option, value in field.options.ListFields():
                option_parts.append(f"{option.name} = {value}")
            parts.append(", ".join(option_parts))
            parts.append("]")
            
        return f"{indent}{' '.join(parts)};"
            
    def _format_options(
        self,
        options,
        level: int = 0,
        inline: bool = False
    ) -> List[str]:
        """
        Format options.
        
        Args:
            options: Options to format
            level: Indentation level
            inline: Whether to format inline
            
        Returns:
            List of formatted option strings
        """
        if not options:
            return []
            
        lines = []
        indent = self._indent * level
        
        for option, value in options.ListFields():
            if inline:
                lines.append(f"{option.name} = {value}")
            else:
                lines.append(f"{indent}option {option.name} = {value};")
                
        return lines 