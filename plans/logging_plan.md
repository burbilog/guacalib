# Logging Implementation Plan for Guacalib

## Overview

This plan outlines the implementation of Python's built-in logging framework to replace internal diagnostic `print()` statements while preserving user-facing CLI output. The goal is to separate concerns between structured CLI output and internal diagnostics, improve configurability, and make the library more suitable for downstream users.

## Current State Analysis

Based on code analysis, the following patterns are currently used:

1. **User-facing output**: `print()` calls for CLI results, YAML dumps, command results
2. **Internal diagnostics**: `debug_print()` method in GuacamoleDB class, `print()` statements in error paths
3. **Debug information**: Controlled by `--debug` flag in CLI
4. **Error handling**: Mixed use of `print()` for errors and exceptions

Files with print statements requiring changes:
- `guacalib/db.py` - Contains `debug_print()` method and error prints
- `guacalib/cli_handle_*.py` files - Error prints in command handlers
- `guacalib/cli.py` - Error handling and validation prints
- `debug_permissions.py` - Debug script (optional to modify)

## Phase 1: Logging Infrastructure Setup

### 1.1 Create Logging Configuration Module
- Create `guacalib/logging_config.py`
- Implement `setup_logging()` function with configurable levels and duplicate handler prevention
- Configure formatters for different log levels
- Set up handlers for stderr output
- Support for existing `--debug` flag integration
- **Critical**: Do NOT configure logging on import - setup_logging() must be called explicitly
- **Important**: Add guard against duplicate handlers for library usage scenarios
- **Important**: Remove or avoid default root handlers to prevent duplicate logs in repeated CLI invocations
- **Critical**: `setup_logging()` must be idempotent to support multiple CLI calls and library usage in tests
- **Style Requirement**: All functions must include Google/NumPy-style docstrings and type hints per AGENTS.md

### 1.2 Define Logging Strategy
- **DEBUG**: Detailed internal operations, SQL queries (when debug enabled), parameter validation details
- **INFO**: Important operational milestones, successful command completions, database connection establishment
- **WARNING**: Recoverable issues, deprecated usage, validation warnings
- **ERROR**: Database errors, connection failures, validation errors, rollback failures
- **CRITICAL**: System-level failures, authentication issues

### 1.3 Logger Naming Convention
- Root logger: `guacalib`
- Module-specific loggers: `guacalib.db`, `guacalib.cli`, etc.

## Phase 2: Core Database Layer Logging

### 2.1 Modify GuacamoleDB Class
- **Decision**: Keep `debug_print()` method as backwards-compatible wrapper that delegates to logging
- Update `debug_print()` method to use `logger.debug()` internally
- Gradually migrate direct `debug_print()` calls to use `logger.debug()` where appropriate
- Add logging for:
  - Database connection establishment and closing
  - Transaction start/commit/rollback
  - Query execution timing (debug level)
  - Parameter validation warnings
- **Critical**: All user-facing print() calls for data output remain unchanged
- **Migration Path**: Existing CLI handlers using `guacdb.debug_print()` continue to work without modification

### 2.2 Database Error Logging
- Replace internal error `print()` statements with `logger.error()`
- **Critical**: Preserve user-facing error messages that tests expect via `print()` statements
- Add context information to error logs
- **Critical**: Maintain exception propagation for CLI layer so existing tests remain unchanged
- Log rollback operations and failures but ensure exceptions still bubble up
- **Important**: User-facing output (lists, dumps, command results, error messages) must stay as print() calls
- **Test Compatibility**: Maintain exact print() message formats that tests rely on for validation

### 2.3 Update `db.py`
- Add logger import and initialization
- Replace all internal diagnostic prints
- Keep user-facing data outputs unchanged
- Add logging for major operations (create, update, delete)

## Phase 3: CLI Handler Logging

