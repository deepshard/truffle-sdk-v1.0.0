"""
Template System

This module implements the CLI template system for project initialization:
- Provides template generators for creating new Truffle projects
- Includes validation utilities for project structure
- Manages file generation and resource handling
- Supports multiple project template types
"""

from .app import generate_main_py, generate_manifest
from .validation import (
    validate_main_py,
    validate_manifest,
    validate_requirements,
)

__all__ = [
    # Generators
    "generate_main_py",
    "generate_manifest",
    
    # Validators
    "validate_main_py",
    "validate_manifest",
    "validate_requirements",
] 