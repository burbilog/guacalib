# Phase 4: Repository Layer Planning

## Problem Statement P4 - Mixed Responsibilities (HIGH SEVERITY)

The current GuacamoleDB class conflates multiple responsibilities that should be separated for better maintainability, testability, and modularity.

## Current GuacamoleDB Responsibilities Analysis

### Total Lines: 3086 lines in guacalib/db.py

### Responsibility Matrix

| Responsibility | Methods | Lines | % of Code | Description |
|----------------|---------|-------|-----------|-------------|
| **Config/Loading** | `__init__`, `read_config`, `connect_db` | ~114 lines | 3.7% | Database credentials, connection setup, environment variable handling |
| **DB Connection/Transactions** | `__enter__`, `__exit__` | ~26 lines | 0.8% | Context manager, commit/rollback logic, connection cleanup |
| **User CRUD Operations** | `user_exists`, `create_user`, `delete_existing_user`, `modify_user`, `change_user_password`, `list_users` | ~450 lines | 14.6% | User creation, deletion, modification, password management |
| **UserGroup CRUD Operations** | `usergroup_exists`, `create_usergroup`, `delete_existing_usergroup`, `list_usergroups`, `add_user_to_usergroup`, `remove_user_from_usergroup` | ~350 lines | 11.3% | User group CRUD, user-group membership management |
| **Connection CRUD Operations** | `connection_exists`, `create_connection`, `delete_existing_connection`, `modify_connection`, `list_connections_with_conngroups_and_parents` | ~600 lines | 19.4% | Connection creation, deletion, parameter modification, protocol handling |
| **ConnGroup CRUD Operations** | `connection_group_exists`, `create_connection_group`, `delete_connection_group`, `list_connection_groups`, `modify_connection_group_parent` | ~400 lines | 13.0% | Connection group hierarchy, CRUD operations |
| **Permission Operations** | `grant_connection_permission_to_user`, `revoke_connection_permission_from_user`, `grant_connection_group_permission_to_user`, `revoke_connection_group_permission_from_user`, various other permission methods | ~500 lines | 16.2% | Grant/deny permissions across all entity combinations |
| **ID Resolution/Validation** | `resolve_connection_id`, `resolve_conngroup_id`, `resolve_usergroup_id`, `validate_positive_id`, `get_*_name_by_id` methods | ~253 lines (extracted to db_utils.py in Phase 2) | 8.2% | Entity ID resolution, validation helpers |
| **Logging Utilities** | `_scrub_credentials`, `debug_print`, `debug_*` methods | ~120 lines | 3.9% | Credential scrubbing, debug output, logging helpers |
| **Parameter Definitions** | `CONNECTION_PARAMETERS`, `USER_PARAMETERS` class attributes | ~2 lines | 0.1% | Parameter dictionaries (imported from external files) |

### Transaction Boundaries Analysis

**Multi-step Operations Requiring Transaction Atomicity:**
1. **User Creation**: Create entity + user record + password hash + salt
2. **Connection Creation**: Create entity + connection record + parameter records
3. **Connection Group Creation**: Create entity + group record + hierarchy validation
4. **Permission Granting**: Validate entities + check existing + insert permission
5. **Cascade Deletes**: Delete entity + dependent records (connections, permissions, etc.)

**All call sites verified to use context manager pattern:**
```python
with GuacamoleDB(args.config, debug=args.debug) as guacdb:
    guacdb.some_operation()
```

### Permission Operations Complexity

**Four Permission Domains:**
1. **User → Connection**: Individual user access to specific connections
2. **User → Connection Group**: Individual user access to connection groups
3. **UserGroup → Connection**: Group-based access to specific connections
4. **UserGroup → Connection Group**: Group-based access to connection groups

**Operations per Domain:**
- Grant permission (with validation)
- Revoke permission
- List permissions
- Check existence

## Repository Layer Design

### Target Architecture

```
guacalib/
├── db_utils.py              # Phase 2 - ID resolvers, validation helpers
├── users_repo.py            # Phase 5 - User CRUD SQL operations
├── usergroups_repo.py       # Phase 6 - User group CRUD SQL operations
├── connections_repo.py      # Phase 7 - Connection CRUD SQL operations
├── conngroups_repo.py       # Phase 8 - Connection group CRUD SQL operations
├── permissions_repo.py      # Phase 9 - Permission grant/deny SQL operations
├── guac_db.py               # Phase 10 - Thin façade preserving GuacamoleDB API
└── db.py                    # DEPRECATED - Re-export for backwards compatibility
```

### Repository API Contracts

**Design Principles:**
1. **Stateless Functions**: Each repository function accepts cursor as first parameter
2. **Single Responsibility**: Each repository handles one domain's SQL operations
3. **No Transaction Logic**: Repositories don't manage transactions - caller handles them
4. **Type Safety**: All functions have comprehensive type hints
5. **Error Handling**: Repository functions raise ValueError for validation, propagate SQL errors

