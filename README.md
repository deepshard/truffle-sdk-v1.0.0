# Truffle SDK

Core SDK and CLI tools.

## Structure

```
packages/
├── sdk/                    # Core SDK implementation
│   ├── src/
│   │   ├── client/        # Client implementations (gRPC, base)
│   │   ├── platform/      # Protocol buffer definitions
│   │   ├── tools/         # Tool management utilities
│   │   ├── toproto/       # Proto conversion utilities
│   │   └── types/         # Type definitions and validation
│   └── tests/             # SDK test suite
│
└── cli/                   # CLI implementation
    └── src/
        ├── commands/      # CLI commands (init, build, run)
        ├── utils/         # CLI utilities
        └── assets/        # Static assets
```

## Core Components

- **SDK**: `/packages/sdk/src/`
  - Client Interface & gRPC Implementation
  - Protocol Buffer Integration
  - Tool Management System
  - Type System & Validation
  - Proto Conversion Utilities

- **CLI**: `/packages/cli/src/`
  - Project Management
  - Build System
  - Runtime Environment
  - Configuration Management
  - Logging System

## Documentation

- API Documentation: `/packages/sdk/docs/`
- CLI Usage: `/packages/cli/docs/`
