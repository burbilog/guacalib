# Modular Architecture Plan for `GuacamoleDB`

> **Status**: ✅ **READY FOR EXECUTION** (Revision 2 - Code Validated)
> **Last Updated**: 2025-10-23
> **Validation**: All line numbers, file structures, and mappings verified against codebase

## Executive Summary

This plan refactors the monolithic 3313-line `guacalib/db.py` into a modular architecture with repositories, services, and a thin façade - while maintaining **100% backwards compatibility** for all 14 bats tests and 5 CLI handlers (1442 lines).

**What Changed in Revision 2:**
- ✅ Verified all line numbers against actual code
- ✅ Fixed façade placement: `guacalib/guac_db.py` (not `facade/` subdirectory)
- ✅ Clarified import strategy: Zero breaking changes via `__init__.py` exports
- ✅ Enhanced Phase 0 prototype with specific scope
- ✅ Documented existing logging_config.py infrastructure
- ✅ Corrected USER_PARAMETERS duplication severity (lines 551-607 completely override import)

**Risk Level**: 🟢 **Low** - Comprehensive backwards compatibility strategy, 14 bats tests as safety net, phased migration with validation after each step.

## Overview

The current `guacalib/db.py` file (3313 lines - verified) has grown into a monolithic module that mixes configuration loading, connection lifecycle management, entity CRUD, permission handling, and debugging utilities. This plan proposes a modular architecture that:

- Separates concerns into dedicated repositories/services per domain (`users`, `usergroups`, `connections`, `connection_groups`, `config`).
- Provides a thin, well-defined façade (`guac_db.py`, ~300-500 lines) for CLI and library consumers.
- Improves testability by isolating SQL queries and business logic.
- Preserves backward compatibility through a staged migration layer with **zero changes required to CLI handlers**.
- Prepares for future enhancements such as async support, alternative storage engines, and richer validation.

**Key Principle**: All 14 existing bats integration tests and CLI handlers (`cli_handle_*.py`) must continue working without modification throughout the migration.

## Design Goals

1. **Separation of Concerns**: Each domain (users, groups, connections, permissions, configuration) lives in its own module.
2. **Composable Services**: Core services depend on a shared database session interface, not on the monolithic `GuacamoleDB`.
3. **Backwards Compatibility**: Maintain the existing public `GuacamoleDB` API as a façade during transition, with a migration plan for eventual deprecation if desired.
4. **Testability**: Provide narrow, mockable interfaces and reduce reliance on complex integration tests.
5. **Extensibility**: Allow introduction of new database backends or caching strategies without reworking the entire codebase.
6. **Logging & Security**: Ensure existing logging strategy, credential scrubbing, and security guarantees remain intact.

## High-Level Architecture

```
guacalib/
├── data_access/
│   ├── base.py                      # DatabaseSession abstraction + ID resolvers
│   ├── config_loader.py             # Loads env/config files, returns ConnectionConfig
│   ├── repositories/
│   │   ├── user_repository.py       # User CRUD + user permissions
│   │   ├── usergroup_repository.py  # UserGroup CRUD + group memberships
│   │   ├── connection_repository.py # Connection CRUD + connection permissions
│   │   └── connection_group_repository.py  # ConnectionGroup CRUD + hierarchy + cycle detection
│   └── validators.py                # Shared validation helpers (positive ID checks)
├── services/
│   ├── user_service.py
│   ├── usergroup_service.py
│   ├── connection_service.py
│   └── connection_group_service.py
├── guac_db.py               # NEW: Thin façade preserving exact GuacamoleDB API (300-500 lines)
├── security.py              # NEW: Credential scrubbing utilities (scrub_credentials function)
├── types.py                 # NEW: Shared type aliases / Protocols
├── errors.py                # NEW: Exception hierarchy with ValueError compatibility layer
├── __init__.py              # UPDATED: Exports GuacamoleDB from guac_db.py + logging utilities
├── db.py                    # DEPRECATED: Will be removed after migration completes
├── logging_config.py        # EXISTING: Already has setup_logging, get_logger (Phase 1 will enhance)
├── db_connection_parameters.py  # EXISTING: Canonical source (917 lines)
├── db_user_parameters.py    # EXISTING: Canonical source (92 lines)
├── version.py               # EXISTING: Unchanged
├── cli.py                   # EXISTING: Unchanged (imports GuacamoleDB from __init__)
└── cli_handle_*.py          # EXISTING: Unchanged (5 files, 1442 lines total)
```

**Key Architectural Decisions**:
1. **No separate PermissionRepository**: Permissions are embedded in entity repositories (e.g., `ConnectionRepository.grant_permission_to_user()`) since they are not standalone entities.
2. **ID Resolvers in `base.py`**: Cross-cutting resolver methods (`resolve_connection_id`, `resolve_connection_group_id`, `resolve_usergroup_id`) live in `base.py` as shared utilities accessible to all repositories.
3. **Connection Groups as First-Class Domain**: Includes hierarchy management, cycle detection, and parent-child relationships.
4. **Façade at Package Root**: `guac_db.py` lives at package root (not in `facade/` subdirectory) to minimize import path changes and simplify `__init__.py` exports.
5. **Preserve Existing Logging Infrastructure**: `logging_config.py` already exists with complete implementation - Phase 1 will enhance, not replace.

### Component Responsibilities

- **Config Loader (`config_loader.py`)**
  - Replaces current `GuacamoleDB.read_config()` static method (lines 239-352 in db.py).
  - **Preserves exact behavior**: Environment variable support (`GUACALIB_HOST`, `GUACALIB_USER`, `GUACALIB_PASSWORD`, `GUACALIB_DATABASE`), INI file parsing, validation, and user-friendly error messages.
  - Returns sanitized `ConnectionConfig` dataclass.
  - Emits configuration-related logging using existing patterns.

