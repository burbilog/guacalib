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
- Implement `setup_logging()` function with configurable levels
- Configure formatters for different log levels
- Set up handlers for stderr output
- Support for existing `--debug` flag integration

### 1.2 Define Logging Strategy
- **DEBUG**: Detailed internal operations, SQL queries (when debug enabled)
- **INFO**: Important operational milestones
- **WARNING**: Recoverable issues, deprecated usage
- **ERROR**: Database errors, connection failures, validation errors
- **CRITICAL**: System-level failures

### 1.3 Logger Naming Convention
- Root logger: `guacalib`
- Module-specific loggers: `guacalib.db`, `guacalib.cli`, etc.

## Phase 2: Core Database Layer Logging

### 2.1 Modify GuacamoleDB Class
- Replace `debug_print()` method with proper logging
- Update all `debug_print()` calls to use `logger.debug()`
- Add logging for:
  - Database connection establishment and closing
  - Transaction start/commit/rollback
  - Query execution timing (debug level)
  - Parameter validation warnings

### 2.2 Database Error Logging
- Replace error `print()` statements with `logger.error()`
- Add context information to error logs
- Maintain exception propagation for CLI layer
- Log rollback operations and failures

### 2.3 Update `db.py`
- Add logger import and initialization
- Replace all internal diagnostic prints
- Keep user-facing data outputs unchanged
- Add logging for major operations (create, update, delete)

## Phase 3: CLI Handler Logging

### 3.1 Update CLI Handler Files
For each `cli_handle_*.py` file:
- Add logger import and initialization
- Replace error `print()` statements with `logger.error()`
- Add logging for command start/completion (info level)
- Log validation warnings and issues

### 3.2 Modify `cli.py`
- Add logging configuration initialization
- Replace error handling `print()` statements with logging
- Add logging for argument parsing issues
- Log configuration permission checks
- Maintain user-facing help/version prints

### 3.3 Preserve User Output
- Ensure all CLI results, YAML dumps, and lists still use `print()`
- Do not change output format expected by tests
- Keep structured command output exactly as-is

## Phase 4: Integration and Configuration

### 4.1 CLI Integration
- Modify `--debug` flag to set logging level to DEBUG
- Set default logging level to WARNING/ERROR for normal operation
- Ensure logging configuration happens early in CLI startup

### 4.2 Library Integration
- Make logging work when GuacamoleDB is used as a library
- Allow downstream users to configure loggers
- Document logger usage for library consumers

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

### File Changes Required

**New Files:**
- `guacalib/logging_config.py` - Logging configuration and setup

**Modified Files:**
- `guacalib/__init__.py` - Import logging setup
- `guacalib/db.py` - Replace debug_print, add logging
- `guacalib/cli.py` - Add logging initialization, replace error prints
- `guacalib/cli_handle_user.py` - Replace error prints with logging
- `guacalib/cli_handle_usergroup.py` - Replace error prints with logging
- `guacalib/cli_handle_conn.py` - Replace error prints with logging
- `guacalib/cli_handle_conngroup.py` - Replace error prints with logging
- `guacalib/cli_handle_dump.py` - Replace error prints with logging

### Backward Compatibility

- All user-facing CLI output remains unchanged
- Existing `--debug` flag behavior preserved
- No breaking changes to public API
- Tests should continue to pass without modification

### Example Logging Implementation

```python
# guacalib/logging_config.py
import logging
import sys

def setup_logging(debug: bool = False) -> None:
    """Configure logging for guacalib package."""
    level = logging.DEBUG if debug else logging.WARNING

    # Configure root logger for guacalib
    logger = logging.getLogger('guacalib')
    logger.setLevel(level)

    # Create handler for stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    if debug:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        formatter = logging.Formatter('%(levelname)s: %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)
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