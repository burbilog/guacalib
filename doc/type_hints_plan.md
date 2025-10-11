# Type Hints Implementation Plan

This document outlines the comprehensive plan to add type hints throughout the guacalib codebase. The goal is to improve code documentation, IDE support, and enable runtime type checking while maintaining backward compatibility.

## Current State Analysis

- **Type Hints Usage**: Minimal - only 1 occurrence across all Python files
- **Typing Imports**: No `from typing import` statements found
- **Scope**: 238 functions across 10 Python files need type hints
- **Files**: 12 total Python files in the project

## Key Files Requiring Type Hints

### Core Files
- [ ] `guacalib/db.py` - GuacamoleDB class with 68 methods (highest priority)
- [ ] `guacalib/cli.py` - CLI interface with 12 functions
- [ ] `guacalib/cli_handle_user.py` - User management commands
- [ ] `guacalib/cli_handle_usergroup.py` - User group management commands
- [ ] `guacalib/cli_handle_conn.py` - Connection management commands
- [ ] `guacalib/cli_handle_conngroup.py` - Connection group management commands
- [ ] `guacalib/cli_handle_dump.py` - Data export functionality

### Supporting Files
- [ ] `guacalib/db_connection_parameters.py` - Connection parameter definitions
- [ ] `guacalib/db_user_parameters.py` - User parameter definitions
- [ ] `guacalib/version.py` - Version information
- [ ] `debug_permissions.py` - Debug utility script

## Required Type Imports

### Standard Library Types
```python
from typing import (
    Optional, Union, Dict, List, Tuple, Any,
    Callable, Iterator, Type, Set, Literal,
    overload, TypeVar, Generic
)
```

### External Library Types
```python
import mysql.connector
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import CursorBase
```

## Custom Type Definitions

### Database Configuration Types
```python
ConnectionConfig = Dict[str, str]
ConnectionParameters = Dict[str, Union[str, int, bool]]
UserParameters = Dict[str, Dict[str, Union[str, str, str]]]
```

### Query Result Types
```python
UserInfo = Tuple[str, List[str]]
ConnectionInfo = Tuple[int, str, str, str, str, str, str, List[str]]
GroupInfo = Dict[str, Dict[str, Union[int, List[str]]]]
PermissionInfo = Tuple[str, str, str]  # (entity_name, entity_type, permission)
```

### CLI Types
```python
ArgsType = Any  # from argparse.Namespace
CommandHandler = Callable[[ArgsType, GuacamoleDB], None]
```

## Implementation Phases

### Phase 1: Core Infrastructure Setup
- [ ] Add typing imports to all files
- [ ] Define custom types at top of relevant modules
- [ ] Type the `GuacamoleDB` class constructor (`__init__`)
- [ ] Type context manager methods (`__enter__`, `__exit__`)
- [ ] Type basic utility methods (`debug_print`, `read_config`, `connect_db`)

### Phase 2: Core Database Operations
- [ ] Type all ID resolution methods (`resolve_connection_id`, `resolve_conngroup_id`, `resolve_usergroup_id`)
- [ ] Type existence checking methods (`*_exists`, `*_exists_by_id`)
- [ ] Type getter methods (`get_*_by_id`, `get_*_by_name`)
- [ ] Type validation methods (`validate_positive_id`)

### Phase 3: CRUD Operations
#### User Management
- [ ] Type `create_user()`
- [ ] Type `delete_existing_user()`
- [ ] Type `modify_user()`
- [ ] Type `change_user_password()`
- [ ] Type user listing methods (`list_users`, `list_users_with_usergroups`)

#### User Group Management
- [ ] Type `create_usergroup()`
- [ ] Type `delete_existing_usergroup()`
- [ ] Type `delete_existing_usergroup_by_id()`
- [ ] Type `add_user_to_usergroup()`
- [ ] Type `remove_user_from_usergroup()`
- [ ] Type user group listing methods

#### Connection Management
- [ ] Type `create_connection()`
- [ ] Type `delete_existing_connection()`
- [ ] Type `modify_connection()`
- [ ] Type `modify_connection_parent_group()`
- [ ] Type connection listing methods (`list_connections_with_conngroups_and_parents`, `get_connection_by_id`)

#### Connection Group Management
- [ ] Type `create_connection_group()`
- [ ] Type `delete_connection_group()`
- [ ] Type `modify_connection_group_parent()`
- [ ] Type connection group listing methods (`list_connection_groups`, `get_connection_group_by_id`)

### Phase 4: Permission Management
- [ ] Type `grant_connection_permission_to_user()`
- [ ] Type `revoke_connection_permission_from_user()`
- [ ] Type `grant_connection_group_permission_to_user()`
- [ ] Type `revoke_connection_group_permission_from_user()`
- [ ] Type `grant_connection_group_permission_to_user_by_id()`
- [ ] Type `revoke_connection_group_permission_from_user_by_id()`
- [ ] Type `get_connection_user_permissions()`
- [ ] Type `_atomic_permission_operation()`