### 3.1 Update CLI Handler Files
For each `cli_handle_*.py` file:
- Add logger import and initialization
- Replace internal error `print()` statements with `logger.error()`
- **Critical**: Preserve user-facing error messages that tests expect via `print()` statements (possibly alongside logging)
- **Decision**: Add `logger.info()` calls for successful command completion and key milestones (e.g., "User created successfully", "Connection updated")
- Add `logger.debug()` calls for detailed operation steps when debug enabled
- Log validation warnings and issues with appropriate levels
- **Critical**: Preserve all user-facing output using `print()` - only replace internal diagnostics
- **Critical**: Ensure exceptions still propagate to CLI layer so existing tests remain unchanged
- **Test Compatibility**: Keep exact print() message formats that tests parse for validation
- **Dual Output Strategy**: For some errors, use both `print()` (for tests/users) AND `logger.error()` (for diagnostics)

### 3.2 Modify `cli.py`
- **Important**: Do NOT call setup_logging() here - only import logging_config
- Replace error handling `print()` statements with logging
- Add logging for argument parsing issues
- Log configuration permission checks
- **Critical**: Maintain user-facing help/version prints exactly as-is
- **Critical**: Ensure all exceptions continue to propagate properly for existing test behavior

### 3.3 Preserve User Output
- Ensure all CLI results, YAML dumps, and lists still use `print()`
- Do not change output format expected by tests
- Keep structured command output exactly as-is

## Phase 4: Integration and Configuration

### 4.1 CLI Integration
- **Critical**: Call `setup_logging()` explicitly from `cli.main()` ONCE per invocation
- Call setup_logging() AFTER parsing `--debug` flag but BEFORE database operations
- Modify `--debug` flag to set logging level to DEBUG
- Set default logging level to WARNING/ERROR for normal operation
- **Important**: Do NOT configure logging in `__init__.py` - avoid import-time configuration

### 4.2 Library Integration
- Make logging work when GuacamoleDB is used as a library
- Allow downstream users to opt-in by calling `setup_logging()` themselves
- Document logger usage for library consumers
- Ensure idempotent behavior for repeated setup_logging() calls

### 4.3 Environment Variable Support (Optional Enhancement)
- Support `GUACALIB_LOG_LEVEL` environment variable
- Support `GUACALIB_LOG_FORMAT` for custom formatting

## Phase 5: Testing and Validation

### 5.1 Functional Testing
- Run full test suite: `make tests`
- Verify all existing tests pass without modification
- Ensure CLI output format remains unchanged
- Test logging with and without `--debug` flag

### 5.2 Logging Behavior Testing
- Verify debug output appears with `--debug` flag
- Confirm error messages go to logging system
- Test log level configuration
- Validate stderr vs stdout separation

### 5.3 Integration Testing
- Test library usage scenarios
- Verify downstream logger configuration works
- Test with different log levels

## Implementation Details

### Code Style Requirements (per AGENTS.md)

All new code must adhere to the following requirements:
- **Type hints**: Add to all function signatures and variable declarations
- **Docstrings**: Use Google-style or NumPy-style docstrings consistently
- **Meaningful names**: Use clear, descriptive variable and function names
- **Error handling**: Provide descriptive error messages and handle exceptions appropriately
- **Single responsibility**: Each function should have a single, clear purpose
- **Security**: Never hardcode sensitive information, validate all inputs
- **Style Reminders**:
  - All new helper functions (like `get_logger()`) must include proper docstrings and type hints
  - Reiterate AGENTS.md compliance for any newly introduced functions
  - Ensure consistency with existing codebase style

### File Changes Required

**New Files:**
- `guacalib/logging_config.py` - Logging configuration and setup with proper type hints and docstrings

**Modified Files:**
- `guacalib/__init__.py` - **DO NOT** configure logging on import - only expose helper functions
- `guacalib/db.py` - Replace debug_print, add logging with type hints, maintain exception propagation
- `guacalib/cli.py` - Import logging_config, call setup_logging() in main(), replace error prints, maintain user output
- `guacalib/cli_handle_user.py` - Replace error prints with logging, add success milestones, preserve exceptions
- `guacalib/cli_handle_usergroup.py` - Replace error prints with logging, add success milestones, preserve exceptions
- `guacalib/cli_handle_conn.py` - Replace error prints with logging, add success milestones, preserve exceptions
- `guacalib/cli_handle_conngroup.py` - Replace error prints with logging, add success milestones, preserve exceptions
- `guacalib/cli_handle_dump.py` - Replace error prints with logging, add success milestones, preserve exceptions

### Backward Compatibility