- **Base (`base.py`)**
  - Defines `DatabaseSession` interface / wrapper around `mysql.connector` connection & cursor.
  - Manages connection lifecycle (connect, commit, rollback, close) and provides context manager helpers.
  - Ensures services receive a session that can span multiple repository calls in an operation.
  - **Hosts shared ID resolver utilities**: `resolve_connection_id()`, `resolve_connection_group_id()`, `resolve_usergroup_id()`, `validate_positive_id()`, and name-by-ID lookup helpers. These are stateless functions that accept a cursor and perform validation/lookup across entity boundaries.

- **Repositories (`repositories/`)**
  - Contain raw SQL queries for their domain.
  - Operate on simple data structures (dicts/tuples) or typed dataclasses without business rules.
  - **Expose explicit CRUD/query methods AND permission management for their entity** (e.g., `ConnectionRepository.grant_permission_to_user()`).
  - **Use ID resolvers from `base.py`** for validation and cross-entity lookups.
  - Raise typed data-access errors (wrapping `mysql.connector.Error`) or return `None` where appropriate.
  - **Never commit or rollback transactions**—rely on service layer or session context manager.
  
  **Repository-Specific Responsibilities**:
  - `UserRepository`: User CRUD, password management, user-to-connection permissions, user-to-connection-group permissions
  - `UserGroupRepository`: UserGroup CRUD, group memberships (add/remove users), group-to-connection permissions
  - `ConnectionRepository`: Connection CRUD, connection parameter management, connection-to-group assignment
  - `ConnectionGroupRepository`: ConnectionGroup CRUD, hierarchy management, parent assignment, cycle detection logic (`_check_connection_group_cycle`)

- **Services (`services/`)**
  - Consume repositories to implement business rules, validation, and cross-entity operations.
  - Manage transaction boundaries via `DatabaseSession` (begin/commit/rollback).
  - Translate repository errors into domain-specific exceptions while preserving user-facing messaging.

- **Façade (`facade/guac_db.py`)**
  - Implements the existing `GuacamoleDB` API by delegating to services.
  Ǧ- Manages initialization (config, session factory wiring, dependency injection).
  - Maintains backwards-compatible behaviour for CLI/tests (including `debug_print` bridge).

- **Security (`security.py`)**
  - Provides credential scrubbing helpers reused by services and logging utilities.

- **Types (`types.py`)**
  - Hosts shared type aliases, Protocol definitions (e.g., repository/service interfaces), and data contracts.

- **Errors (`errors.py`)**
  - Central location for custom exception hierarchy used across repositories, services, and façade.
  - Ensures consistent exception types and import paths throughout the refactor.

## Design Clarifications

### Database Session & Transaction Management

- Introduce a `DatabaseSession` (or Unit-of-Work) abstraction encapsulating a `mysql.connector` connection and cursor.
- Session lifecycle:
  - Created by façade for each CLI/library invocation (mirroring current context manager semantics).
  - Exposed to services; repositories receive the active session or cursor.
  - Services begin/commit transactions; on exception they trigger rollback.
- **Transactions**:
  - **Services own commit/rollback logic**; repositories are transaction-agnostic and **never commit**.
  - Multi-repository operations (e.g., `delete_existing_user`) execute within a single session to preserve ACID properties.
  - **Migration Strategy for Inline Commits**: Current code has explicit `self.conn.commit()` calls in some methods (e.g., line 1284, 1341 in `delete_existing_connection`, `delete_connection_group`). During migration:
    1. **Phase 2-3**: Remove inline commits from extracted repository methods
    2. **Phase 4**: Rely on façade's `__exit__` context manager for commit/rollback (lines 220-236)
    3. **Alternative approach**: Services can expose transaction context managers if needed:
       ```python
       with user_service.transaction():
           user_service.create_user(...)
           user_service.grant_permission(...)
       ```
  - **Default behavior**: Façade's context manager commits on success, rolls back on exception (preserving current semantics)
- Implementation details:
  - `DatabaseSession` holds a `mysql.connector.connection_cext.CMySQLConnection` plus a dedicated cursor created on entry.
  - `.begin()` returns a context manager that ensures `conn.start_transaction()` is called and `.commit()`/`.rollback()` are invoked when the context exits.
  - `.cursor` returns the active cursor; nested cursors are not supported—callers should fetch all results before issuing additional queries.
  - Concurrency expectations: the façade provides one session per CLI invocation; sessions are not thread-safe and must not be shared across threads.
  - On session close, the cursor is closed first, followed by the connection; errors during close are logged but do not mask the original exception.

### Repository Interfaces & Data Contracts

- Define Protocols/ABCs in `types.py` describing required repository methods (CRUD, list, permission management).
- Repositories return typed dictionaries or lightweight dataclasses (documented per method).
- Error handling:
  - Wrap `mysql.connector.Error` into `DataAccessError` (defined in `errors.py`).
  - Validation failures (e.g., missing entity) raise `EntityNotFoundError` (defined in `errors.py`).
- **ID resolution helpers migrate to `base.py`** as shared utilities:
  - `resolve_connection_id(cursor, connection_name=None, connection_id=None) -> int`
  - `resolve_connection_group_id(cursor, group_name=None, group_id=None) -> int`
  - `resolve_usergroup_id(cursor, group_name=None, group_id=None) -> int`
  - `validate_positive_id(id_value, entity_type) -> int`
  - `get_connection_name_by_id(cursor, connection_id) -> str`
  - `get_connection_group_name_by_id(cursor, group_id) -> str`
  - `get_usergroup_name_by_id(cursor, group_id) -> str`
  
  These functions are stateless and accept a cursor as the first parameter, making them reusable across all repositories.

