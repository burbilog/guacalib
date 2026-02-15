# CLAUDE.md

This file provides guidance to Claude Code and other AI assistants when working with code in this repository.

## Project Overview

Guacalib is a Python library and CLI tool for managing Apache Guacamole users, groups, connections, and connection groups through direct MySQL database access. The project consists of two main components:

1. **Python Library (`guacalib`)**: Programmatic access via the `GuacamoleDB` class
2. **CLI Tool (`guacaman`)**: Command-line interface for database operations

## Development Commands

### Testing

**IMPORTANT**: Tests require **at least 600 seconds (10 minutes)** timeout due to the comprehensive test suite (116 tests).

```bash
# Set TEST_CONFIG first
export TEST_CONFIG=/home/rm/.guacaman.ini

# Run all tests with timeout (REQUIRED!)
timeout 600 make tests

# Or run individual test files (faster):
bats -t --print-output-on-failure tests/test_user.bats
bats -t --print-output-on-failure tests/test_usergroup.bats
bats -t --print-output-on-failure tests/test_connection.bats
bats -t --print-output-on-failure tests/test_conngroup.bats

# SSH tunnel tests (requires SSH key setup):
# Setup: ssh-keygen -t ed25519 -f ~/.ssh/test_id_ed25519 -N ""
#        cat ~/.ssh/test_id_ed25519.pub >> ~/.ssh/authorized_keys
bats -t --print-output-on-failure tests/test_ssh_tunnel.bats
```

### Code Formatting

```bash
# Check formatting
make format-check

# Apply formatting
make format
```

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
# Activate virtual environment first
source .venv/bin/activate

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e .[dev]

# Development dependencies include: black, flake8, pytest
```

## Code Architecture

### Repository Pattern

The codebase uses the Repository pattern with a facade for backward compatibility:

```
guacalib/
├── __init__.py
├── version.py
├── db.py                           # GuacamoleDB (facade)
├── cli/
│   ├── __init__.py
│   ├── main.py                     # Entry point
│   ├── handle_user.py
│   ├── handle_usergroup.py
│   ├── handle_conn.py
│   ├── handle_conngroup.py
│   └── handle_dump.py
└── repositories/
    ├── __init__.py
    ├── base.py
    ├── connection.py
    ├── connection_group.py
    ├── connection_parameters.py   # Connection parameter definitions
    ├── user.py
    ├── usergroup.py
    └── user_parameters.py         # User parameter definitions
```

### Core Components

#### GuacamoleDB (Facade)
- Main entry point for backward compatibility
- Creates a single shared database connection
- Delegates all operations to specialized repositories
- Exposes `users`, `usergroups`, `connections`, `connection_groups` attributes for direct repository access

#### BaseGuacamoleRepository
- Abstract base class for all repositories
- Handles database connection management
- Supports external connection sharing (for facade pattern)
- Supports SSH tunnel for remote MySQL access
- Provides `debug_print()`, `read_config()`, `read_ssh_tunnel_config()`, `validate_positive_id()` utilities

#### Repository Classes
Each repository handles operations for its entity type:
- **UserRepository**: list_users, create_user, delete_existing_user, modify_user, change_user_password
- **UserGroupRepository**: list_usergroups, create_usergroup, add_user_to_usergroup, remove_user_from_usergroup
- **ConnectionRepository**: create_connection, delete_existing_connection, modify_connection, grant/revoke permissions
- **ConnectionGroupRepository**: create_connection_group, delete_connection_group, modify_connection_group_parent, permissions

#### CLI Layer
- **Main CLI (`cli/main.py`)**: Argument parsing and command routing
- **Command Handlers**: Separate modules for each command group:
  - `cli/handle_user.py`: User management
  - `cli/handle_usergroup.py`: User group management
  - `cli/handle_conn.py`: Connection management
  - `cli/handle_conngroup.py`: Connection group management
  - `cli/handle_dump.py`: Data export functionality

### Data Model

The tool manages four main entity types:
1. **Users**: Guacamole user accounts with authentication
2. **User Groups**: Collections of users for permission management
3. **Connections**: Individual protocol connections (VNC, RDP, SSH)
4. **Connection Groups**: Hierarchical organization of connections

### Key Design Patterns

- **Repository Pattern**: Each entity has its own repository class
- **Facade Pattern**: GuacamoleDB provides a unified interface
- **Context Manager**: Database connections with automatic cleanup (includes SSH tunnel)
- **Shared Connection**: All repositories use a single DB connection
- **SSH Tunnel**: Optional SSH tunnel managed at facade level for remote DB access

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

### SSH Tunnel Configuration (Optional)
For remote MySQL access through an SSH gateway, add an `[ssh_tunnel]` section:
```ini
[ssh_tunnel]
enabled = true
host = ssh-gateway.example.com
port = 22
user = ssh_username
private_key = /home/user/.ssh/id_rsa
# password = ssh_password  # alternative to private_key
# private_key_passphrase = passphrase  # if key is encrypted
```

**Environment Variables** (have priority over config file):
- `GUACALIB_SSH_TUNNEL_ENABLED` - set to "true" to enable
- `GUACALIB_SSH_TUNNEL_HOST` - SSH gateway hostname
- `GUACALIB_SSH_TUNNEL_PORT` - SSH port (default: 22)
- `GUACALIB_SSH_TUNNEL_USER` - SSH username
- `GUACALIB_SSH_TUNNEL_PASSWORD` - SSH password (if not using key)
- `GUACALIB_SSH_TUNNEL_PRIVATE_KEY` - path to SSH private key
- `GUACALIB_SSH_TUNNEL_PRIVATE_KEY_PASSPHRASE` - key passphrase (if encrypted)

**Note**: Either `password` or `private_key` is required for SSH authentication.

## Development Guidelines

### Code Style and Structure
- Use meaningful variable and function names
- Add type hints to function signatures
- Structure code in logical modules and packages
- Avoid deeply nested code structures
- Avoid global variables

### Documentation
- Write docstrings for all public functions, classes, and modules
- Use Google-style or NumPy-style docstrings consistently
- Include parameter descriptions, return types, and examples
- Update README.md when adding new features

### Code Quality
- Write code for clarity first. Prefer readable, maintainable solutions with clear names, comments where needed, and straightforward control flow
- Do not produce code-golf or overly clever one-liners unless explicitly requested
- Don't add unnecessary dependencies
- Use descriptive error messages
- Handle exceptions appropriately
- Strictly adhere to single-responsibility principles

### Security
- Never hardcode sensitive information
- Validate all user inputs
- Handle file paths securely
- Use secure default settings
- All SQL queries use parameterized statements to prevent injection
- Password hashing before database storage

### Performance
- Optimize for readability first, then performance
- Comment any non-obvious optimizations
- Consider memory usage for large data operations

### Testing Strategy
- Uses bats (Bash Automated Testing System) for integration testing
- Tests are split into specialized files by feature (user, connection, conngroup, etc.)
- Tests require a live MySQL database with Guacamole schema
- Test setup creates temporary entities and cleans up afterward
- Environment variable `TEST_CONFIG` must point to test database config
- **Always use timeout >= 600 seconds when running tests**

## When Suggesting Changes
- Explain the reasoning behind proposed changes
- Offer complete solutions, not partial fixes
- Respect the existing architecture

## When Reviewing Code
- Check for issues such as rule violations, deviations from best practices, design patterns, or security concerns
- Document findings for follow-up sessions to iteratively address each issue