### Phase 5: CLI Layer
- [ ] Type `main()` function in cli.py
- [ ] Type argument parser functions (`positive_int`, `validate_selector`)
- [ ] Type subcommand setup functions (`setup_*_subcommands`)
- [ ] Type all command handler functions in cli_handle_*.py files

### Phase 6: Parameter Definitions & Utilities
- [ ] Type parameter definition structures in db_*_parameters.py
- [ ] Type utility functions in debug_permissions.py
- [ ] Type version module exports

## Priority Method Breakdown

### High Priority (Complex Signatures)
- [ ] `GuacamoleDB.__init__(self, config_file: str = "db_config.ini", debug: bool = False) -> None`
- [ ] `GuacamoleDB.__enter__(self) -> GuacamoleDB`
- [ ] `GuacamoleDB.__exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[Any]) -> None`
- [ ] `GuacamoleDB.resolve_connection_id(self, connection_name: Optional[str] = None, connection_id: Optional[int] = None) -> int`
- [ ] `GuacamoleDB.resolve_conngroup_id(self, group_name: Optional[str] = None, group_id: Optional[int] = None) -> int`
- [ ] `GuacamoleDB.resolve_usergroup_id(self, group_name: Optional[str] = None, group_id: Optional[int] = None) -> int`
- [ ] `GuacamoleDB.list_connections_with_conngroups_and_parents(self) -> List[ConnectionInfo]`
- [ ] `GuacamoleDB.list_usergroups_with_users_and_connections(self) -> Dict[str, Dict[str, Union[int, List[str]]]]`
- [ ] `GuacamoleDB.list_users_with_usergroups(self) -> Dict[str, List[str]]`

### Medium Priority (Standard CRUD)
- [ ] All existence checking methods: `-> bool`
- [ ] All simple getter methods: `-> Optional[Union[str, int]]`
- [ ] All creation methods: `-> Union[int, bool, None]`
- [ ] All deletion methods: `-> None`
- [ ] All modification methods: `-> bool`

### Low Priority (Simple Functions)
- [ ] Utility functions with basic signatures
- [ ] Configuration-related functions
- [ ] Debug and helper methods

## Special Considerations

### Database Cursor Types
- [ ] Use `CursorBase[Any]` for cursor type hints
- [ ] Specify return types for fetch operations (`List[Tuple[Any, ...]]`)
- [ ] Type individual tuple elements where possible

### Error Handling
- [ ] Many methods raise `ValueError` for validation errors
- [ ] Many methods raise `mysql.connector.Error` for database errors
- [ ] Consider using `Union[ReturnType, None]` for methods that may return None on error

### Optional Parameters
- [ ] Use `Optional[Type]` for parameters that can be None
- [ ] Use default values of `None` for optional parameters
- [ ] Consider using `Union[Type1, Type2]` for parameters that accept multiple types

### Context Manager
- [ ] Ensure `GuacamoleDB` context manager methods are properly typed
- [ ] Type the `self` parameter in class methods as `GuacamoleDB`

## Implementation Guidelines

### Code Style
- [ ] Follow PEP 484 type hinting conventions
- [ ] Use forward references for circular imports where needed
- [ ] Keep type hints on the same line for simple signatures
- [ ] Use multi-line signatures for complex methods

### Backward Compatibility
- [ ] Ensure all type hints are optional (runtime compatible)
- [ ] Do not change existing method signatures
- [ ] Use `Any` for complex types that are difficult to specify precisely
- [ ] Test that the code still works after adding type hints

### Documentation
- [ ] Update docstrings to reflect type information where helpful
- [ ] Use type hints as primary documentation for parameter/return types
- [ ] Add comments explaining complex type choices

## Validation

### Type Checking
- [ ] Run `mypy guacalib/` to verify type hints
- [ ] Fix any type errors that arise
- [ ] Ensure strict type checking passes

### Runtime Testing
- [ ] Run existing test suite to ensure functionality is preserved
- [ ] Test with `python -m typing` to verify runtime compatibility
- [ ] Test CLI functionality with all commands

## Progress Tracking

- [ ] Phase 1: Core Infrastructure (0/5 complete)
- [ ] Phase 2: Core Database Operations (0/4 complete)
- [ ] Phase 3: CRUD Operations (0/4 complete)
- [ ] Phase 4: Permission Management (0/7 complete)
- [ ] Phase 5: CLI Layer (0/4 complete)
- [ ] Phase 6: Parameter Definitions & Utilities (0/3 complete)

## Notes

This plan is designed to be implemented incrementally. Each phase builds on the previous one and provides immediate benefits in terms of code clarity and IDE support. The prioritization ensures that the most complex and important parts of the codebase are addressed first.