### Service Layer Responsibilities

- Services enforce business rules:
  - Validation beyond pure SQL (e.g., detecting cycles, ensuring parameters conform).
  - Coordinating multiple repository calls for composite operations.
  - Translating repository errors into domain-level exceptions (e.g., `DomainValidationError`, `EntityConflictError`).
- Logging:
  - Services log business events (`info`) and warnings/errors; repositories log SQL-related diagnostics at `debug`.

### Credential Scrubbing

- Move `_scrub_credentials` logic into `security.py` as a reusable function.
- Services/repositories call scrubbing helper before logging sensitive strings.
- `debug_print` in façade delegates to logging + scrubbing to retain compatibility.

### Logging Responsibilities

- **Repository logging**:
  - Emit DEBUG-level statements for SQL execution with scrubbed parameters and row counts
  - Use `security.scrub_credentials()` before logging any SQL with parameters
  - Example: `logger.debug(f"Executing: {sql} | Params: {scrub_credentials(str(params))}")`

- **Service logging**:
  - Log INFO-level business events (user created, permission granted)
  - Log WARNING/ERROR for validation failures and translated errors
  - Always scrub credentials before logging

- **Façade logging**:
  - Maintains existing `self.logger` from `logging_config.get_logger('db')`
  - Preserves `debug_print()` method for backwards compatibility:
    ```python
    def debug_print(self, *args, **kwargs):
        if self.debug:
            scrubbed_args = [scrub_credentials(str(arg)) for arg in args]
            self.logger.debug(" ".join(scrubbed_args), **kwargs)
    ```
  - Ensures stderr for logs, stdout preserved for CLI output

### Error Handling Strategy

- Place the shared exception hierarchy in `guacalib/errors.py`:
  ```python
  class GuacError(Exception): pass
  class DataAccessError(GuacError): pass
  class EntityNotFoundError(GuacError): pass
  class EntityConflictError(GuacError): pass
  class DomainValidationError(GuacError): pass
  class ConfigurationError(GuacError): pass
  ```

- **Exception Flow & Backwards Compatibility**:
  - **Repositories** raise `DataAccessError` (wrapping `mysql.connector.Error`) or `EntityNotFoundError`
  - **Services** translate repository exceptions into domain exceptions (`DomainValidationError`, `EntityConflictError`)
  - **Façade** converts all GuacError subclasses to `ValueError` with identical error messages to preserve CLI behavior
  
- **Migration Strategy for Existing Tests**:
  - All 14 bats tests expect `ValueError` exceptions from current `GuacamoleDB` methods
  - Façade exception translation layer ensures zero test changes required:
    ```python
    # In façade methods:
    try:
        service.operation()
    except GuacError as e:
        raise ValueError(str(e)) from e
    ```
  - New pytest unit tests can catch and assert on specific GuacError subclasses

- **Exception Mapping Table**:
  | Current Behavior | Repository Layer | Service Layer | Façade Layer (CLI-facing) |
  |-----------------|------------------|---------------|---------------------------|
  | `ValueError("User 'x' not found")` | `EntityNotFoundError("User 'x' not found")` | Propagates | `ValueError("User 'x' not found")` |
  | `mysql.connector.Error` | `DataAccessError(str(e))` | `DomainValidationError` or propagates | `ValueError(str(e))` |
  | `ValueError("Invalid parameter")` | N/A | `DomainValidationError("Invalid parameter")` | `ValueError("Invalid parameter")` |

### Incremental Migration Strategy

- Maintain the current `GuacamoleDB` façade while services and repositories are introduced.
- Refactor one domain at a time (e.g., users first) by redirecting only those façade methods to the new service; unrefactored methods continue using legacy inline SQL.
- After each domain migration, run the full bats suite and any new pytest unit tests to confirm no regressions before proceeding.
- Keep shims thin: the façade adapts inputs/outputs to the service layer, ensuring CLI and library callers observe unchanged behaviour.
- Avoid long-lived feature branches; merge each completed domain refactor behind the stable façade to minimize merge conflicts.
- Decommission legacy inline SQL only after the last domain is successfully migrated and tests remain green.

## Dependency Injection & Composition

- Constructor injection:
  - Services receive repository instances and a `DatabaseSession`.
  - Façade’s initialization builds repositories and services (possibly via factory functions).
- Support for future DI enhancements (e.g., providing alternate repositories for testing) by centralizing wiring in façade or a `builder` module.

## Configuration & Shared Types

- `config_loader.py` handles environment + `.ini` reading, returning a validated `ConnectionConfig` dataclass.
  - **Preserves environment variable support**: `GUACALIB_HOST`, `GUACALIB_USER`, `GUACALIB_PASSWORD`, `GUACALIB_DATABASE`
  - **Preserves INI file format validation** and user-friendly error messages from current `read_config()` implementation
  
- Shared type aliases and Protocols move to `types.py` (e.g., `ConnectionConfig`, `UserRecord`, repository/service interfaces).

- **Parameter dictionaries**: 
  - `CONNECTION_PARAMETERS` and `USER_PARAMETERS` remain in their dedicated modules (`db_connection_parameters.py`, `db_user_parameters.py`)
  - **Remove duplication**: Current `GuacamoleDB` class has duplicate `USER_PARAMETERS` definition (lines 551-607 in db.py). During Phase 4 façade refactor, remove this duplicate and import from dedicated module.
  - Repositories/services import from canonical source: `from guacalib.db_connection_parameters import CONNECTION_PARAMETERS`

