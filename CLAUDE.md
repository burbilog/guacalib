# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Guacalib is a Python library and CLI tool for managing Apache Guacamole users, groups, connections, and connection groups through direct MySQL database access. The project consists of two main components:

1. **Python Library (`guacalib`)**: Programmatic access via the `GuacamoleDB` class
2. **CLI Tool (`guacaman`)**: Command-line interface for database operations

## Development Commands

### Testing
```bash
# Run all tests (requires TEST_CONFIG environment variable)
make tests

# The test suite uses bats (Bash Automated Testing System)
# Set TEST_CONFIG to point to a valid .guacaman.ini file:
export TEST_CONFIG=/home/rm/.guacaman.ini
bats -t --print-output-on-failure tests/test_guacaman.bats
```

**ATTENTION** running tests requires more than 2 minutes! Claude code will time out, if make tests is ran without working around this default time limitation.

### Building and Publishing
```bash
# Build the package
make build

# Test publish to PyPI test repository
make testpub

# Publish to PyPI
make pub

# Create version tag and push (updates README.md automatically)
make push
```

### Development Setup
```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e .[dev]

# Development dependencies include: black, flake8, pytest
```

## Code Architecture

### Core Components

#### Database Layer (`db.py`)
- **GuacamoleDB**: Main class providing database operations
- Uses MySQL connector with parameterized queries for security
- Implements context manager pattern (`__enter__`/`__exit__`)
- Contains connection and user parameter validation dictionaries

#### CLI Layer (`cli.py` and `cli_handle_*.py`)
- **Main CLI (`cli.py`)**: Argument parsing and command routing
- **Command Handlers**: Separate modules for each command group:
  - `cli_handle_user.py`: User management
  - `cli_handle_usergroup.py`: User group management  
  - `cli_handle_conn.py`: Connection management
  - `cli_handle_conngroup.py`: Connection group management
  - `cli_handle_dump.py`: Data export functionality

#### Parameter Definitions
- **`db_connection_parameters.py`**: Valid connection parameters by protocol type
- **`db_user_parameters.py`**: Valid user account parameters

### Data Model

The tool manages four main entity types:
1. **Users**: Guacamole user accounts with authentication
2. **User Groups**: Collections of users for permission management
3. **Connections**: Individual protocol connections (VNC, RDP, SSH)
4. **Connection Groups**: Hierarchical organization of connections

### Key Design Patterns

- **Command Pattern**: CLI commands separated into handler modules
- **Context Manager**: Database connections with automatic cleanup
- **Parameter Validation**: Centralized parameter definitions with validation
- **Hierarchical IDs**: Support for both name-based and ID-based entity identification

## Configuration

### Database Configuration
The tool requires a configuration file at `~/.guacaman.ini`:
```ini
[mysql]
host = localhost
user = guacamole_user
password = your_password
database = guacamole_db
```

File permissions must be 0600 (owner read/write only) for security.

## Development Guidelines

### Code Quality (from AGENTS.md)
- Write clear, readable code with meaningful names
- Add type hints to function signatures
- Use Google-style or NumPy-style docstrings
- Handle exceptions appropriately with descriptive error messages
- Follow single-responsibility principles
- Validate all user inputs and handle file paths securely

### Testing Strategy
- Uses bats (Bash Automated Testing System) for integration testing
- Tests require a live MySQL database with Guacamole schema
- Test setup creates temporary entities and cleans up afterward
- Environment variable `TEST_CONFIG` must point to test database config

## Current Development Focus

### Active Features (feature/ids branch)
- Adding `--id` parameter support for connections and connection groups
- Resolving naming ambiguity in hierarchical structures
- Enhanced list commands to always show database IDs

### Planned Improvements
- GuacamoleDB initialization without configuration file
- More granular permission management
- Custom connection parameters for different protocols
- RDP connection support in dump command

## Security Considerations

- Database credentials stored in separate configuration file with strict permissions
- All SQL queries use parameterized statements to prevent injection
- Password hashing before database storage
- Input validation on all user-provided data
- No hardcoded sensitive information in source code
