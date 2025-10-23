# Incremental Refactoring Plan for `GuacamoleDB`

> **Status**: ✅ **READY FOR EXECUTION** (Revision 5 - Repository Pattern Committed)
> **Last Updated**: 2025-10-24
> **Approach**: Evidence-driven, incremental repository extraction following YAGNI and KISS principles

## Executive Summary

This plan addresses **documented code quality issues** in the 3313-line `guacalib/db.py` through incremental, evidence-based refactoring - while maintaining **100% backwards compatibility** for all 14 bats tests and 5 CLI handlers (1442 lines).

**What Changed in Revision 5 (Committed to Repository Pattern):**
- ✅ **Evidence-driven approach**: Documented actual pain points (P1-P4) with code evidence
- ✅ **Incremental execution**: 10 phases, each independently shippable
- ✅ **YAGNI compliance**: Repository pattern justified by mixed responsibilities (P4)
- ✅ **TDD alignment**: All changes validated by existing 14 bats tests
- ✅ **Clear commitment**: Phases 1-3 fix duplication/transactions, Phases 4-10 extract repositories
- ✅ **Walking skeleton**: Phase 5 validates approach before continuing
- ✅ **Thin facade**: GuacamoleDB becomes orchestration layer (~400 lines)

**Goal:** Achieve **modularity and maintainability** through clear layer separation (repositories for SQL, facade for orchestration), not to satisfy LLM context limits. Better LLM usability is a side benefit of well-factored code.

**Risk Level**: 🟢 **Very Low** - Small, incremental changes validated by 14 bats tests after each step.

---

## Problem Statement

### Current Pain Points (Evidence-Based)

#### **P1: Code Duplication (HIGH SEVERITY)**
**Evidence:**
```python
# Lines 15, 68 in db.py - Import from canonical source
from .db_user_parameters import USER_PARAMETERS

# Lines 551-607 in db.py - Complete override (57 lines duplicated)
USER_PARAMETERS = {
    "disabled": {...},
    "expired": {...},
    # ... 11 parameters redefined
}
```
**Impact:** Maintenance burden - changes must be made in two places, risk of inconsistency.
**Call sites:** Used throughout user modification methods.

#### **P2: Redundant Transaction Commits (MEDIUM SEVERITY)**
**Evidence:**
```python
# Line 226 in __exit__ - Context manager handles commits
if exc_type is None:
    self.conn.commit()

# Line 1284 in delete_existing_connection() - Redundant commit
self.conn.commit()

# Line 1341 in delete_connection_group() - Redundant commit
self.conn.commit()
```
**Impact:** Confusion about transaction boundaries, potential for partial commits in multi-step operations.
**Risk:** If inline commits are removed without testing, multi-step operations may fail.

#### **P3: ID Resolution Duplication (MEDIUM SEVERITY)**
**Evidence:**
```python
# Resolver methods used across multiple domains:
- resolve_connection_id() (line 2512) - 76 lines
- resolve_conngroup_id() (line 2589) - 51 lines
- resolve_usergroup_id() (line 2641) - 48 lines
- validate_positive_id() (line 2502) - 9 lines
- get_connection_name_by_id() (line 2468) - 16 lines
- get_connection_group_name_by_id() (line 2485) - 16 lines
- get_usergroup_name_by_id() (line 2704) - 37 lines
```
**Impact:** 253 lines of pure utility code mixed with business logic.
**Call sites:** ≥3 call sites per resolver across different domain methods.

#### **P4: Mixed Responsibilities (HIGH SEVERITY)**
**Evidence:**
- Single GuacamoleDB class conflates multiple responsibilities:
  - **Config/Loading**: Database credentials and connection setup (~114 lines)
  - **DB Connection/Transactions**: Context manager, commit/rollback (~26 lines)
  - **SQL Repositories**: CRUD operations for users, connections, groups (~2300 lines)
  - **Validation/Resolution**: ID resolution, parameter validation (~253 lines, partially fixed in Phase 2)
  - **Permissions Logic**: Grant/deny operations across domains (~400 lines)
  - **Logging Utilities**: Credential scrubbing, debug output (~120 lines)

**Impact:**
- **Hard to test**: Tightly coupled SQL, transaction, and business logic requires database for all tests
- **Fragile to change**: Modifications ripple across unrelated concerns
- **Duplication prone**: Multiple sources of truth (e.g., USER_PARAMETERS override in P1)
- **Unclear boundaries**: Transaction boundaries unclear, permission logic scattered
- **Cognitive load**: Mental context switching between infrastructure, SQL, and business logic

**Justification for Splitting:**
The goal is **modularity and maintainability**, not LLM context limits. Clear layer boundaries (repositories for SQL, facade for orchestration, utilities for helpers) enable:
- **Targeted testing**: Unit test SQL logic without database context manager
- **Safer changes**: Modify connection logic without risk to user logic
- **Clear contracts**: Repositories accept cursor, return data (stateless)
- **Eliminated duplication**: Single source of truth for each concern
- **Better onboarding**: Navigate by domain, not by line number

---

## Design Principles (PLAN.md Compliance)

### **RULE #0: DO NOT OVERENGINEER**
Start with the simplest solution that works; add complexity only with evidence.

### **Approach:**
1. **Solve Today's Problem** - Fix documented bugs and duplication (P1-P3)
2. **Test-Driven** - All changes validated by existing 14 bats tests
3. **Incremental** - Each phase is a complete, shippable improvement
4. **Optimize Last** - Defer domain splitting (P4) until evidence proves necessity