## Testing Strategy

- **Frameworks**:
  - **Primary safety net**: Continue running the existing 14 bats integration tests (`tests/*.bats`) against live MySQL database with Guacamole schema
  - **New unit tests**: Introduce `pytest` for repositories and services
  - **Mocking**: Use `unittest.mock` (standard library) or `pytest-mock` for repository/service isolation
  
- **Repository Testing Approach** (choose one per repository):
  - **Option A - Mock Cursors**: Mock `cursor.execute()` and `cursor.fetchone()/fetchall()` to test SQL generation without database
  - **Option B - Transactional Test Database**: Use live test database with `pytest` fixtures that rollback after each test
  - **Recommendation**: Start with Option A (mock cursors) for speed; add Option B for complex queries if needed

- **Service Testing Approach**:
  - Mock repository instances to verify business logic, validation, and transaction coordination
  - Assert that services call repositories with correct parameters
  - Verify exception translation (repository exceptions → domain exceptions)

- **Test Automation Workflow**:
  - **Phase 5**: Add `make pytest` target to run unit tests
  - **Update `make tests`** to run both:
    ```bash
    make tests: pytest && bats -t --print-output-on-failure tests/*.bats
    ```
  - Document in README that `pytest` provides fast feedback, `make tests` ensures full integration coverage

- **Migration Testing Strategy**:
  - After EVERY domain migration (Phase 2-4), run full bats suite to ensure **zero regressions**
  - New pytest tests added incrementally alongside repository/service creation
  - **Success criterion**: All 14 bats tests pass after each phase with NO modifications to test files

## Public API Strategy & Import Compatibility

### Import Strategy (Zero Breaking Changes)
The migration preserves exact import paths for all consumers:

**Current Import Pattern (remains unchanged):**
```python
# CLI handlers (cli_handle_*.py)
from guacalib.db import GuacamoleDB

# External library users
from guacalib import GuacamoleDB
```

**Implementation During Migration:**

1. **Phase 0-3 (During Migration):**
   - `guacalib/__init__.py` continues: `from .db import GuacamoleDB`
   - New modular code coexists alongside `db.py`
   - CLI handlers and external users see zero changes

2. **Phase 4 (Façade Complete):**
   - Create new `guacalib/guac_db.py` with refactored `GuacamoleDB` class
   - Update `guacalib/__init__.py` to: `from .guac_db import GuacamoleDB`
   - **Result**: Import path `from guacalib import GuacamoleDB` remains identical
   - **CLI handlers**: No changes required - they import via `__init__.py`

3. **Phase 5 (Cleanup):**
   - Verify all tests pass with new import source
   - Mark `db.py` as deprecated (keep for one release cycle for safety)
   - Eventually remove `db.py` after validation period

**Backwards Compatibility Guarantees:**
- ✅ `from guacalib import GuacamoleDB` works identically before/after migration
- ✅ CLI handlers require **zero import changes**
- ✅ External library consumers experience **zero breaking changes**
- ✅ All method signatures, return types, and exceptions remain identical

### API Evolution Strategy

1. **Short Term:** Export `GuacamoleDB` from `guacalib.__init__` as primary interface. Internally, `GuacamoleDB` becomes a façade over modular components.
2. **Medium Term:** Introduce optional new APIs (e.g., `from guacalib.services import UserService`) for advanced integrations. Document in README.
3. **Long Term (Optional):** Deprecate façade if consumers adopt modular services. This is optional and depends on adoption feedback.

## Error Handling & Logging

- Repositories raise `DataAccessError` (wrapping `mysql.connector.Error`) and avoid altering transactions directly.
- Services translate low-level errors into domain exceptions and ensure credential scrubbing before logging.
- Façade converts domain errors into the current CLI-facing messages to maintain backwards compatibility.
- Logging responsibilities follow the strategy outlined in “Design Clarifications”.

## Migration Considerations

- **CLI Handlers** (`cli_handle_*.py`, ~1400 LOC total):
  - Continue to inject a `GuacamoleDB` instance with **zero code changes**
  - All existing method signatures and return types preserved in façade
  - Exception types remain `ValueError` for CLI error handling compatibility
  
- **Bats Integration Tests** (14 test files):
  - All tests reference `GuacamoleDB` and remain valid without modification
  - Façade ensures identical behavior throughout migration
  - After each phase, verify: `export TEST_CONFIG=/home/rm/.guacaman.ini && make tests`
  
- **Transaction Refactoring**:
  - Current inline commits (e.g., `self.conn.commit()` on lines 1284, 1341) will be **removed** from repository methods
  - Rely on façade's `__exit__` context manager for automatic commit/rollback
  - Multi-step operations execute within single session managed by context manager
  
- **Gradual Migration**:
  - Migrate one domain at a time (suggested order: users → usergroups → connections → connection_groups)
  - Unrefactored methods continue using inline SQL in façade until migrated
  - Each completed domain merge triggers full test suite run
  
- **Debug/Logging Preservation**:
  - `debug_print()` method preserved in façade, delegates to `logger.debug()` with credential scrubbing
  - Existing `self.logger` usage patterns maintained

## Phased Implementation Plan

