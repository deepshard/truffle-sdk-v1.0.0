"""
Truffle CLI

Main entry point for the Truffle CLI application.
Provides command-line interface for creating, building, and managing Truffle apps.
"""

from .utils.logger import log
from .commands import get_app

def main() -> None:
    """Main entry point for the CLI."""
    try:
        app = get_app()
        app()
    except Exception as e:
        log.error("Unexpected error", {"Error": str(e)})
        raise SystemExit(1)

if __name__ == "__main__":
    main() 