- **Critical**: All user-facing CLI output remains unchanged (print() calls preserved)
- Existing `--debug` flag behavior preserved
- No breaking changes to public API
- **Critical**: Exception propagation behavior unchanged - tests parsing stdout/stderr remain unaffected
- Tests should continue to pass without modification
- **Critical**: Importing guacalib as a library does not reconfigure logging automatically

### Example Logging Implementation

```python
# guacalib/logging_config.py
"""Logging configuration for guacalib package.

This module provides centralized logging configuration for the guacalib
library and CLI application, with proper handling for duplicate handlers
to support both library usage and CLI invocation scenarios.
"""

import logging
import sys
from typing import Optional


def setup_logging(debug: bool = False, force_reconfigure: bool = False) -> None:
    """Configure logging for guacalib package with duplicate handler prevention.

    This function sets up logging configuration for the guacalib package.
    It includes guards against duplicate handlers to support repeated
    invocations and library usage scenarios. This function is idempotent
    and can be called multiple times safely.

    Args:
        debug: If True, set logging level to DEBUG; otherwise use WARNING.
        force_reconfigure: If True, remove existing handlers before configuration.
                         Used for testing and special scenarios.

    Note:
        - Function is idempotent - safe to call multiple times
        - Prevents duplicate handlers by checking existing handlers
        - **Important**: Does NOT modify root logger handlers - respects host application configuration
        - Only manages guacalib-specific handlers to avoid interference with embedding applications
        - Configures both guacalib root logger and module-specific loggers
        - Uses stderr for log output to preserve stdout for user-facing data
        - Must be called explicitly - never configured on import

    Example:
        >>> # CLI usage (called from cli.main after parsing --debug)
        >>> setup_logging(debug=True)
        >>>
        >>> # Library usage with custom configuration
        >>> setup_logging(debug=False)
        >>> logger = logging.getLogger('guacalib.db')
        >>> logger.info("Database operation completed")
    """
    level = logging.DEBUG if debug else logging.WARNING

    # Get the guacalib root logger
    logger = logging.getLogger('guacalib')

    # Check if already configured to avoid duplicate handlers
    if logger.handlers and not force_reconfigure:
        return

    # Remove any existing handlers if forcing reconfiguration
    if force_reconfigure:
        logger.handlers.clear()

    # **Important**: Do NOT remove root logger handlers - respect host application's logging configuration
    # Only manage guacalib-specific handlers to avoid interfering with embedding applications

    logger.setLevel(level)

    # Create handler for stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter based on debug mode
    if debug:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter('%(levelname)s: %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplication
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific guacalib module.

    Args:
        name: The module name (e.g., 'db', 'cli', 'cli_handle_user')

    Returns:
        A configured logger instance for the specified module.

    Example:
        >>> logger = get_logger('db')
        >>> logger.debug("Executing SQL query")

    Note:
        This helper function must follow AGENTS.md requirements:
        - Includes proper type hints and Google-style docstrings
        - Uses clear, meaningful function names
        - Handles parameters appropriately
        - Follows single-responsibility principle
    """
    return logging.getLogger(f'guacalib.{name}')
```


## Success Criteria

1. **All tests pass**: `make tests` completes successfully
2. **Debug functionality preserved**: `--debug` flag works as expected
3. **Clean separation**: User output uses stdout, logs use stderr
4. **Library integration**: GuacamoleDB can be used in other applications with configurable logging
5. **No breaking changes**: Existing CLI behavior and output unchanged
6. **Improved diagnostics**: Better error context and operational visibility

## Timeline Estimate

- **Phase 1**: 1-2 hours (Infrastructure setup)
- **Phase 2**: 2-3 hours (Core database logging)
- **Phase 3**: 2-3 hours (CLI handlers)
- **Phase 4**: 1-2 hours (Integration and configuration)
- **Phase 5**: 2-3 hours (Testing and validation)

**Total Estimated Time**: 8-13 hours

## Post-Implementation Benefits

1. **Better developer experience**: Configurable verbosity and better debugging
2. **Enhanced library integration**: Downstream users can control logging
3. **Improved testing**: Easier to capture and assert on diagnostics
4. **Production readiness**: Suitable for production deployment with log aggregation
5. **Maintainability**: Clearer separation of concerns in codebase