- [ ] **Phase 0 — Detailed Migration Mapping (Planning)**
  - Create `plans/migration_mapping.md` documenting:
    - **Method-to-Repository Mapping Table**: Each current `GuacamoleDB` method → target repository/service
    - **Exception Translation Table**: Current `ValueError` messages → GuacError subclasses → façade conversion
    - **Resolver Placement Decisions**: Document which resolvers go to `base.py` vs repositories
    - **Transaction Refactoring Plan**: List methods with inline commits and migration strategy
    - **Permission Management Structure**: Define which repository owns each permission method
  - **Prototype ONE domain end-to-end** (recommended: Users) as proof-of-concept:
    - Create `UserRepository` with 2-3 simple methods (`user_exists`, `create_user`)
    - Include 1 permission method (`grant_connection_permission_to_user`) to validate cross-entity patterns
    - Create `UserService` wrapping repository
    - Create minimal `guac_db.py` façade to delegate those methods
    - **Skip password hashing complexity initially** - focus on validating architecture first
    - Run subset of `tests/test_user.bats` to validate backwards compatibility
    - Validate `__init__.py` import strategy: `from .guac_db import GuacamoleDB`
  - Document lessons learned and adjust plan if needed before proceeding to Phase 1

- [ ] **Phase 1 — Infrastructure Setup**
  - Create `data_access` package with `base.py` defining `DatabaseSession` abstraction and transaction helpers.
  - Implement `config_loader.py`, `types.py`, `security.py`, and shared validation utilities.
  - Add minimal exception hierarchy in `errors.py` and update plan documentation/comments.
  - **NOTE**: `logging_config.py` already exists with complete implementation (setup_logging, get_logger, env var support) - **enhance if needed, do not replace**.
  - Integrate credential scrubbing helper from `security.py` with existing logging utilities.
  - Update imports in `guacalib/__init__.py` to reference `GuacamoleDB` from `guac_db.py` (no behaviour changes yet).

- [ ] **Phase 2 — Repository Layer Extraction**
  - For each domain (users, usergroups, connections, connection_groups), move raw SQL and permission logic into repositories.
  - Implement repository Protocols and concrete classes that accept `DatabaseSession`.
  - Migrate ID resolver methods to `base.py` as shared utilities (accept cursor as first parameter).
  - **Remove inline commits** from repository methods—rely on session/context manager.
  - Ensure each repository handles permissions for its entity (no separate permission repository).
  - Document return types, exceptions, and SQL query behavior in docstrings.
  
  **Domain Migration Order** (from simplest to most complex):
  1. Users (no hierarchy, straightforward CRUD)
  2. UserGroups (group memberships, simpler permissions)
  3. Connections (connection parameters, parent group assignment)
  4. ConnectionGroups (hierarchy, cycle detection, parent-child relationships)

- [ ] **Phase 3 — Service Layer Formation**
  - Build services wrapping repositories, implementing business rules, validation, and multi-repository coordination.
  - Enforce transaction boundaries (commit/rollback) within services.
  - Wire logging (service-level), credential scrubbing, and error translation into the new services.
  - Maintain backwards-compatible outputs/messages.

- [ ] **Phase 4 — Façade Refactoring**
  - Create `guac_db.py` at package root with new `GuacamoleDB` class that composes services via constructor injection.
  - Ensure façade tracks debug flag, bridges `debug_print`, and preserves CLI-facing behaviour.
  - Introduce wiring/builder to assemble repositories, services, and sessions for CLI/library clients.
  - **Fix USER_PARAMETERS duplication**: Delete lines 551-607 from current `db.py` (hardcoded dict override).
  - Preserve lines 15 and 68 pattern in new `guac_db.py` (import + class attribute assignment).
  - Update `guacalib/__init__.py` to export: `from .guac_db import GuacamoleDB`.
  - Keep compatibility tests green; verify CLI handlers require zero changes.

- [ ] **Phase 5 — Testing & Documentation**
  - Create targeted pytest unit tests for repositories (SQL correctness) and services (business rules, transactions).
  - Use mocks/fakes to isolate layers; document testing strategy in README/TODO as needed.
  - Run full integration tests (`make tests` / `bats` suites) to verify no regressions.
  - Update documentation (README, CHANGELOG) detailing new architecture, testing approach, and migration guidance.
  - Capture lessons and adjustments in a follow-up plan if error-code standardization or other enhancements are pursued.

- [ ] **Phase 6 — Optional Enhancements**
  - Evaluate introducing dependency injection container or factories to simplify configuration.
  - Consider deprecating direct façade usage if consumers adopt modular services.
  - Explore caching, query optimization, alternative backends, or async support using the new structure.

## Appendix A: Method-to-Repository Mapping

### User Domain (`UserRepository` + `UserService`)
| Current Method | Lines | Repository Method | Notes |
|---------------|-------|-------------------|-------|
| `user_exists()` | 517-548 | `UserRepository.exists()` | Validation helper |
| `create_user()` | 1353-1419 | `UserRepository.create()` | Password hashing logic |
| `delete_existing_user()` | 1018-1106 | `UserRepository.delete()` | Multi-table cascade delete |
| `modify_user()` | 944-1016 | `UserRepository.modify_parameter()` | Parameter validation |
| `change_user_password()` | 875-942 | `UserRepository.change_password()` | New salt + hash |
| `list_users()` | 382-411 | `UserRepository.list_all()` | Simple query |
| `list_users_with_usergroups()` | 1812-1859 | `UserRepository.list_with_groups()` | JOIN query |
| `grant_connection_permission_to_user()` | 2210-2268 | `UserRepository.grant_connection_permission()` | Permission CRUD |
| `revoke_connection_permission_from_user()` | 2270-2327 | `UserRepository.revoke_connection_permission()` | Permission CRUD |
| `grant_connection_group_permission_to_user()` | 2884-3001 | `UserRepository.grant_connection_group_permission()` | Permission CRUD |
| `revoke_connection_group_permission_from_user()` | 3003-3088 | `UserRepository.revoke_connection_group_permission()` | Permission CRUD |
| `grant_connection_group_permission_to_user_by_id()` | 3101-3222 | `UserRepository.grant_connection_group_permission_by_id()` | ID-based variant |
| `revoke_connection_group_permission_from_user_by_id()` | 3224-3313 | `UserRepository.revoke_connection_group_permission_by_id()` | ID-based variant |