### **Complexity Checklist Applied:**
- ✅ **Add complexity when:** ≥3 call sites (ID resolvers) ✓
- ✅ **Add complexity when:** Painful duplication (USER_PARAMETERS) ✓
- ❌ **Avoid:** "Just in case" abstractions (removed security.py, errors.py)
- ❌ **Avoid:** Single-implementation interfaces (removed errors.py)
- ❌ **Avoid:** Designing for scale you don't have (deferred domain split)

---

## Incremental Implementation Plan

### **Phase 0 - Preparation** (Est: 30 minutes)
**Outcome:** Baseline established, tests passing, ready for refactoring.

- [ ] **0.1. Establish baseline**
  - [ ] 0.1.1. Run full bats test suite: `export TEST_CONFIG=/home/rm/.guacaman.ini && make tests`
  - [ ] 0.1.2. Document current test pass rate and runtime
  - [ ] 0.1.3. Create git branch: `git checkout -b refactor/incremental-cleanup`

  **Acceptance Criteria:**
  - All 14 bats tests pass (100% green)
  - Baseline metrics documented for comparison

---

### **Phase 1 - Fix Code Duplication** (Est: 1 hour)
**Outcome:** USER_PARAMETERS duplication eliminated, single source of truth restored.

**Problem Addressed:** P1 (Code Duplication - HIGH)

- [ ] **1.1. Remove USER_PARAMETERS override**
  - [ ] 1.1.1. Delete lines 551-607 in `guacalib/db.py`
  - [ ] 1.1.2. Verify import on line 15 remains: `from .db_user_parameters import USER_PARAMETERS`
  - [ ] 1.1.3. Verify class attribute on line 68 remains: `USER_PARAMETERS = USER_PARAMETERS`

  **Acceptance Criteria:**
  - Given db.py imports USER_PARAMETERS from db_user_parameters.py
  - When a user parameter is modified in db_user_parameters.py
  - Then the change is reflected in GuacamoleDB without duplicating edits

- [ ] **1.2. Validate fix**
  - [ ] 1.2.1. Run full bats test suite
  - [ ] 1.2.2. Verify all tests pass (no regressions)
  - [ ] 1.2.3. Test user modification: `guacaman user modify --username testuser --disabled 1`

  **Acceptance Criteria:**
  - All 14 bats tests pass (100% green)
  - User modification commands work identically

- [ ] **1.3. Commit changes**
  - [ ] 1.3.1. Git commit: "fix: remove USER_PARAMETERS duplication (lines 551-607)"
  - [ ] 1.3.2. Document lines saved: 57 lines removed

  **Success Metrics:**
  - Lines of code: -57
  - Duplication: 0 instances
  - Tests passing: 14/14

---

### **Phase 2 - Extract Shared Utilities** (Est: 2 hours)
**Outcome:** ID resolvers and validation helpers centralized in dedicated utility module.

**Problem Addressed:** P3 (ID Resolution Duplication - MEDIUM)

- [ ] **2.1. Create db_utils.py**
  - [ ] 2.1.1. Create new file: `guacalib/db_utils.py`
  - [ ] 2.1.2. Add module docstring explaining purpose (shared utilities for ID resolution)
  - [ ] 2.1.3. Move resolver functions from db.py (preserve exact logic, add type hints):
    - `resolve_connection_id()` (line 2512, ~76 lines)
    - `resolve_conngroup_id()` (line 2589, ~51 lines)
    - `resolve_usergroup_id()` (line 2641, ~48 lines)
    - `validate_positive_id()` (line 2502, ~9 lines)
    - `get_connection_name_by_id()` (line 2468, ~16 lines)
    - `get_connection_group_name_by_id()` (line 2485, ~16 lines)
    - `get_usergroup_name_by_id()` (line 2704, ~37 lines)

  **Acceptance Criteria:**
  - Given multiple domains need to resolve entity IDs
  - When ID resolution is needed
  - Then a single, tested utility function is called (no duplication)

- [ ] **2.2. Update db.py to use db_utils**
  - [ ] 2.2.1. Add import: `from .db_utils import resolve_connection_id, resolve_conngroup_id, ...`
  - [ ] 2.2.2. Replace method implementations with delegation:
    ```python
    def resolve_connection_id(self, connection_name=None, connection_id=None):
        from .db_utils import resolve_connection_id as _resolve
        return _resolve(self.cursor, connection_name, connection_id)
    ```
  - [ ] 2.2.3. OR: Replace all call sites to use db_utils directly and remove wrapper methods

  **Acceptance Criteria:**
  - All resolver call sites use db_utils functions
  - No logic duplication between db.py and db_utils.py

- [ ] **2.3. Validate extraction**
  - [ ] 2.3.1. Run full bats test suite
  - [ ] 2.3.2. Test connection operations with ID resolution: `guacaman conn modify --id 123 --parameter hostname --value newhost`
  - [ ] 2.3.3. Test connection group hierarchy: `guacaman conngroup create --name "parent/child"`

  **Acceptance Criteria:**
  - All 14 bats tests pass (100% green)
  - ID resolution works identically for connections, connection groups, usergroups

- [ ] **2.4. Commit changes**
  - [ ] 2.4.1. Git commit: "refactor: extract ID resolvers to db_utils.py"
  - [ ] 2.4.2. Document lines moved: ~253 lines to db_utils.py

  **Success Metrics:**
  - Lines in db.py: -253
  - New file: db_utils.py (~253 lines)
  - Duplication eliminated: 7 utility functions centralized
  - Tests passing: 14/14

