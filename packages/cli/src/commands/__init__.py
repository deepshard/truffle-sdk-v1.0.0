"""
CLI Commands Package Initialization

This package implements the core Truffle CLI commands and functionality:
- Project initialization (init.py)
- Project building (build.py)
- Project execution (run.py)

The package uses Typer for command-line interface management and provides
a clean, modular structure for handling different CLI operations.

Dependencies:
- typer: Command-line interface framework
- pathlib: Path manipulation utilities
- platform.models: Core platform models
- utils.templates: Template management
"""

import typer

from . import init, build, run

# Create the CLI app
app = typer.Typer(
    help="Truffle CLI - Create and manage Truffle applications",
    add_completion=False,
)

# Register commands
app.command()(init.init)
app.command()(build.build)
app.command()(run.run)

def get_app() -> typer.Typer:
    """Get the CLI application instance."""
    return app