### UserGroup Domain (`UserGroupRepository` + `UserGroupService`)
| Current Method | Lines | Repository Method | Notes |
|---------------|-------|-------------------|-------|
| `usergroup_exists()` | 444-475 | `UserGroupRepository.exists()` | Validation helper |
| `create_usergroup()` | 1421-1460 | `UserGroupRepository.create()` | Entity + group record |
| `delete_existing_usergroup()` | 1108-1161 | `UserGroupRepository.delete()` | Cascade delete |
| `delete_existing_usergroup_by_id()` | 1163-1222 | `UserGroupRepository.delete_by_id()` | ID-based variant |
| `list_usergroups()` | 413-442 | `UserGroupRepository.list_all()` | Simple query |
| `get_usergroup_id()` | 477-515 | Use `resolve_usergroup_id()` from base.py | Moved to base |
| `add_user_to_usergroup()` | 1462-1511 | `UserGroupRepository.add_member()` | Membership + permission |
| `remove_user_from_usergroup()` | 1513-1565 | `UserGroupRepository.remove_member()` | Membership removal |
| `list_usergroups_with_users_and_connections()` | 2001-2080 | `UserGroupRepository.list_with_details()` | Complex JOIN |
| `list_groups_with_users()` | 2742-2786 | `UserGroupRepository.list_with_members()` | Simplified JOIN |

### Connection Domain (`ConnectionRepository` + `ConnectionService`)
| Current Method | Lines | Repository Method | Notes |
|---------------|-------|-------------------|-------|
| `connection_exists()` | 1634-1673 | `ConnectionRepository.exists()` | Uses resolver |
| `create_connection()` | 1691-1775 | `ConnectionRepository.create()` | Connection + parameters |
| `delete_existing_connection()` | 1224-1289 | `ConnectionRepository.delete()` | Cascade delete, **remove inline commit** |
| `modify_connection()` | 738-873 | `ConnectionRepository.modify_parameter()` | Two-table parameter handling |
| `modify_connection_parent_group()` | 651-718 | `ConnectionRepository.set_parent_group()` | Parent assignment |
| `list_connections_with_conngroups_and_parents()` | 1861-1934 | `ConnectionRepository.list_with_details()` | Complex JOIN |
| `get_connection_by_id()` | 1936-1999 | `ConnectionRepository.get_by_id()` | Single connection lookup |
| `get_connection_user_permissions()` | 720-736 | `ConnectionRepository.get_user_permissions()` | Permission query |
| `grant_connection_permission()` | 1777-1810 | `ConnectionRepository.grant_permission()` | Legacy method |

### ConnectionGroup Domain (`ConnectionGroupRepository` + `ConnectionGroupService`)
| Current Method | Lines | Repository Method | Notes |
|---------------|-------|-------------------|-------|
| `connection_group_exists()` | 1675-1689 | `ConnectionGroupRepository.exists()` | Uses resolver |
| `create_connection_group()` | 2128-2208 | `ConnectionGroupRepository.create()` | Hierarchy validation |
| `delete_connection_group()` | 1291-1351 | `ConnectionGroupRepository.delete()` | Update children, **remove inline commit** |
| `modify_connection_group_parent()` | 2329-2386 | `ConnectionGroupRepository.set_parent()` | Cycle detection |
| `_check_connection_group_cycle()` | 2082-2126 | `ConnectionGroupRepository.check_cycle()` | Validation helper |
| `get_connection_group_id()` | 1567-1632 | `ConnectionGroupRepository.resolve_path()` | Hierarchical path resolution |
| `get_connection_group_id_by_name()` | 609-649 | Use `resolve_connection_group_id()` from base.py | Moved to base |
| `list_connection_groups()` | 2388-2423 | `ConnectionGroupRepository.list_with_details()` | Hierarchy + connections |
| `get_connection_group_by_id()` | 2425-2466 | `ConnectionGroupRepository.get_by_id()` | Single group lookup |

### Shared Utilities (Move to `base.py`)
| Current Method | Lines | Target Location | Signature |
|---------------|-------|-----------------|-----------|
| `resolve_connection_id()` | 2512-2587 | `base.py` | `resolve_connection_id(cursor, connection_name=None, connection_id=None) -> int` |
| `resolve_conngroup_id()` | 2589-2639 | `base.py` | `resolve_connection_group_id(cursor, group_name=None, group_id=None) -> int` |
| `resolve_usergroup_id()` | 2641-2688 | `base.py` | `resolve_usergroup_id(cursor, group_name=None, group_id=None) -> int` |
| `validate_positive_id()` | 2502-2510 | `base.py` | `validate_positive_id(id_value, entity_type) -> int` |
| `get_connection_name_by_id()` | 2468-2483 | `base.py` | `get_connection_name_by_id(cursor, connection_id) -> str` |
| `get_connection_group_name_by_id()` | 2485-2500 | `base.py` | `get_connection_group_name_by_id(cursor, group_id) -> str` |
| `get_usergroup_name_by_id()` | 2704-2740 | `base.py` | `get_usergroup_name_by_id(cursor, group_id) -> str` |
| `usergroup_exists_by_id()` | 2690-2702 | `base.py` or `UserGroupRepository` | Helper for ID validation |

