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
from typing import Dict, List, Optional, Set
from google.protobuf.descriptor import (
    Descriptor,
    EnumDescriptor,
    FieldDescriptor,
    FileDescriptor,
    ServiceDescriptor
)

from .utils import (
    camel_to_snake,
    get_field_type,
    get_message_fields,
    get_nested_messages,
    get_nested_enums,
    get_package_name
)

class DescriptorToFile:
    """Converts protocol buffer descriptors to .proto file content."""
    
    def __init__(self):
        self.indent = "  "
        self.imports: Set[str] = set()
        self.package = ""
        
    def convert(self, desc: FileDescriptor) -> str:
        """
        Convert file descriptor to .proto file content.
        
        Args:
            desc: File descriptor to convert
            
        Returns:
            Proto file content
        """
        self.imports.clear()
        self.package = get_package_name(desc)
        
        # Build content
        content = []
        
        # Add syntax
        content.append('syntax = "proto3";\n')
        
        # Add package
        if self.package:
            content.append(f'package {self.package};\n')
            
        # Add imports
        if self.imports:
            content.extend(f'import "{imp}";' for imp in sorted(self.imports))
            content.append("")
            
        # Add options
        if desc.options:
            content.extend(self._format_options(desc.options))
            content.append("")
            
        # Add messages
        for message in desc.message_types_by_name.values():
            content.append(self._format_message(message))
            content.append("")
            
        # Add enums
        for enum in desc.enum_types_by_name.values():
            content.append(self._format_enum(enum))
            content.append("")
            
        # Add services
        for service in desc.services_by_name.values():
            content.append(self._format_service(service))
            content.append("")
            
        return "\n".join(content).strip() + "\n"
        
    def _format_message(self, desc: Descriptor, level: int = 0) -> str:
        """Format a message descriptor."""
        indent = self.indent * level
        content = []
        
        # Message declaration
        content.append(f"{indent}message {desc.name} {{")
        
        # Reserved fields
        if desc.reserved_ranges:
            ranges = [f"{r.start}" if r.start == r.end else f"{r.start} to {r.end}"
                     for r in desc.reserved_ranges]
            content.append(f"{indent}{self.indent}reserved {', '.join(ranges)};")
            
        if desc.reserved_names:
            names = [f'"{name}"' for name in desc.reserved_names]
            content.append(f"{indent}{self.indent}reserved {', '.join(names)};")
            
        # Nested enums
        for enum in get_nested_enums(desc):
            content.append("")
            content.append(self._format_enum(enum, level + 1))
            
        # Nested messages
        for nested in get_nested_messages(desc):
            content.append("")
            content.append(self._format_message(nested, level + 1))
            
        # Fields
        if desc.fields:
            if desc.reserved_ranges or desc.reserved_names or get_nested_enums(desc) or get_nested_messages(desc):
                content.append("")
                
        for field in get_message_fields(desc):
            content.append(self._format_field(field, level + 1))
            
        # Close message
        content.append(f"{indent}}}")
        return "\n".join(content)
        
    def _format_enum(self, desc: EnumDescriptor, level: int = 0) -> str:
        """Format an enum descriptor."""
        indent = self.indent * level
        content = []
        
        # Enum declaration
        content.append(f"{indent}enum {desc.name} {{")
        
        # Options
        if desc.options:
            content.extend(self._format_options(desc.options, level + 1))
            
        # Values
        for value in desc.values:
            if value.options:
                opts = self._format_options(value.options, 0, inline=True)
                content.append(f"{indent}{self.indent}{value.name} = {value.number} {opts};")
            else:
                content.append(f"{indent}{self.indent}{value.name} = {value.number};")
                
        # Close enum
        content.append(f"{indent}}}")
        return "\n".join(content)
        
    def _format_service(self, desc: ServiceDescriptor, level: int = 0) -> str:
        """Format a service descriptor."""
        indent = self.indent * level
        content = []
        
        # Service declaration
        content.append(f"{indent}service {desc.name} {{")
        
        # Options
        if desc.options:
            content.extend(self._format_options(desc.options, level + 1))
            
        # Methods
        for method in desc.methods:
            content.append("")
            content.append(self._format_method(method, level + 1))
            
        # Close service
        content.append(f"{indent}}}")
        return "\n".join(content)
        
    def _format_method(self, method: ServiceDescriptor.Method, level: int) -> str:
        """Format a method descriptor."""
        indent = self.indent * level
        content = []
        
        # Method signature
        input_type = method.input_type.name
        output_type = method.output_type.name
        
        if method.client_streaming:
            input_type = f"stream {input_type}"
        if method.server_streaming:
            output_type = f"stream {output_type}"
            
        content.append(
            f"{indent}rpc {method.name} ({input_type}) returns ({output_type})"
        )
        
        # Method options
        if method.options:
            content[-1] = content[-1] + " {"
            content.extend(self._format_options(method.options, level + 1))
            content.append(f"{indent}}}")
        else:
            content[-1] = content[-1] + ";"
            
        return "\n".join(content)
        
    def _format_field(self, field: FieldDescriptor, level: int) -> str:
        """Format a field descriptor."""
        indent = self.indent * level
        
        # Field type
        if field.type == FieldDescriptor.TYPE_MESSAGE:
            field_type = field.message_type.name
        elif field.type == FieldDescriptor.TYPE_ENUM:
            field_type = field.enum_type.name
        else:
            field_type = field.type_name.lower()
            
        # Field label
        if field.label == FieldDescriptor.LABEL_REPEATED:
            label = "repeated "
        else:
            label = ""
            
        # Field options
        if field.options:
            opts = self._format_options(field.options, 0, inline=True)
            return f"{indent}{label}{field_type} {field.name} = {field.number} {opts};"
        else:
            return f"{indent}{label}{field_type} {field.name} = {field.number};"
            
    def _format_options(
        self,
        options,
        level: int = 0,
        inline: bool = False
    ) -> List[str]:
        """Format options."""
        indent = self.indent * level if not inline else ""
        content = []
        
        for name, value in sorted(options.Items()):
            if inline:
                content.append(f"[{name} = {value}]")
            else:
                content.append(f"{indent}option {name} = {value};")
                
        return content 