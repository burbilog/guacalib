# Modular Architecture Plan for `GuacamoleDB`

## Overview

The current `guacalib/db.py` file has grown into a monolithic module that mixes configuration loading, connection lifecycle management, entity CRUD, permission handling, and debugging utilities. This plan proposes a modular architecture that:

- Separates concerns into dedicated repositories/services per domain (`users`, `usergroups`, `connections`, `conngroups`, `permissions`, `config`).
- Provides a thin, well-defined façade for CLI and library consumers.
- Improves testability by isolating SQL queries and business logic.
- Preserves backward compatibility through a staged migration layer.
- Prepares for future enhancements such as async support, alternative storage engines, and richer validation.

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
│   ├── base.py              # DatabaseSession / Unit-of-Work abstraction + helpers
│   ├── config_loader.py     # Loads env/config files, returns ConnectionConfig
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── usergroup_repository.py
│   │   ├── connection_repository.py
│   │   ├── conngroup_repository.py
│   │   └── permission_repository.py
│   └── validators.py        # Shared validation helpers, e.g., positive ID checks
├── services/
│   ├── user_service.py
│   ├── usergroup_service.py
│   ├── connection_service.py
│   ├── conngroup_service.py
│   └── permission_service.py
├── facade/
│   └── guac_db.py           # Thin façade exposing current public API
├── security.py              # Credential scrubbing and security utilities
├── types.py                 # Shared type aliases / Protocols
├── errors.py                # Shared exception hierarchy
└── __init__.py              # Exports façade + new interfaces as needed
```

### Component Responsibilities

- **Config Loader (`config_loader.py`)**
  - Handles reading environment variables / `.ini` files with validation.
  - Returns sanitized `ConnectionConfig`.
  - Emits configuration-related logging and user-facing error guidance.

- **Base (`base.py`)**
  - Defines `DatabaseSession` interface / wrapper around `mysql.connector` connection & cursor.
  - Manages connection lifecycle (connect, commit, rollback, close) and provides context manager helpers.
  - Ensures services receive a session that can span multiple repository calls in an operation.

- **Repositories (`repositories/`)**
  - Contain raw SQL queries for their domain.
  - Operate on simple data structures (dicts/tuples) or typed dataclasses without business rules.
  - Expose explicit CRUD/query methods plus ID resolution helpers (`resolve_*_id`).
  - Raise typed data-access errors (wrapping `mysql.connector.Error`) or return `None` where appropriate.

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
- Transactions:
  - Services own commit/rollback calls; repositories are transaction-agnostic and never commit.
  - Multi-repository operations (e.g., `delete_existing_user`) execute within a single session to preserve ACID properties.
- Implementation details:
  - `DatabaseSession` holds a `mysql.connector.connection_cext.CMySQLConnection` plus a dedicated cursor created on entry.
  - `.begin()` returns a context manager that ensures `conn.start_transaction()` is called and `.commit()`/`.rollback()` are invoked when the context exits.
  - `.cursor` returns the active cursor; nested cursors are not supported—callers should fetch all results before issuing additional queries.
  - Concurrency expectations: the façade provides one session per CLI invocation; sessions are not thread-safe and must not be shared across threads.
  - On session close, the cursor is closed first, followed by the connection; errors during close are logged but do not mask the original exception.

### Repository Interfaces & Data Contracts

- Define Protocols/ABCs in `types.py` describing required repository methods (CRUD, list, resolve ID).
- Repositories return typed dictionaries or lightweight dataclasses (documented per method).
- Error handling:
  - Wrap `mysql.connector.Error` into `DataAccessError` (defined in `errors.py`).
  - Validation failures (e.g., missing entity) return `None` or raise specialized exceptions (e.g., `EntityNotFoundError`).
- ID resolution helpers (current `resolve_*` methods) migrate into repositories (e.g., `ConnectionRepository.resolve_id`).

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

- Repository logging:
  - Emit debug-level statements for SQL execution, parameters (scrubbed), and row counts when debug mode is active.
- Service logging:
  - Log high-level operations, validation outcomes, and translated errors.
- Façade logging:
  - Maintains existing loggers and ensures CLI expectations (stdout vs stderr) remain intact.
  - Continues to bridge `debug_print` to logging when debugging is enabled.

### Error Handling Strategy

- Place the shared exception hierarchy in `guacalib/errors.py`.
- Introduce `GuacError` (base), `DomainValidationError`, `EntityNotFoundError`, `EntityConflictError`, `DataAccessError`, and `ConfigurationError`.
- Repositories raise `DataAccessError`; services translate into domain exceptions; façade converts to current `ValueError`/user-facing messages to keep CLI behaviour stable.
- Document how exceptions propagate to ensure existing tests remain valid.

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
- Shared type aliases and Protocols move to `types.py` (e.g., `ConnectionConfig`, `UserRecord`, repository/service interfaces).
- Parameter dictionaries (`CONNECTION_PARAMETERS`, `USER_PARAMETERS`) remain in their dedicated modules and are imported where needed.

## Testing Strategy

- **Frameworks**:
  - Continue running the existing bats integration suite (`tests/*.bats`) as the primary regression safety net.
  - Introduce `pytest` for new unit and service-level tests. Add a minimal `pytest.ini` if necessary to configure discovery paths.
  - Use `pytest-mock` (already available via standard pytest plugins) for repository/service mocking; avoid adding new dependencies beyond pytest unless absolutely required.
- **Test automation workflow**:
  - Update the Makefile (or add a new target) so `make tests` runs both pytest (`pytest`) and the existing bats suite (`bats -t ...`).
  - Document in `README.md` (after refactor) that contributors should run `pytest` for fast unit-level feedback and `make tests` for full coverage.
- **Coverage expectations**:
  - Repositories: pytest unit tests exercising SQL generation with a transactional test database (or using controlled fixtures/mocks for cursor interactions).
  - Services: pytest tests using mock repositories to verify business rules and transaction management.
  - Façade: rely primarily on bats integration tests and selective pytest smoke tests for bridging logic.

## Public API Strategy

1. **Short Term:** Keep exporting `GuacamoleDB` from `guacalib.__init__`. Internally, `GuacamoleDB` becomes a façade constructed from modular components.
2. **Medium Term:** Introduce optional new APIs (e.g., `guacalib.services.UserService`) for advanced integrations. Document usage in README.
3. **Long Term (Optional):** Deprecate façade layer once consumers adopt new services. This is optional and depends on adoption feedback.

## Error Handling & Logging

- Repositories raise `DataAccessError` (wrapping `mysql.connector.Error`) and avoid altering transactions directly.
- Services translate low-level errors into domain exceptions and ensure credential scrubbing before logging.
- Façade converts domain errors into the current CLI-facing messages to maintain backwards compatibility.
- Logging responsibilities follow the strategy outlined in “Design Clarifications”.

## Migration Considerations

- CLI handlers continue to inject a `GuacamoleDB` instance, unchanged.
- Tests referencing `GuacamoleDB` remain valid; new unit tests can target individual services and repositories.
- Internal methods currently calling `self.cursor` adapt to repository usage.
- Gradual migration: move one domain at a time while others remain in the monolith until refactoring is complete.
- Preserve `debug_print` behaviour via façade delegating to logger + scrubbing helper during transition.

## Phased Implementation Plan

- [ ] **Phase 1 — Infrastructure Setup**
  - Create `data_access` package with `base.py` defining `DatabaseSession` abstraction and transaction helpers.
  - Implement `config_loader.py`, `types.py`, `security.py`, and shared validation utilities.
  - Add minimal exception hierarchy in `errors.py` and update plan documentation/comments.
  - Ensure logging utilities can consume credential scrubbing helper.
  - Update imports in `guacalib/__init__.py` to reference new façade location once ready (no behaviour changes yet).

- [ ] **Phase 2 — Repository Layer Extraction**
  - For each domain (users, usergroups, connections, conngroups, permissions), move raw SQL and simple helpers into repositories.
  - Implement repository Protocols and concrete classes that accept `DatabaseSession`.
  - Migrate resolver methods (`resolve_*`) and document return types or exceptions.
  - Ensure repositories never commit/rollback; rely on session provided.

- [ ] **Phase 3 — Service Layer Formation**
  - Build services wrapping repositories, implementing business rules, validation, and multi-repository coordination.
  - Enforce transaction boundaries (commit/rollback) within services.
  - Wire logging (service-level), credential scrubbing, and error translation into the new services.
  - Maintain backwards-compatible outputs/messages.

- [ ] **Phase 4 — Façade Refactoring**
  - Rewrite `GuacamoleDB` as a façade that composes services via constructor injection.
  - Ensure façade tracks debug flag, bridges `debug_print`, and preserves CLI-facing behaviour.
  - Introduce wiring/builder to assemble repositories, services, and sessions for CLI/library clients.
  - Keep compatibility tests green; update CLI if necessary for dependency injection improvements.

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

## Success Criteria

- `GuacamoleDB` façade remains functionally equivalent for CLI and existing consumers.
- Each domain’s logic resides in its own repository/service with dedicated tests and documented interfaces.
- Overall cyclomatic complexity of `guacalib/db.py` drops dramatically; file becomes thin façade.
- Transaction management and credential scrubbing are centralized and well-documented.
- Documentation reflects modular architecture, testing strategy, and guides future maintenance.