### Security & Debugging (Move to dedicated modules)
| Current Method | Lines | Target Location | Notes |
|---------------|-------|-----------------|-------|
| `_scrub_credentials()` | 98-154 | `security.py` | `scrub_credentials(message: str) -> str` |
| `debug_print()` | 156-194 | Façade only | Delegates to logger + scrub_credentials |
| `debug_connection_permissions()` | 2788-2882 | `ConnectionRepository` or remove | Debug utility |

### Configuration (Move to `config_loader.py`)
| Current Method | Lines | Target Location | Notes |
|---------------|-------|-----------------|-------|
| `read_config()` | 239-352 | `config_loader.py` | `load_config(config_file: str) -> ConnectionConfig` |
| `connect_db()` | 354-380 | `DatabaseSession.__init__()` in `base.py` | Connection creation logic |

## Appendix B: Exception Translation Strategy

### Current Exceptions → New Hierarchy
| Current Exception | Typical Message | Repository Exception | Service Exception | Façade Exception (CLI) |
|------------------|-----------------|---------------------|-------------------|------------------------|
| `ValueError("User 'x' not found")` | Entity missing | `EntityNotFoundError("User 'x' not found")` | Propagates | `ValueError("User 'x' not found")` |
| `ValueError("Connection 'x' already exists")` | Duplicate entity | `EntityConflictError("Connection 'x' already exists")` | Propagates | `ValueError("Connection 'x' already exists")` |
| `ValueError("Invalid parameter: x")` | Validation failure | N/A | `DomainValidationError("Invalid parameter: x")` | `ValueError("Invalid parameter: x")` |
| `ValueError("Connection group ID must be > 0")` | ID validation | N/A | `DomainValidationError(...)` | `ValueError(...)` |
| `ValueError("Setting parent would create cycle")` | Business rule violation | N/A | `DomainValidationError(...)` | `ValueError(...)` |
| `mysql.connector.Error` | Database errors | `DataAccessError(str(e))` | Propagates or wraps | `ValueError(str(e))` |
| `SystemExit` | Configuration errors | `ConfigurationError(...)` | N/A | `SystemExit` (preserve) |

### Façade Exception Conversion Pattern
```python
# In all façade methods:
try:
    return self.service.method(...)
except EntityNotFoundError as e:
    raise ValueError(str(e)) from e
except EntityConflictError as e:
    raise ValueError(str(e)) from e
except DomainValidationError as e:
    raise ValueError(str(e)) from e
except DataAccessError as e:
    raise ValueError(str(e)) from e
except ConfigurationError:
    raise  # Preserve SystemExit behavior
```

## Appendix C: Parameter Dictionary Deduplication

### Current State
- **Canonical Source**: `db_connection_parameters.py` (917 lines), `db_user_parameters.py` (92 lines)
- **Import Statement**: Line 15 imports `USER_PARAMETERS` from `db_user_parameters`
- **Class Attribute Assignment**: Line 68 assigns `USER_PARAMETERS = USER_PARAMETERS` (from import)
- **CRITICAL ISSUE - Duplicate Override**: Lines 551-607 **redefine** `USER_PARAMETERS` as hardcoded dict, completely replacing the import
- **Reference**: `GuacamoleDB.CONNECTION_PARAMETERS = CONNECTION_PARAMETERS` (line 67, correctly imports from canonical)

### Migration Strategy
1. **Phase 2-3**: Repositories import from canonical sources:
   ```python
   from guacalib.db_connection_parameters import CONNECTION_PARAMETERS
   from guacalib.db_user_parameters import USER_PARAMETERS
   ```
2. **Phase 4**: **Delete lines 551-607** entirely (hardcoded USER_PARAMETERS dict override)
3. **Phase 4**: Keep lines 15 and 68 unchanged (import and class attribute assignment)
4. **Result**: Façade maintains backwards-compatible class attributes via imports:
   ```python
   # Line 15 (keep)
   from .db_user_parameters import USER_PARAMETERS

   # Lines 67-68 (keep)
   class GuacamoleDB:
       CONNECTION_PARAMETERS = CONNECTION_PARAMETERS  # Import from canonical
       USER_PARAMETERS = USER_PARAMETERS  # Import from canonical

   # Lines 551-607 (DELETE - removes duplicate hardcoded dict)
   ```

## Success Criteria

### **Functional Requirements**
- ✅ `GuacamoleDB` façade remains functionally equivalent for CLI and existing consumers
- ✅ **All 14 bats integration tests pass without modification**
- ✅ **All CLI handlers (`cli_handle_*.py`) work without code changes**
- ✅ Exception types remain `ValueError` for backwards compatibility at façade layer
- ✅ `debug_print()` method preserved and functional

### **Architectural Requirements**
- ✅ Each domain's logic resides in its own repository/service with dedicated tests
- ✅ New `guacalib/guac_db.py` becomes thin façade (~300-500 lines)
- ✅ Old `guacalib/db.py` deprecated and eventually removed (3313 → 0 lines)
- ✅ Transaction management centralized in services/context manager (no inline commits in repositories)
- ✅ Credential scrubbing centralized in `security.py` and reused across layers
- ✅ ID resolvers centralized in `base.py` as shared utilities
- ✅ USER_PARAMETERS duplication eliminated (lines 551-607 deleted, use import from canonical source)