#### Users Repository (`users_repo.py`)
```python
def user_exists(cursor: MySQLCursor, username: str) -> bool:
    """Check if user exists in database."""

def create_user(cursor: MySQLCursor, username: str, password_hash: str, salt: str, **params) -> int:
    """Create user and return entity ID."""

def delete_user(cursor: MySQLCursor, username: str) -> None:
    """Delete user and all related records."""

def modify_user_parameter(cursor: MySQLCursor, username: str, parameter: str, value: str) -> None:
    """Modify user account parameter."""

def change_user_password(cursor: MySQLCursor, username: str, new_password_hash: str, salt: str) -> None:
    """Change user password with new salt."""

def list_users(cursor: MySQLCursor) -> List[str]:
    """List all users alphabetically."""
```

#### UserGroups Repository (`usergroups_repo.py`)
```python
def usergroup_exists(cursor: MySQLCursor, group_name: str) -> bool:
    """Check if user group exists."""

def create_usergroup(cursor: MySQLCursor, group_name: str) -> int:
    """Create user group and return entity ID."""

def delete_usergroup(cursor: MySQLCursor, group_name: str) -> None:
    """Delete user group and all related records."""

def add_user_to_group(cursor: MySQLCursor, username: str, group_name: str) -> None:
    """Add user to user group."""

def remove_user_from_group(cursor: MySQLCursor, username: str, group_name: str) -> None:
    """Remove user from user group."""

def list_usergroups(cursor: MySQLCursor) -> List[str]:
    """List all user groups alphabetically."""
```

#### Connections Repository (`connections_repo.py`)
```python
def connection_exists(cursor: MySQLCursor, connection_name: str = None, connection_id: int = None) -> bool:
    """Check if connection exists by name or ID."""

def create_connection(cursor: MySQLCursor, protocol: str, name: str, hostname: str, port: int, **params) -> int:
    """Create connection and return connection ID."""

def delete_connection(cursor: MySQLCursor, connection_id: int) -> None:
    """Delete connection and all related records."""

def modify_connection_parameter(cursor: MySQLCursor, connection_id: int, parameter: str, value: str) -> None:
    """Modify connection parameter."""

def list_connections(cursor: MySQLCursor) -> List[ConnectionInfo]:
    """List connections with detailed information."""
```

#### ConnGroups Repository (`conngroups_repo.py`)
```python
def connection_group_exists(cursor: MySQLCursor, group_name: str = None, group_id: int = None) -> bool:
    """Check if connection group exists by name or ID."""

def create_connection_group(cursor: MySQLCursor, name: str, group_type: str, parent_id: int = None) -> int:
    """Create connection group and return group ID."""

def delete_connection_group(cursor: MySQLCursor, group_id: int) -> None:
    """Delete connection group and update children."""

def check_connection_group_cycle(cursor: MySQLCursor, group_id: int, parent_id: int) -> bool:
    """Check for circular hierarchy references."""

def modify_connection_group_parent(cursor: MySQLCursor, group_id: int, parent_id: int = None) -> None:
    """Change connection group parent."""
```

#### Permissions Repository (`permissions_repo.py`)
```python
# User → Connection permissions
def grant_user_connection_permission(cursor: MySQLCursor, username: str, connection_name: str) -> None:
    """Grant connection permission to user."""

def revoke_user_connection_permission(cursor: MySQLCursor, username: str, connection_name: str) -> None:
    """Revoke connection permission from user."""

# User → Connection Group permissions
def grant_user_conngroup_permission(cursor: MySQLCursor, username: str, group_name: str) -> None:
    """Grant connection group permission to user."""

def revoke_user_conngroup_permission(cursor: MySQLCursor, username: str, group_name: str) -> None:
    """Revoke connection group permission from user."""

# UserGroup → Connection permissions
def grant_usergroup_connection_permission(cursor: MySQLCursor, group_name: str, connection_name: str, group_path: str = None) -> None:
    """Grant connection permission to user group."""

def revoke_usergroup_connection_permission(cursor: MySQLCursor, group_name: str, connection_name: str, group_path: str = None) -> None:
    """Revoke connection permission from user group."""

# UserGroup → Connection Group permissions
def grant_usergroup_conngroup_permission(cursor: MySQLCursor, group_name: str, target_group_name: str, group_path: str = None) -> None:
    """Grant connection group permission to user group."""

def revoke_usergroup_conngroup_permission(cursor: MySQLCursor, group_name: str, target_group_name: str, group_path: str = None) -> None:
    """Revoke connection group permission from user group."""
```

## Facade Preservation Strategy

### GuacamoleDB Facade Design (`guac_db.py`)

**Goals:**
1. **100% API Compatibility**: All public method signatures preserved exactly
2. **Thin Orchestration**: Methods delegate to repositories (≤3 lines each)
3. **Transaction Management**: Context manager preserved in facade
4. **Config Loading**: Database connection setup remains in facade
5. **Utility Retention**: `_scrub_credentials()` and debug methods stay in facade

