# Guacalib Docstrings Implementation Plan

This document outlines a comprehensive plan for adding Google-style docstrings to all Python code in the guacalib library.

## Current State Analysis

Based on code analysis:
- **Total functions**: 293 functions across 7 Python files
- **Total classes**: 3 classes across 2 Python files
- **Existing docstrings**: 86 docstrings (mostly incomplete)
- **Files requiring documentation**:
  - `guacalib/db.py` - Core database class (57 functions, 2 classes)
  - `guacalib/cli.py` - Main CLI interface (10 functions)
  - `guacalib/cli_handle_user.py` - User management (6 functions)
  - `guacalib/cli_handle_conn.py` - Connection management (8 functions)
  - `guacalib/cli_handle_usergroup.py` - User group management (1 function)
  - `guacalib/cli_handle_conngroup.py` - Connection group management (1 function)
  - `guacalib/cli_handle_dump.py` - Data export (2 functions)
  - `debug_permissions.py` - Debug utilities (18 functions)

## Documentation Standards

All docstrings will follow **Google-style format** with the following structure:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Brief one-line summary.

    Extended description if needed. Explain the purpose, behavior, and any
    important considerations.

    Args:
        param1: Description of parameter 1.
        param2: Description of parameter 2.

    Returns:
        Description of the return value.

    Raises:
        ValueError: Description of when this error is raised.
        mysql.connector.Error: Description of database-related errors.

    Example:
        >>> result = function_name("value1", "value2")
        >>> print(result)
        expected_output
    """
```

## Implementation Phases

### Phase 1: Core Database Layer
**File**: `guacalib/db.py` (GuacamoleDB class)

- [ ] **GuacamoleDB class documentation**
  - [ ] Class-level docstring explaining purpose and usage
  - [ ] Context manager methods (`__enter__`, `__exit__`)
  - [ ] Initialization method (`__init__`)

- [ ] **Configuration and connection methods**
  - [ ] `read_config()` - Parse configuration file
  - [ ] `connect_db()` - Establish database connection
  - [ ] `debug_print()` - Debug output utility

- [ ] **User management methods**
  - [ ] `user_exists()` - Check user existence
  - [ ] `list_users()` - List all users
  - [ ] `create_user()` - Create new user
  - [ ] `delete_existing_user()` - Delete user
  - [ ] `change_user_password()` - Update password
  - [ ] `modify_user()` - Update user parameters

- [ ] **User group management methods**
  - [ ] `usergroup_exists()` - Check group existence
  - [ ] `usergroup_exists_by_id()` - Check group existence by ID
  - [ ] `list_usergroups()` - List all groups
  - [ ] `create_usergroup()` - Create new group
  - [ ] `delete_existing_usergroup()` - Delete group by name
  - [ ] `delete_existing_usergroup_by_id()` - Delete group by ID
  - [ ] `get_usergroup_id()` - Get group ID by name
  - [ ] `get_usergroup_name_by_id()` - Get group name by ID
  - [ ] `add_user_to_usergroup()` - Add user to group
  - [ ] `remove_user_from_usergroup()` - Remove user from group

- [ ] **Connection management methods**
  - [ ] `connection_exists()` - Check connection existence
  - [ ] `create_connection()` - Create new connection
  - [ ] `delete_existing_connection()` - Delete connection
  - [ ] `modify_connection()` - Update connection parameters
  - [ ] `modify_connection_parent_group()` - Set parent group
  - [ ] `get_connection_by_id()` - Get connection by ID
  - [ ] `get_connection_name_by_id()` - Get connection name by ID
  - [ ] `resolve_connection_id()` - Resolve name/ID to connection ID

- [ ] **Connection group management methods**
  - [ ] `connection_group_exists()` - Check group existence
  - [ ] `create_connection_group()` - Create new group
  - [ ] `delete_connection_group()` - Delete group
  - [ ] `list_connection_groups()` - List all groups
  - [ ] `get_connection_group_by_id()` - Get group by ID
  - [ ] `get_connection_group_name_by_id()` - Get group name by ID
  - [ ] `get_connection_group_id_by_name()` - Get group ID by name
  - [ ] `modify_connection_group_parent()` - Set parent group
  - [ ] `resolve_conngroup_id()` - Resolve name/ID to group ID
  - [ ] `resolve_usergroup_id()` - Resolve name/ID to user group ID

- [ ] **Permission management methods**
  - [ ] `grant_connection_permission()` - Grant connection access
  - [ ] `grant_connection_permission_to_user()` - Grant to specific user
  - [ ] `revoke_connection_permission_from_user()` - Revoke from user
  - [ ] `grant_connection_group_permission_to_user()` - Grant group access
  - [ ] `grant_connection_group_permission_to_user_by_id()` - Grant by group ID
  - [ ] `revoke_connection_group_permission_from_user()` - Revoke group access
  - [ ] `revoke_connection_group_permission_from_user_by_id()` - Revoke by group ID

- [ ] **Data retrieval and listing methods**
  - [ ] `list_users_with_usergroups()` - Users with their groups
  - [ ] `list_connections_with_conngroups_and_parents()` - Connections with details
  - [ ] `list_usergroups_with_users_and_connections()` - Groups with members
  - [ ] `list_groups_with_users()` - Groups and user membership
  - [ ] `get_connection_user_permissions()` - Get user permissions for connection

- [ ] **Utility and validation methods**
  - [ ] `validate_positive_id()` - Validate ID format
  - [ ] `_check_connection_group_cycle()` - Check for circular references
  - [ ] `_atomic_permission_operation()` - Atomic operation wrapper
  - [ ] `debug_connection_permissions()` - Debug permission issues

### Phase 2: CLI Interface Layer
**File**: `guacalib/cli.py`

- [ ] **Utility functions**
  - [ ] `positive_int()` - Validate positive integers
  - [ ] `validate_selector()` - Validate name/ID selectors
  - [ ] `check_config_permissions()` - Validate config file permissions

- [ ] **CLI setup functions**
  - [ ] `setup_user_subcommands()` - Configure user commands
  - [ ] `setup_usergroup_subcommands()` - Configure user group commands
  - [ ] `setup_conn_subcommands()` - Configure connection commands
  - [ ] `setup_conngroup_subcommands()` - Configure connection group commands
  - [ ] `setup_dump_subcommand()` - Configure dump command
  - [ ] `setup_version_subcommand()` - Configure version command
  - [ ] `main()` - Main CLI entry point

### Phase 3: Command Handler Modules
**Files**: `cli_handle_*.py`

- [ ] **User management handlers** (`cli_handle_user.py`)
  - [ ] `handle_user_command()` - Main user command router
  - [ ] `handle_user_new()` - Create user command
  - [ ] `handle_user_list()` - List users command
  - [ ] `handle_user_exists()` - Check user existence command
  - [ ] `handle_user_delete()` - Delete user command
  - [ ] `handle_user_modify()` - Modify user command

- [ ] **Connection management handlers** (`cli_handle_conn.py`)
  - [ ] `handle_conn_command()` - Main connection command router
  - [ ] `handle_conn_new()` - Create connection command
  - [ ] `handle_conn_list()` - List connections command
  - [ ] `handle_conn_exists()` - Check connection existence command
  - [ ] `handle_conn_delete()` - Delete connection command
  - [ ] `handle_conn_modify()` - Modify connection command
  - [ ] Additional connection-related functions

- [ ] **User group management handlers** (`cli_handle_usergroup.py`)
  - [ ] `handle_usergroup_command()` - Main user group command router
  - [ ] All user group subcommand handlers

- [ ] **Connection group management handlers** (`cli_handle_conngroup.py`)
  - [ ] `handle_conngroup_command()` - Main connection group command router
  - [ ] All connection group subcommand handlers

- [ ] **Data export handlers** (`cli_handle_dump.py`)
  - [ ] `handle_dump_command()` - Export data command
  - [ ] `print_yaml_dump()` - Format and print YAML output

### Phase 4: Parameter Definition Modules
**Files**: `db_*.py`

- [ ] **Connection parameters** (`db_connection_parameters.py`)
  - [ ] Module-level docstring explaining connection parameter structure
  - [ ] Documentation for CONNECTION_PARAMETERS dictionary

- [ ] **User parameters** (`db_user_parameters.py`)
  - [ ] Module-level docstring explaining user parameter structure
  - [ ] Documentation for USER_PARAMETERS dictionary

### Phase 5: Utility and Debug Tools
**Files**: `debug_permissions.py`, `version.py`

- [ ] **Debug utilities** (`debug_permissions.py`)
  - [ ] All 18 debug functions for permission troubleshooting
  - [ ] Clear explanations of what each debug function checks

- [ ] **Version information** (`version.py`)
  - [ ] Module-level documentation
  - [ ] VERSION constant documentation

### Phase 6: Package Initialization
**File**: `guacalib/__init__.py`

- [ ] Package-level docstring explaining the library's purpose
- [ ] Usage examples
- [ ] API overview

## Quality Assurance Checklist

For each documented function/class:

- [ ] **Google-style format** followed correctly
- [ ] **Brief summary** line (imperative mood)
- [ ] **Detailed description** when needed
- [ ] **Args section** with type annotations and descriptions
- [ ] **Returns section** with clear return value description
- [ ] **Raises section** documenting all exceptions
- [ ] **Example section** for complex functions
- [ ] **See Also** section for related functions when appropriate
- [ ] **Notes section** for important implementation details

## Documentation Tools and Validation

- [ ] **pydocstyle** configuration for linting
- [ ] **Sphinx** compatibility for future API documentation
- [ ] **Type hint integration** with existing type annotations
- [ ] **Example testing** where applicable

## Implementation Notes

1. **Maintain backward compatibility** - All existing signatures and behavior preserved
2. **Leverage existing type hints** - Use already-defined type annotations in docstrings
3. **Database security emphasis** - Document security considerations where relevant
4. **Error handling clarity** - Clearly document when and why exceptions are raised
5. **MySQL/Guacamole context** - Provide sufficient domain-specific context

## Estimated Timeline

- **Phase 1**: 2-3 days (Core database layer - highest priority)
- **Phase 2**: 1 day (CLI interface)
- **Phase 3**: 2-3 days (Command handlers)
- **Phase 4**: 0.5 day (Parameter definitions)
- **Phase 5**: 1 day (Utilities and debug tools)
- **Phase 6**: 0.5 day (Package initialization)

**Total estimated time**: 7-8 days

## Success Criteria

1. **100% coverage** - All public functions and classes have docstrings
2. **Style consistency** - All docstrings follow Google style
3. **Documentation completeness** - Args, Returns, and Raises documented
4. **Example clarity** - Complex functions include usage examples
5. **Tool validation** - Passes pydocstyle linting without errors

This plan ensures comprehensive, high-quality documentation that will improve code maintainability and enable automatic API documentation generation.