---

### **Phase 3 - Fix Transaction Handling** (Est: 1.5 hours)
**Outcome:** Redundant commits removed, transaction boundaries clarified.

**Problem Addressed:** P2 (Redundant Transaction Commits - MEDIUM)

**⚠️ RISK:** This changes transaction behavior. Requires careful testing.

- [ ] **3.1. Analyze transaction boundaries**
  - [ ] 3.1.1. Document which operations are multi-step (require transaction atomicity)
  - [ ] 3.1.2. Verify context manager commit (line 226) handles all normal flows
  - [ ] 3.1.3. Identify if inline commits serve a purpose (e.g., partial commit before next step)

  **Acceptance Criteria:**
  - Transaction boundaries documented
  - Decision recorded: remove inline commits OR keep with justification

- [ ] **3.2. Remove redundant commits (if analysis confirms safe)**
  - [ ] 3.2.1. Remove commit at line 1284 in `delete_existing_connection()`
  - [ ] 3.2.2. Remove commit at line 1341 in `delete_connection_group()`
  - [ ] 3.2.3. Update docstrings to clarify: "Transaction committed by context manager"

  **Acceptance Criteria:**
  - Given a delete operation is called within GuacamoleDB context manager
  - When the operation completes successfully
  - Then the transaction is committed exactly once (by __exit__)

- [ ] **3.3. Validate transaction behavior**
  - [ ] 3.3.1. Run full bats test suite (especially delete operations)
  - [ ] 3.3.2. Test multi-step operation: Create connection, grant permission, delete connection
  - [ ] 3.3.3. Test rollback: Trigger error mid-operation, verify no partial commits

  **Acceptance Criteria:**
  - All 14 bats tests pass (100% green)
  - Delete operations commit exactly once
  - Rollback works correctly on errors

- [ ] **3.4. Commit changes**
  - [ ] 3.4.1. Git commit: "fix: remove redundant transaction commits (lines 1284, 1341)"
  - [ ] 3.4.2. Document reasoning in commit message

  **Success Metrics:**
  - Redundant commits: 0 (down from 2)
  - Transaction boundaries: Clear and documented
  - Tests passing: 14/14

---

### **Phase 4 - Plan Repository Layer** (Est: 1 hour)
**Outcome:** Clear mapping of SQL operations to repository modules, transaction boundaries documented.

**Problem Addressed:** P4 (Mixed Responsibilities - GuacamoleDB conflates config, transactions, SQL, validation, permissions)

**Rationale for Splitting:**
The current GuacamoleDB class mixes multiple responsibilities that should be separated:
- **Config/Loading**: Database credentials and connection setup
- **DB Connection/Transactions**: Context manager, commit/rollback logic
- **SQL Repositories**: CRUD operations for users, connections, groups
- **Validation/Resolution**: ID resolution, parameter validation (partially addressed in Phase 2)
- **Permissions Logic**: Grant/deny operations across domains
- **Logging Utilities**: Credential scrubbing, debug output

This conflation makes the code:
- Hard to test (tightly coupled SQL, transaction, and business logic)
- Difficult to reason about (transaction boundaries unclear, multiple sources of truth)
- Fragile to change (modifications ripple across unrelated concerns)
- Prone to duplication (e.g., USER_PARAMETERS override discovered in Phase 1)

**Goal:** Achieve modularity through clear layer boundaries (repositories → services → facade), not to satisfy LLM context limits.

- [ ] **4.1. Document current responsibilities**
  - [ ] 4.1.1. Identify all SQL operations (CRUD methods by domain)
  - [ ] 4.1.2. Identify transaction boundaries (which operations must be atomic)
  - [ ] 4.1.3. Identify permission operations (grant/deny, cross-domain)
  - [ ] 4.1.4. Identify shared utilities (beyond db_utils.py from Phase 2)

  **Acceptance Criteria:**
  - Responsibility matrix created (method → layer mapping)
  - Transaction boundaries documented