**Facade Structure (~400 lines):**
```python
class GuacamoleDB:
    # Config and connection management (preserve)
    def __init__(self, config_file: str = "db_config.ini", debug: bool = False) -> None
    def __enter__(self) -> "GuacamoleDB"
    def __exit__(self, exc_type, exc_value, traceback) -> None
    @staticmethod def read_config(config_file: str) -> ConnectionConfig
    def connect_db(self) -> MySQLConnection

    # Utility methods (preserve)
    def _scrub_credentials(self, message: str) -> str
    def debug_print(self, *args: Any, **kwargs: Any) -> None

    # Class attributes (preserve)
    CONNECTION_PARAMETERS = CONNECTION_PARAMETERS
    USER_PARAMETERS = USER_PARAMETERS

    # Delegation methods (thin wrappers)
    def user_exists(self, username: str) -> bool:
        return users_repo.user_exists(self.cursor, username)

    def create_user(self, username: str, password: str) -> None:
        password_hash, salt = self._hash_password(password)
        users_repo.create_user(self.cursor, username, password_hash, salt)

    # ... similar thin delegation for all methods
```

### Import Compatibility Plan

**Phase 5-9 (Repository Extraction):**
```python
# guacalib/__init__.py - UNCHANGED
from .db import GuacamoleDB

# CLI handlers - UNCHANGED
from guacalib.db import GuacamoleDB
```

**Phase 10 (Facade Creation):**
```python
# guacalib/__init__.py - UPDATED
from .guac_db import GuacamoleDB

# guacalib/db.py - DEPRECATED but functional
from .guac_db import GuacamoleDB
__all__ = ['GuacamoleDB']

# CLI handlers - UNCHANGED (still works)
from guacalib.db import GuacamoleDB  # Re-exports from guac_db.py
```

**External Library Users - NO CHANGES**
```python
# This import continues to work unchanged
from guacalib import GuacamoleDB
```

## Incremental Migration Path

### Phase-by-Phase Commitment

**Phase 5: Users Repository (Walking Skeleton)**
- Extract ~450 lines of user CRUD to `users_repo.py`
- Validate approach with full test suite
- Commit before proceeding

**Phase 6: UserGroups Repository**
- Extract ~350 lines of user group CRUD to `usergroups_repo.py`
- Update GuacamoleDB delegation
- Full test validation

**Phase 7: Connections Repository**
- Extract ~600 lines of connection CRUD to `connections_repo.py`
- Largest extraction - critical validation
- Full test validation

**Phase 8: ConnGroups Repository**
- Extract ~400 lines of connection group CRUD to `conngroups_repo.py`
- Hierarchy validation logic extraction
- Full test validation

**Phase 9: Permissions Repository**
- Extract ~500 lines of permission operations to `permissions_repo.py`
- Most complex domain (4 permission types × 2 operations)
- Full test validation

**Phase 10: Final Facade**
- Create `guac_db.py` with thin facade
- Update `__init__.py` import
- Deprecate `db.py` with re-export
- Update documentation

### Walking Skeleton Approach

**Why Phase 5 as Walking Skeleton:**
1. **Domain Complexity**: Users domain is straightforward (no hierarchy, simple CRUD)
2. **Test Coverage**: Extensive user test coverage validates extraction immediately
3. **Pattern Establishment**: Establishes repository pattern for subsequent phases
4. **Risk Mitigation**: Failure at this stage is easy to rollback

### Success Criteria Per Phase

**Each Phase Must Achieve:**
- [x] Code changes committed to git
- [x] All 132 bats test cases passing (100% green)
- [x] CLI handlers unchanged (verified with `git diff guacalib/cli_handle_*.py`)
- [x] Smoke tests passed manually
- [x] Repository functions are stateless (accept cursor, return data)
- [x] No SQL logic remains in db.py for extracted domain

### Rollback Strategy

**If Any Phase Fails:**
```bash
git reset --hard HEAD~1  # Rollback to previous phase
# All phases are independently reversible
# No phase depends on future phases
```

## Benefits of Repository Extraction

### Testability Improvements
- **Unit Testing**: Can test SQL logic without database context manager
- **Domain Isolation**: Test user logic without connection/group interference
- **Mock Testing**: Repository functions can be mocked for integration testing

### Maintainability Improvements
- **Single Responsibility**: Each file has clear, single purpose
- **Reduced Cognitive Load**: Developers can focus on one domain at a time
- **Easier Onboarding**: New developers understand one repository first
- **Safer Changes**: Modify connection logic without risk to user logic

### Code Quality Improvements
- **Clearer Contracts**: Repository function signatures are explicit
- **Reduced Duplication**: Single source of truth for each domain's SQL
- **Better Error Handling**: Centralized validation logic per domain
- **Consistent Patterns**: All repositories follow same design principles

## Conclusion

Phase 4 planning establishes clear commitment to repository extraction with:
- **Evidence-based approach**: Current pain points documented with line counts
- **Incremental delivery**: Each phase independently shippable
- **Walking skeleton**: Phase 5 validates approach before full commitment
- **Backwards compatibility**: Zero breaking changes for CLI handlers
- **Risk mitigation**: Each phase reversible with simple git rollback

**Ready to proceed to Phase 5 implementation.**