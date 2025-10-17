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
│   ├── base.py              # Low-level DB session + helper interfaces
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
└── __init__.py              # Exports façade + new interfaces as needed
```

### Component Responsibilities

- **Config Loader (`config_loader.py`)**
  - Handles reading environment variables / `.ini` files with validation.
  - Returns sanitized `ConnectionConfig`.
  - Emits configuration-related logging and user-facing error guidance.

- **Base (`base.py`)**
  - Defines `DatabaseSession` interface / wrapper around `mysql.connector` connection & cursor.
  - Manages connection lifecycle (connect, commit, rollback, close).
  - Provides context management utilities for services.

- **Repositories (`repositories/`)**
  - Contain raw SQL queries for their domain.
  - Operate on simple data structures (dicts/tuples) without business rules.
  - Offer CRUD + listing methods returning normalized entities.

- **Services (`services/`)**
  - Consume repositories to implement business rules, validation, and cross-entity operations.
  - Handle errors, raise domain-specific exceptions, call logging, and scrub credentials.

- **Façade (`facade/guac_db.py`)**
  - Implements the existing `GuacamoleDB` API by delegating to services.
  - Manages initialization (config, session factory).
  - Serves as compatibility layer while downstream consumers migrate.

## Public API Strategy

1. **Short Term:** Keep exporting `GuacamoleDB` from `guacalib.__init__`. Internally, `GuacamoleDB` becomes a façade constructed from modular components.
2. **Medium Term:** Introduce optional new APIs (e.g., `guacalib.services.UserService`) for advanced integrations. Document usage in README.
3. **Long Term (Optional):** Deprecate façade layer once consumers adopt new services. This is optional and depends on adoption feedback.

## Error Handling & Logging

- Repositories raise data access exceptions (wrapping `mysql.connector.Error`).
- Services translate low-level errors into meaningful domain errors, preserving user-facing messages expected by CLI.
- Logging remains at service level using existing `get_logger`.
- Credential scrubbing moved to shared helper to ensure consistency across modules.

## Migration Considerations

- CLI handlers continue to inject a `GuacamoleDB` instance, unchanged.
- Tests referencing `GuacamoleDB` remain valid; new unit tests can target individual services and repositories.
- Internal methods currently calling `self.cursor` adapt to repository usage.
- Gradual migration: move one domain at a time while others remain in the monolith until refactoring is complete.

## Phased Implementation Plan

- [ ] **Phase 1 — Infrastructure Setup**
  - Create `data_access` package with `base.py` (session abstraction) and `config_loader.py`.
  - Implement shared validation helpers (`validators.py`) and ensure logging utilities are accessible.
  - Update imports in `guacalib/__init__.py` to reference new façade location once ready (no behavior changes yet).

- [ ] **Phase 2 — Repository Layer Extraction**
  - For each domain (users, usergroups, connections, conngroups, permissions), move raw SQL and simple helpers into repositories.
  - Maintain method signatures but relocate logic; ensure unit tests cover repository methods.

- [ ] **Phase 3 — Service Layer Formation**
  - Build services that wrap repositories and implement business rules (validation, composite operations, transaction coordination).
  - Wire logging, credential scrubbing, and error translation within services.

- [ ] **Phase 4 — Façade Refactoring**
  - Rewrite `GuacamoleDB` as a façade that composes services.
  - Ensure all public methods simply delegate to service counterparts.
  - Keep compatibility tests green; update CLI if necessary for dependency injection improvements.

- [ ] **Phase 5 — Testing & Documentation**
  - Create targeted unit tests for repositories and services.
  - Run full integration tests (`make tests` / `bats` suites).
  - Update documentation (README, CHANGELOG) detailing new architecture and future migration guidance.
  - Optionally publish migration tips for downstream users wanting to adopt services directly.

- [ ] **Phase 6 — Optional Enhancements**
  - Evaluate introducing dependency injection for session factories (e.g., to support async/backends).
  - Consider deprecating direct façade usage if consumers adopt modular services.
  - Explore caching, query optimization, and connection pooling improvements using the new structure.

## Success Criteria

- `GuacamoleDB` façade remains functionally equivalent for CLI and existing consumers.
- Each domain’s logic resides in its own repository/service with dedicated tests.
- Overall cyclomatic complexity of `guacalib/db.py` drops dramatically; file becomes thin façade.
- Future contributors can modify domain logic without touching unrelated code.
- Documentation reflects modular architecture and guides future maintenance.