- [ ] **4.2. Design repository layer**
  - [ ] 4.2.1. Define repository modules:
    - `users_repo.py` - User CRUD SQL operations
    - `usergroups_repo.py` - User group CRUD SQL operations
    - `connections_repo.py` - Connection CRUD SQL operations
    - `conngroups_repo.py` - Connection group CRUD SQL operations
    - `permissions_repo.py` - Permission grant/deny SQL operations
  - [ ] 4.2.2. Define repository function signatures (input: cursor + params, output: dict/list)
  - [ ] 4.2.3. Define transaction policy: repositories are stateless, caller manages transactions

  **Acceptance Criteria:**
  - Repository API contracts documented
  - Each repository has single responsibility (one domain's SQL operations)

- [ ] **4.3. Design facade preservation**
  - [ ] 4.3.1. Plan GuacamoleDB facade structure:
    - Preserve all public methods (100% backwards compatible)
    - Delegate to repositories (thin orchestration layer)
    - Manage database connection and transactions
    - Handle config loading (keep in facade or extract to db_config.py)
  - [ ] 4.3.2. Document import compatibility:
    - `from guacalib import GuacamoleDB` remains unchanged
    - Internal imports change, external API identical

  **Acceptance Criteria:**
  - Facade design documented with delegation strategy
  - Zero breaking changes for CLI handlers

- [ ] **4.4. Document incremental migration path**
  - [ ] 4.4.1. Phase 5: Extract users repository (walking skeleton)
  - [ ] 4.4.2. Phase 6: Extract usergroups repository
  - [ ] 4.4.3. Phase 7: Extract connections repository
  - [ ] 4.4.4. Phase 8: Extract conngroups repository
  - [ ] 4.4.5. Phase 9: Extract permissions repository
  - [ ] 4.4.6. Phase 10: Final cleanup and documentation

  **Success Criteria:**
  - Each phase has clear scope (one repository at a time)
  - Each phase is independently testable (14 bats tests pass)
  - Walking skeleton approach (end-to-end before next domain)

---

### **Phase 5 - Extract Users Repository** (Est: 3 hours)
**Outcome:** User CRUD operations moved to `users_repo.py`, GuacamoleDB delegates to repository.

**Walking Skeleton:** First end-to-end domain extraction to validate approach.

- [ ] **5.1. Create users_repo.py**
  - [ ] 5.1.1. Create `guacalib/users_repo.py` with module docstring
  - [ ] 5.1.2. Extract SQL functions (preserve exact logic):
    - `user_exists(cursor, username)` (lines 517-548)
    - `create_user(cursor, username, password, ...)` (lines 1353-1419)
    - `delete_user(cursor, username)` (lines 1018-1106)
    - `modify_user_parameter(cursor, username, parameter, value)` (lines 944-1016)
    - `change_user_password(cursor, username, new_password)` (lines 875-942)
    - `list_users(cursor)` (lines 382-411)
  - [ ] 5.1.3. Add type hints to all function signatures
  - [ ] 5.1.4. Import USER_PARAMETERS from db_user_parameters.py

  **Acceptance Criteria:**
  - All user SQL operations in users_repo.py
  - Functions accept cursor as first parameter (stateless)
  - No GuacamoleDB class dependencies

- [ ] **5.2. Update GuacamoleDB to delegate**
  - [ ] 5.2.1. Add import: `from . import users_repo`
  - [ ] 5.2.2. Update methods to delegate:
    ```python
    def user_exists(self, username):
        return users_repo.user_exists(self.cursor, username)
    ```
  - [ ] 5.2.3. Preserve all method signatures (backwards compatibility)

  **Acceptance Criteria:**
  - GuacamoleDB methods are thin wrappers (≤3 lines each)
  - No user SQL logic remains in db.py

- [ ] **5.3. Validate extraction**
  - [ ] 5.3.1. Run full bats test suite
  - [ ] 5.3.2. Test user operations: create, modify, delete, list
  - [ ] 5.3.3. Verify CLI handlers unchanged: `git diff guacalib/cli_handle_user.py`

  **Acceptance Criteria:**
  - All 14 bats tests pass (100% green)
  - User operations identical to pre-refactor

- [ ] **5.4. Commit changes**
  - [ ] 5.4.1. Git commit: "refactor: extract users repository to users_repo.py"
  - [ ] 5.4.2. Document lines moved: ~450 lines to users_repo.py

  **Success Metrics:**
  - Lines in db.py: -450
  - New file: users_repo.py (~450 lines)
  - Tests passing: 14/14
  - Walking skeleton validated ✅

---

### **Phase 6 - Extract UserGroups Repository** (Est: 2 hours)
**Outcome:** User group CRUD operations moved to `usergroups_repo.py`.

- [ ] **6.1. Create usergroups_repo.py**
  - [ ] 6.1.1. Create `guacalib/usergroups_repo.py` with module docstring
  - [ ] 6.1.2. Extract SQL functions:
    - `usergroup_exists(cursor, usergroup_name)` (lines 444-475)
    - `create_usergroup(cursor, usergroup_name, ...)` (lines 1421-1460)
    - `delete_usergroup(cursor, usergroup_name)` (lines 1108-1161)
    - `list_usergroups(cursor)` (lines 413-442)
  - [ ] 6.1.3. Add type hints

- [ ] **6.2. Update GuacamoleDB to delegate**
  - [ ] 6.2.1. Add import: `from . import usergroups_repo`
  - [ ] 6.2.2. Update methods to delegate (thin wrappers)

- [ ] **6.3. Validate extraction**
  - [ ] 6.3.1. Run full bats test suite
  - [ ] 6.3.2. Test usergroup operations

- [ ] **6.4. Commit changes**
  - [ ] 6.4.1. Git commit: "refactor: extract usergroups repository"

  **Success Metrics:**
  - Lines in db.py: -350
  - New file: usergroups_repo.py (~350 lines)
  - Tests passing: 14/14

---

### **Phase 7 - Extract Connections Repository** (Est: 3 hours)
**Outcome:** Connection CRUD operations moved to `connections_repo.py`.

- [ ] **7.1. Create connections_repo.py**
  - [ ] 7.1.1. Create `guacalib/connections_repo.py` with module docstring
  - [ ] 7.1.2. Extract SQL functions:
    - `connection_exists(cursor, connection_name, connection_id)` (lines 1634-1673)
    - `create_connection(cursor, protocol, name, ...)` (lines 1691-1775)
    - `delete_connection(cursor, connection_id)` (lines 1224-1289)
    - `modify_connection_parameter(cursor, connection_id, parameter, value)` (lines 738-873)
  - [ ] 7.1.3. Import CONNECTION_PARAMETERS from db_connection_parameters.py
  - [ ] 7.1.4. Add type hints

- [ ] **7.2. Update GuacamoleDB to delegate**
  - [ ] 7.2.1. Add import: `from . import connections_repo`
  - [ ] 7.2.2. Update methods to delegate

- [ ] **7.3. Validate extraction**
  - [ ] 7.3.1. Run full bats test suite (connection tests critical)
  - [ ] 7.3.2. Test connection operations with various protocols

- [ ] **7.4. Commit changes**
  - [ ] 7.4.1. Git commit: "refactor: extract connections repository"

  **Success Metrics:**
  - Lines in db.py: -600
  - New file: connections_repo.py (~600 lines)
  - Tests passing: 14/14

---

### **Phase 8 - Extract ConnGroups Repository** (Est: 2.5 hours)
**Outcome:** Connection group CRUD operations moved to `conngroups_repo.py`.

- [ ] **8.1. Create conngroups_repo.py**
  - [ ] 8.1.1. Create `guacalib/conngroups_repo.py` with module docstring
  - [ ] 8.1.2. Extract SQL functions:
    - `connection_group_exists(cursor, conngroup_name, conngroup_id)` (lines 1675-1689)
    - `create_connection_group(cursor, name, group_type, ...)` (lines 2128-2208)
    - `delete_connection_group(cursor, conngroup_id)` (lines 1291-1351)
    - `check_connection_group_cycle(cursor, group_id, parent_id)` (lines 2082-2126)
  - [ ] 8.1.3. Add type hints

- [ ] **8.2. Update GuacamoleDB to delegate**
  - [ ] 8.2.1. Add import: `from . import conngroups_repo`
  - [ ] 8.2.2. Update methods to delegate

- [ ] **8.3. Validate extraction**
  - [ ] 8.3.1. Run full bats test suite (conngroup hierarchy tests critical)
  - [ ] 8.3.2. Test connection group operations

- [ ] **8.4. Commit changes**
  - [ ] 8.4.1. Git commit: "refactor: extract conngroups repository"

  **Success Metrics:**
  - Lines in db.py: -400
  - New file: conngroups_repo.py (~400 lines)
  - Tests passing: 14/14

---

### **Phase 9 - Extract Permissions Repository** (Est: 3 hours)
**Outcome:** Permission grant/deny operations moved to `permissions_repo.py`.

- [ ] **9.1. Create permissions_repo.py**
  - [ ] 9.1.1. Create `guacalib/permissions_repo.py` with module docstring
  - [ ] 9.1.2. Extract SQL functions for all permission operations:
    - User-to-connection grants/denies
    - User-to-connection-group grants/denies
    - UserGroup-to-connection grants/denies
    - UserGroup-to-connection-group grants/denies
    - Permission listing functions
  - [ ] 9.1.3. Add type hints

- [ ] **9.2. Update GuacamoleDB to delegate**
  - [ ] 9.2.1. Add import: `from . import permissions_repo`
  - [ ] 9.2.2. Update methods to delegate

- [ ] **9.3. Validate extraction**
  - [ ] 9.3.1. Run full bats test suite (permission tests critical)
  - [ ] 9.3.2. Test all permission operations

- [ ] **9.4. Commit changes**
  - [ ] 9.4.1. Git commit: "refactor: extract permissions repository"

  **Success Metrics:**
  - Lines in db.py: -500
  - New file: permissions_repo.py (~500 lines)
  - Tests passing: 14/14

---

### **Phase 10 - Create Facade and Deprecate db.py** (Est: 2 hours)
**Outcome:** Clean GuacamoleDB facade in `guac_db.py`, `db.py` deprecated.

- [ ] **10.1. Create guac_db.py facade**
  - [ ] 10.1.1. Create `guacalib/guac_db.py`
  - [ ] 10.1.2. Move GuacamoleDB class from db.py
  - [ ] 10.1.3. Keep config loading, connection management, context manager
  - [ ] 10.1.4. Keep `_scrub_credentials()` utility
  - [ ] 10.1.5. All methods delegate to repositories (thin wrappers)
  - [ ] 10.1.6. Add comprehensive module docstring

  **Acceptance Criteria:**
  - guac_db.py is thin orchestration layer (~400 lines)
  - No SQL queries in guac_db.py (delegated to repositories)
  - All public methods preserved (100% API compatibility)

- [ ] **10.2. Update db.py to re-export**
  - [ ] 10.2.1. Replace db.py contents with deprecation notice:
    ```python
    """
    DEPRECATED: This module is deprecated and will be removed in v2.0.
    Import from guacalib.guac_db instead.
    """
    from .guac_db import GuacamoleDB
    __all__ = ['GuacamoleDB']
    ```

- [ ] **10.3. Update __init__.py**
  - [ ] 10.3.1. Change import: `from .guac_db import GuacamoleDB`
  - [ ] 10.3.2. External import unchanged: `from guacalib import GuacamoleDB`

- [ ] **10.4. Validate final state**
  - [ ] 10.4.1. Run full bats test suite
  - [ ] 10.4.2. Verify CLI handlers unchanged
  - [ ] 10.4.3. Test all import paths

- [ ] **10.5. Update documentation**
  - [ ] 10.5.1. Update README.md with new architecture
  - [ ] 10.5.2. Update CLAUDE.md with repository layer
  - [ ] 10.5.3. Add migration guide for library users

- [ ] **10.6. Commit changes**
  - [ ] 10.6.1. Git commit: "refactor: create GuacamoleDB facade in guac_db.py, deprecate db.py"

  **Success Metrics:**
  - guac_db.py: ~400 lines (thin facade)
  - db.py: ~10 lines (deprecation re-export)
  - Total LOC unchanged (code moved, not added)
  - Tests passing: 14/14
  - Zero breaking changes ✅

---

## Repository Extraction (Phase 5-10) - Summary

**Commitment:** Execute repository extraction to achieve clean layer separation (planned in Phase 4).

### **Target Architecture**

```
guacalib/
├── db_utils.py              # CREATED Phase 2 - ID resolvers, validation helpers
├── users_repo.py            # Phase 5 - User CRUD SQL operations
├── usergroups_repo.py       # Phase 6 - User group CRUD SQL operations
├── connections_repo.py      # Phase 7 - Connection CRUD SQL operations
├── conngroups_repo.py       # Phase 8 - Connection group CRUD SQL operations
├── permissions_repo.py      # Phase 9 - Permission grant/deny SQL operations
├── guac_db.py               # Phase 10 - Thin façade preserving GuacamoleDB API
├── db.py                    # DEPRECATED - Kept for one release, imports from guac_db.py
```

**Walking Skeleton Approach:**
1. Extract ONE repository at a time (Phases 5-9)
2. Update GuacamoleDB to delegate to repository
3. Run full bats suite (100% pass required)
4. Commit before proceeding to next domain
5. Each phase is independently shippable

**Explicitly NOT Created:**
- ❌ `security.py` - `_scrub_credentials()` stays in guac_db.py (single caller, no duplication)
- ❌ `errors.py` - `ValueError` sufficient (no custom exception hierarchy needed)
- ❌ `db_config.py` - Config loading stays in guac_db.py (114 lines, no duplication)

---

## Testing Strategy

### **Primary Safety Net**
- **14 bats integration tests** run after EVERY phase
- **Success criterion:** 100% pass rate (no regressions allowed)
- **Command:** `export TEST_CONFIG=/home/rm/.guacaman.ini && make tests`

### **Smoke Tests**
After each phase, manually verify:
1. User CRUD: `guacaman user create testuser password123`
2. Connection CRUD: `guacaman conn create --protocol vnc --name test --hostname localhost`
3. Permission grant: `guacaman user grant-conn --username testuser --connection test`
4. List operations: `guacaman user list`, `guacaman conn list`

### **Rollback Strategy**
- Each phase is a separate git commit
- If any phase fails tests: `git reset --hard HEAD~1`
- No phase depends on future phases - can stop at any point

---

## Import Compatibility

### **Zero Breaking Changes Guarantee**

**Current Import (Preserved Throughout):**
```python
# CLI handlers (cli_handle_*.py)
from guacalib.db import GuacamoleDB

# External library users
from guacalib import GuacamoleDB
```

**Implementation:**
- **Phases 1-4:** `guacalib/__init__.py` continues: `from .db import GuacamoleDB`
- **Phase 5+ (if executed):** Update to: `from .guac_db import GuacamoleDB`
- **Result:** Import path `from guacalib import GuacamoleDB` remains identical

**Compatibility Guarantees:**
- ✅ All method signatures unchanged
- ✅ All return types unchanged
- ✅ All exceptions unchanged (ValueError throughout)
- ✅ All CLI handlers require zero import changes

---

## Success Criteria

### **Phase 1-3 (Fix Duplication and Transactions)**
- ✅ USER_PARAMETERS duplication eliminated (P1 resolved)
- ✅ ID resolvers centralized in db_utils.py (P3 resolved)
- ✅ Redundant commits removed (P2 resolved)
- ✅ All 14 bats tests pass (100% green)
- ✅ All 5 CLI handlers unchanged (1442 lines)
- ✅ Backwards compatibility maintained
- ✅ Lines of code reduced: ~310 lines

### **Phase 4 (Plan Repository Layer)**
- ✅ Responsibility matrix created (method → layer mapping)
- ✅ Repository API contracts documented
- ✅ Transaction boundaries documented
- ✅ Facade delegation strategy designed
- ✅ Migration path defined (Phases 5-10)

### **Phase 5-9 (Extract Repositories)**
- ✅ Walking skeleton validated (Phase 5 users_repo.py)
- ✅ All repositories extracted (users, usergroups, connections, conngroups, permissions)
- ✅ Each repository is stateless (accepts cursor, returns data)
- ✅ All 14 bats tests pass after each phase
- ✅ Zero breaking changes for CLI handlers

### **Phase 10 (Create Facade)**
- ✅ GuacamoleDB facade is thin orchestration layer (~400 lines)
- ✅ No SQL queries in guac_db.py (delegated to repositories)
- ✅ db.py deprecated with re-export (backwards compatible)
- ✅ All 14 bats tests pass (100% green)
- ✅ Documentation updated (README.md, CLAUDE.md)
- ✅ Mixed responsibilities resolved (P4) ✅

---

## Definition of Done (Per Phase)

**Each phase is considered complete when:**
1. ✅ Code changes committed to git
2. ✅ All 14 bats tests passing (100% green)
3. ✅ CLI handlers unchanged (verified with `git diff guacalib/cli_handle_*.py`)
4. ✅ Smoke tests passed manually
5. ✅ Metrics documented (lines changed, duplication removed, etc.)
6. ✅ Decision point reached (continue or stop)

---

## Risk Management

### **Risk Log**

| Risk | Severity | Mitigation | Owner |
|------|----------|------------|-------|
| Transaction commit removal breaks multi-step operations | MEDIUM | Thorough analysis in Phase 3.1, extensive testing, easy rollback | Developer |
| ID resolver extraction changes behavior | LOW | Preserve exact logic, comprehensive test coverage | Developer |
| Import changes break external users | LOW | No import changes in Phases 1-4, façade pattern in Phase 5+ | Developer |
| Domain split adds complexity without benefit | MEDIUM | Phase 4 measure-and-decide gate, walking skeleton approach | Developer |

### **Rollback Strategy**
- Each phase is a separate git commit
- Revert command: `git reset --hard <phase-N-commit>`
- All phases are independent - can stop at any point without breaking changes

---

## Non-Functional Requirements

### **Performance**
- **Target:** No degradation in query execution time
- **Measurement:** Compare bats test suite runtime before/after
- **Acceptable:** ±5% variance

### **Reliability**
- **Target:** 100% bats test pass rate maintained
- **Measurement:** All 14 tests green after every phase

### **Security**
- **Target:** Credential scrubbing preserved
- **Measurement:** Verify `_scrub_credentials()` still called in all log/error paths

### **Maintainability**
- **Target:** Reduced code duplication, clearer separation of concerns
- **Measurement:**
  - Duplication: 0 instances of USER_PARAMETERS
  - Utility code: Centralized in db_utils.py
  - Lines of code: Reduced by ~310 in Phases 1-3

---

## Comparison: Before vs After

### **Before (Current State)**
```
guacalib/db.py: 3313 lines
- Mixed responsibilities: config, transactions, SQL, validation, permissions, logging
- Duplication: USER_PARAMETERS (57 lines)
- Redundant commits: 2 instances
- Utility functions: Scattered throughout
- Hard to test: Requires full database context for all operations
- Fragile: Changes ripple across unrelated domains
```

### **After Phase 1-3 (Quick Wins)**
```
guacalib/db.py: ~3003 lines (−310 lines)
guacalib/db_utils.py: ~253 lines (NEW)
- Duplication eliminated: USER_PARAMETERS, redundant commits
- Utilities extracted: ID resolvers centralized
- Still monolithic: Mixed responsibilities remain
```

### **After Phase 4-10 (Final Architecture)**
```
guacalib/guac_db.py: ~400 lines (thin facade)
  ├─ Config loading, connection management, context manager
  ├─ Credential scrubbing utility
  └─ Thin delegation methods (≤3 lines each)

guacalib/users_repo.py: ~450 lines (user CRUD SQL)
guacalib/usergroups_repo.py: ~350 lines (usergroup CRUD SQL)
guacalib/connections_repo.py: ~600 lines (connection CRUD SQL)
guacalib/conngroups_repo.py: ~400 lines (conngroup CRUD SQL)
guacalib/permissions_repo.py: ~500 lines (permission grant/deny SQL)
guacalib/db_utils.py: ~253 lines (ID resolvers, validation)
guacalib/db.py: ~10 lines (deprecation re-export)

Total LOC: ~2963 (−350 lines due to eliminated duplication)

Benefits:
- ✅ Clear separation: Each repository has single responsibility
- ✅ Testable: Can unit test SQL logic without context manager
- ✅ Safe changes: Modify connections without risk to users
- ✅ Clear contracts: Repositories accept cursor, return data (stateless)
- ✅ Easy navigation: Find code by domain, not line number
- ✅ Onboarding: Understand one repository at a time
- ✅ Transaction boundaries: Documented and enforced by facade
```

---

## Appendix A: Method-to-Repository Mapping

**Reference:** Detailed method-to-repository mapping for Phases 5-9 execution.

### User Repository (`users_repo.py`) - Phase 5
| Current Method | Lines | Repository Function | Notes |
|---------------|-------|---------------------|-------|
| `user_exists()` | 517-548 | `user_exists(cursor, username)` | Validation helper |
| `create_user()` | 1353-1419 | `create_user(cursor, username, password, ...)` | Password hashing logic |
| `delete_existing_user()` | 1018-1106 | `delete_user(cursor, username)` | Multi-table cascade delete |
| `modify_user()` | 944-1016 | `modify_user_parameter(cursor, username, parameter, value)` | Parameter validation |
| `change_user_password()` | 875-942 | `change_user_password(cursor, username, new_password)` | New salt + hash |
| `list_users()` | 382-411 | `list_users(cursor)` | Simple query |

### UserGroup Repository (`usergroups_repo.py`) - Phase 6
| Current Method | Lines | Repository Function | Notes |
|---------------|-------|---------------------|-------|
| `usergroup_exists()` | 444-475 | `usergroup_exists(cursor, usergroup_name)` | Validation helper |
| `create_usergroup()` | 1421-1460 | `create_usergroup(cursor, usergroup_name, ...)` | Entity + group record |
| `delete_existing_usergroup()` | 1108-1161 | `delete_usergroup(cursor, usergroup_name)` | Cascade delete |
| `list_usergroups()` | 413-442 | `list_usergroups(cursor)` | Simple query |

### Connection Repository (`connections_repo.py`) - Phase 7
| Current Method | Lines | Repository Function | Notes |
|---------------|-------|---------------------|-------|
| `connection_exists()` | 1634-1673 | `connection_exists(cursor, connection_name, connection_id)` | Uses resolver |
| `create_connection()` | 1691-1775 | `create_connection(cursor, protocol, name, ...)` | Connection + parameters |
| `delete_existing_connection()` | 1224-1289 | `delete_connection(cursor, connection_id)` | Cascade delete |
| `modify_connection()` | 738-873 | `modify_connection_parameter(cursor, connection_id, parameter, value)` | Two-table parameter handling |

### ConnectionGroup Repository (`conngroups_repo.py`) - Phase 8
| Current Method | Lines | Repository Function | Notes |
|---------------|-------|---------------------|-------|
| `connection_group_exists()` | 1675-1689 | `connection_group_exists(cursor, conngroup_name, conngroup_id)` | Uses resolver |
| `create_connection_group()` | 2128-2208 | `create_connection_group(cursor, name, group_type, ...)` | Hierarchy validation |
| `delete_connection_group()` | 1291-1351 | `delete_connection_group(cursor, conngroup_id)` | Update children |
| `_check_connection_group_cycle()` | 2082-2126 | `check_connection_group_cycle(cursor, group_id, parent_id)` | Validation helper |

### Permissions Repository (`permissions_repo.py`) - Phase 9
| Current Method Domain | Lines Range | Repository Functions | Notes |
|----------------------|-------------|----------------------|-------|
| User-to-Connection permissions | Various | `grant_user_connection(cursor, ...)`, `deny_user_connection(cursor, ...)` | INSERT/DELETE in permission tables |
| User-to-ConnGroup permissions | Various | `grant_user_conngroup(cursor, ...)`, `deny_user_conngroup(cursor, ...)` | INSERT/DELETE in permission tables |
| UserGroup-to-Connection permissions | Various | `grant_usergroup_connection(cursor, ...)`, `deny_usergroup_connection(cursor, ...)` | INSERT/DELETE in permission tables |
| UserGroup-to-ConnGroup permissions | Various | `grant_usergroup_conngroup(cursor, ...)`, `deny_usergroup_conngroup(cursor, ...)` | INSERT/DELETE in permission tables |
| Permission listing | Various | `list_user_permissions(cursor, ...)`, `list_usergroup_permissions(cursor, ...)` | Query permission tables |

---

## Appendix B: Resolved Issues from Previous Revisions

### **Issues Fixed in Revision 5 (from Revision 4):**
1. ✅ **Removed conditional decision gate** - Phase 4 now plans repositories, doesn't decide
2. ✅ **Reclassified P4** - From "LOW - Monolithic File" to "HIGH - Mixed Responsibilities"
3. ✅ **Added splitting justification** - Clear rationale based on testability, safety, clarity (not LLM limits)
4. ✅ **Detailed Phases 5-10** - Concrete extraction steps for each repository
5. ✅ **Committed to final architecture** - guac_db.py facade + 5 repositories + db_utils.py
6. ✅ **Updated success criteria** - Phase-by-phase outcomes documented
7. ✅ **Walking skeleton approach** - Phase 5 validates before continuing

### **Issues Fixed in Revision 4 (from Revision 3):**
1. ✅ **Removed security.py** - Single function, no duplication, keep in façade
2. ✅ **Removed errors.py** - ValueError sufficient, no custom exceptions needed
3. ✅ **Removed db_base.py** - Simplified to db_utils.py (utilities only), config stays in façade
4. ✅ **Fixed transaction documentation** - Lines 1284, 1341 marked for removal
5. ✅ **Added evidence-based approach** - Problem statement documents actual pain points
6. ✅ **Added PLAN.md compliance** - YAGNI, KISS, TDD alignment throughout

### **Complexity Comparison:**
- **Revision 3:** 8 new files (db_base.py, users.py, usergroups.py, connections.py, conngroups.py, guac_db.py, security.py, errors.py)
- **Revision 4 (Conditional):** 1-5 new files depending on Phase 4 decision
- **Revision 5 (Committed):** 7 new files (db_utils.py + 5 repositories + guac_db.py) + 1 deprecated (db.py → re-export)

---

## Plan Revision History

### **Revision 5 (2025-10-24)** - Repository Pattern Committed
- **Commitment to splitting**: Phase 4 decision gate removed, repository extraction committed
- **P4 reclassified**: From "LOW - Monolithic File" to "HIGH - Mixed Responsibilities"
- **Justification added**: Clear rationale for splitting (testability, safety, clarity, not LLM limits)
- **Phases 5-10 detailed**: Concrete extraction steps for each repository (users, usergroups, connections, conngroups, permissions)
- **Walking skeleton**: Phase 5 validates approach before continuing
- **Final architecture**: guac_db.py facade (~400 lines) + 5 repositories + db_utils.py
- **Risk management**: Each phase independently testable, reversible via git
- **Documentation plan**: Update README.md, CLAUDE.md, add migration guide

### **Revision 4 (2025-10-23)** - PLAN.md Compliance (Superseded)
- **PLAN.md alignment**: Evidence-driven, incremental, YAGNI/KISS compliant
- **Problem statement**: Documented actual pain points (P1-P4) with code evidence
- **Minimal viable refactor**: Phases 1-3 fix real bugs without speculation
- **Conditional domain split**: Phase 4 decision gate based on measured impact
- **Removed overengineering**: Eliminated security.py, errors.py, simplified db_base.py to db_utils.py
- **Issue:** Left decision to split as conditional, delaying commitment

### **Revision 3 (2025-10-23)** - Simplified (Superseded)
- Removed module/service pattern, no dependency injection
- **Issue:** Still added 8 new files without evidence of need

### **Revision 2 (2025-10-23)** - Code Analysis & Validation (Superseded)
- Verified line numbers against actual codebase
- **Issue:** Preserved overengineered architecture from Revision 1

### **Revision 1 (Original)** - Enterprise Architecture (Superseded)
- Module/service pattern with dependency injection
- **Issue:** Severe overengineering for CLI tool

**This plan is now READY FOR EXECUTION with clear commitment to repository extraction, evidence-driven approach, and incremental delivery.**
