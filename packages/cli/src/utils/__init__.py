"""
CLI Utilities Package

This package provides core utilities for the Truffle CLI:
- Logging and output formatting
  - Configuration management
- Template generation and handling
- Project validation and verification
"""

from .logger import log, Symbols, Colors
from .config import (
    load_manifest,
    update_manifest,
    load_pyproject,
    update_pyproject,
    get_sdk_version,
    format_requirements
)
from .templates import (
    generate_main_py,
    generate_manifest,
    generate_requirements,
    copy_project_template,
    copy_default_icon
)
from .validation import (
    validate_project_structure,
    validate_manifest_json,
    validate_main_py,
    validate_requirements_txt
)

__all__ = [
    # Logger
    'log',
    'Symbols',
    'Colors',
    
    # Config
    'load_manifest',
    'update_manifest',
    'load_pyproject',
    'update_pyproject',
    'get_sdk_version',
    'format_requirements',
    
    # Templates
    'generate_main_py',
    'generate_manifest',
    'generate_requirements',
    'copy_project_template',
    'copy_default_icon',
    
    # Validation
    'validate_project_structure',
    'validate_manifest_json',
    'validate_main_py',
    'validate_requirements_txt'
]

# Package version
__version__ = "1.0.0"