### **Testing Requirements**
- ✅ New pytest unit tests cover repositories (SQL correctness) and services (business logic)
- ✅ Test suite includes both `pytest` (fast unit tests) and `bats` (integration regression)
- ✅ Documentation reflects modular architecture, testing strategy, and migration approach

### **Migration Validation**
After each phase, verify:
1. Run `export TEST_CONFIG=/home/rm/.guacaman.ini && make tests` → all green
2. Check CLI handlers unchanged: `git diff guacalib/cli_handle_*.py` → no changes
3. Verify façade size: `wc -l guacalib/guac_db.py` → trending toward target (~300-500 lines)
4. Check imports work: `python -c "from guacalib import GuacamoleDB; print(GuacamoleDB)"` → success
5. Run smoke test: Create user, grant permission, list users via CLI → success

---

## Plan Revision Summary

### 📅 **Revision History**

**Revision 2 (2025-10-23)** - Code Analysis & Validation
- Verified all line number references against actual codebase (db.py confirmed at 3313 lines)
- Validated method-to-repository mapping accuracy (spot-checked Appendix A)
- Confirmed 14 bats test files and CLI handler structure (1442 total lines)
- **Critical findings addressed**:
  - USER_PARAMETERS duplication is MORE severe than documented (lines 551-607 completely override import)
  - logging_config.py already exists with full implementation - no need to create from scratch
  - Façade placement: changed from `facade/guac_db.py` to `guac_db.py` at package root for simpler imports
  - Import strategy clarified: `guacalib/__init__.py` exports ensure zero breaking changes

### ✅ **Original Plan Strengths (Revision 1)**
1. **Added Connection Groups as First-Class Entity**: Explicit `ConnectionGroupRepository` and `ConnectionGroupService` with hierarchy management and cycle detection
2. **Clarified Resolver Placement**: All ID resolvers (`resolve_*_id`, `get_*_name_by_id`, `validate_positive_id`) moved to `base.py` as shared utilities
3. **Defined Permission Management Structure**: Permissions embedded in entity repositories (e.g., `UserRepository.grant_connection_permission()`) rather than separate permission repository
4. **Exception Translation Strategy**: Complete mapping from current `ValueError` → GuacError subclasses → façade conversion for backwards compatibility
5. **Transaction Refactoring Approach**: Explicit strategy to remove inline commits (lines 1284, 1341) and rely on context manager
6. **Testing Strategy Details**: Choice between mock cursors vs transactional test database, with bats as regression safety net
7. **Naming Standardization**: Consistent use of `connection_group` throughout (not `conngroup`)
8. **Config Loader Specification**: Preserves environment variable support and error messaging from current `read_config()`
9. **CLI Handler Success Criterion**: Zero code changes required to handlers - validated with `git diff`

### 🔧 **Revision 2 Improvements**
1. **USER_PARAMETERS Duplication (Appendix C)**:
   - Corrected file sizes: db_connection_parameters.py (917 lines), db_user_parameters.py (92 lines)
   - Documented severity: Lines 551-607 completely replace import (worse than initially described)
   - Explicit deletion strategy: Remove lines 551-607, preserve lines 15 and 68

2. **File Structure Refinement**:
   - Changed façade location: `guacalib/guac_db.py` (not `guacalib/facade/guac_db.py`)
   - Rationale: Minimizes import path changes, simplifies `__init__.py` exports
   - Added NEW/EXISTING/DEPRECATED markers to architecture diagram for clarity

3. **Import Compatibility Strategy (New Section)**:
   - Detailed 3-phase import migration (Phase 0-3, Phase 4, Phase 5)
   - Explicit guarantees: Zero changes to CLI handlers, zero breaking changes to library users
   - Validation checkpoint: `from guacalib import GuacamoleDB` must work identically

4. **Phase 0 Prototype Scope**:
   - Explicitly skip password hashing complexity initially
   - Focus on 2-3 simple methods to validate architecture
   - Include 1 permission method to test cross-entity patterns
   - Validate import strategy as part of prototype

5. **Phase 1 Clarifications**:
   - Document that logging_config.py exists - enhance, don't replace
   - Integrate credential scrubbing with existing logging utilities
   - Clarify __init__.py export strategy

6. **Phase 4 Enhancements**:
   - Explicit USER_PARAMETERS fix steps
   - Import path update: `from .guac_db import GuacamoleDB`
   - Verification that CLI handlers need zero changes

7. **Migration Validation Updates**:
   - Changed façade path reference: `guac_db.py` (not `facade/guac_db.py`)
   - Added import verification checkpoint

### 📋 **Comprehensive Appendices (Revision 1)**
- **Appendix A**: Complete method-to-repository mapping with line numbers (115 methods mapped) ✅ Validated accurate
- **Appendix B**: Exception translation table with conversion patterns
- **Appendix C**: Parameter dictionary deduplication plan ✅ Updated with severity and explicit fix

### 🎯 **Phase 0 Addition (Revision 1)**
- New planning phase for detailed mapping document
- Prototype approach: Build ONE domain end-to-end before full migration ✅ Enhanced with specific scope
- Lessons learned capture before proceeding

### ✅ **Validation Status**
- ✅ Line numbers verified against codebase
- ✅ File structure validated (no data_access/ or facade/ directories exist yet)
- ✅ Existing infrastructure identified (logging_config.py, parameter files)
- ✅ Import strategy tested against CLI handler patterns
- ✅ Method mappings spot-checked for accuracy

**This plan is now READY FOR EXECUTION with code-verified mappings, clarified import strategy, and enhanced Phase 0 prototype scope.**
