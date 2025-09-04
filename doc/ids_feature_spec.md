# Complete Specification: --id Implementation for Connections and Connection Groups

# Overview

Add --id parameter support to uniquely identify connections and connection groups by their database IDs, resolving naming ambiguity in hierarchical structures.

# Scope

- Connection commands: del, exists, modify
- Connection group commands: del, exists, modify
- Enhanced list commands (always show IDs)
- Basic test coverage

# Requirements

1. CLI Parameter Changes

1.1 New Parameters

- Add --id parameter to specific subcommands
- --id and --name are mutually exclusive (business rule)
- --id must be a positive integer (> 0)

1.2 Affected Commands

1.2.1 Connection commands

guacaman conn del --id <connection_id>  
guacaman conn exists --id <connection_id>  
guacaman conn modify --id <connection_id> [other options]

1.2.2 Connection group commands

guacaman conngroup del --id <group_id>  
guacaman conngroup exists --id <group_id>  
guacaman conngroup modify --id <group_id> [other options]

1.3 Selector semantics for modify

- The target entity must be selected by exactly one of --name or --id.
- New values to apply are expressed via existing options (e.g., --set param=value, --parent, --permit/--deny). Selector options are not considered modifications.

2. Database Layer Requirements

## Stage 1: Database Layer - Enhanced Existing Methods

Files: guacalib/db.py

Tasks:

- [x] Add two reusable internal helper methods:
  - `resolve_connection_id(connection_name=None, connection_id=None)` to validate inputs, ensure exactly one is provided, enforce id > 0, and resolve IDs from names if needed.
  - `resolve_conngroup_id(group_name=None, group_id=None)` to do the same for connection groups.
- [x] Update the following existing methods to accept optional `*_id` arguments and internally call the relevant resolver:
  - delete_existing_connection()
  - delete_connection_group()
  - modify_connection()
  - modify_connection_group_parent()
  - modify_connection_parent_group()
  - connection_exists()
  - connection_group_exists()
- [x] All validation for "exactly one of name or ID" and "positive integer IDs" is performed inside the shared resolver methods.
- [x] Ensure all enhanced methods maintain backward compatibility with existing name-based calls.
- [ ] Note: Permission-related methods (grant/revoke/get permissions) are out of scope and unchanged in this feature.

Verification Steps:

- [x] Implement Stage 1 tests in tests/test_guacaman.bats (integration-focus)  
- [x] Test each enhanced method path via CLI with both name and ID selectors  
- [x] Verify validation logic ("exactly one parameter required")  
- [x] Test error handling for non-existent IDs  
- [x] Confirm backward compatibility with existing name-based calls

Acceptance Criteria:

- All enhanced methods work with both name and ID parameters  
- Validation ensures exactly one of name or ID is provided  
- Methods handle non-existent IDs gracefully with clear error messages  
- Database errors are caught and re-raised  
- Existing method calls continue to work unchanged  
- No code duplication between name and ID handling paths — all handled in the two resolver helpers

## Stage 2: Enhanced List Commands

Files: guacalib/db.py, guacalib/cli_handle_conn.py, guacalib/cli_handle_conngroup.py

Tasks:

- [x] Update `list_connections_with_conngroups_and_parents()` (DB) to always include `id` in its return structure alongside existing fields.
- [x] Update `list_connection_groups()` (DB) to always include `id` in its return structure.
- [x] Modify CLI printing in `handle_conn_list()` to display each connection's `id` directly under the connection name as a separate YAML key `id: <ID>`.
- [x] Modify CLI printing in `handle_conngroup_command()` (list subcommand) to display each connection group's `id` directly under the group name as `id: <ID>`.
- [x] Ensure both the DB return data and the CLI output contain `id` fields in the expected structure and stable position.

Verification Steps:

- [x] Implement Stage 2 list output format tests in tests/test_guacaman.bats  
- [x] Verify list methods return ID information in correct format in DB and CLI layers  
- [x] Check that ID values match actual database IDs  
- [x] Ensure existing output structure is preserved and augmented with IDs  
- [x] Test with empty databases and populated data

Acceptance Criteria:

- List methods always include `id` in their return structures (DB)  
- CLI output shows IDs for each entity in a clear and consistent position  
- ID information is accurate and matches database values  
- Output format remains consistent and parseable  
- ID field integration does not break existing scripts relying only on name keys

Stage 2 Output Format Specification:

- Connection list (YAML-like) — `id` inserted as a first field within each mapping:

Before:
```yaml
connections:
  web-01:
    type: vnc
    hostname: 10.0.0.1
    port: 5900
    parent: prod
    groups:
      - admins
```

After:
```yaml
connections:
  web-01:
    id: 42
    type: vnc
    hostname: 10.0.0.1
    port: 5900
    parent: prod
    groups:
      - admins
```

- Connection group list (YAML-like) — `id` inserted as a first field within each mapping:

Before:
```yaml
conngroups:
  prod:
    parent: ROOT
    connections:
      - web-01
```

After:
```yaml
conngroups:
  prod:
    id: 7
    parent: ROOT
    connections:
      - web-01
```

Notes:
- Key names remain unchanged; only a new key `id` is added.
- Key order is stable: `id` precedes `type`/`parent` etc.
- If a parent is not set, `parent` remains `ROOT`.

## Stage 3: CLI Argument Parser Updates

Files: guacalib/cli.py

Tasks:

- [x] Add --id parameter to conn del subcommand
- [x] Add --id parameter to conn exists subcommand
- [x] Add --id parameter to conn modify subcommand
- [x] Add --id parameter to conngroup del subcommand
- [x] Add --id parameter to conngroup exists subcommand
- [x] Add --id parameter to conngroup modify subcommand
- [x] Add a mutually exclusive group for --name and --id in each affected subparser; do not mark the group as required to preserve backward compatibility. Set --id type=int.
- [x] Ensure help text clearly states: "Exactly one of --name or --id must be provided."

Verification Steps:

- [x] Implement Stage 3 CLI argument parser tests in tests/test_guacaman.bats  
- [x] Test argument parser help text includes --id parameters and the exclusivity note  
- [x] Verify --id parameter accepts integer values  
- [x] Test that --id and --name are properly parsed as separate options  
- [x] Check help text clarity

Acceptance Criteria:

- [x] All new parameters defined with correct types  
- [x] Help text is accurate  
- [x] Parameters are optional and don't break existing functionality  
- [x] Parser handles --id and --name correctly

## Stage 4: Connection Command Handlers with Validation

Files: guacalib/cli_handle_conn.py

Tasks:

- [x] Update handle_conn_delete(), handle_conn_exists(), handle_conn_modify() to support --id and pass to enhanced DB methods
- [x] Update handle_conn_list() to always show IDs
- [x] Add syntax-level validation in handlers: ensure that at least one of --name or --id is provided
- [x] Do not duplicate business-rule validation in handlers; "exactly one" and "positive integer" checks live in Stage 1 resolvers
- [x] Proper error handling for invalid or non-existent IDs (surfaces resolver/DB errors with clear messages)
- [x] Pass correct params to DB methods

Verification Steps:

- [x] Implement Stage 4 tests in tests/test_guacaman.bats  
- [x] Test everything with both valid and invalid IDs/names  
- [x] Verify list command shows IDs in output  
- [x] Test backward compatibility with --name usage

Acceptance Criteria:

- [x] Works with both name and ID  
- [x] Validation in handlers for presence of at least one selector  
- [x] Correct DB calls  
- [x] Clear error messages for invalid IDs  
- [x] Backward compatible  
- [x] Matches existing error formatting

## Stage 5: Connection Group Command Handlers with Validation

Files: guacalib/cli_handle_conngroup.py

Tasks:

- [ ] Update relevant branches to support --id and pass to enhanced DB methods
- [ ] Update list subcommand to show IDs
- [ ] Add syntax-level validation in handlers: ensure at least one selector (--name or --id) is provided (business-rule validation remains in resolvers)
- [ ] Do not duplicate ID format or “exactly one” validation in handlers; rely on resolvers
- [ ] Handle invalid/non-existent IDs
- [ ] Pass correct params to DB

Verification Steps:

- [ ] Implement Stage 5 tests in tests/test_guacaman.bats  
- [ ] Test with valid and invalid IDs  
- [ ] Validate errors for multiple/both/missing params  
- [ ] Verify list output shows IDs  
- [ ] Confirm backward compatibility  
- [ ] Verify cycle detection works with IDs

Acceptance Criteria:

- Works with both name and ID  
- Validation rules in handlers (presence)  
- Correct parameters passed to DB  
- Clear error messages  
- Backward compatibility  
- Cycle detection intact

## Stage 6: Integration Tests

Files: tests/test_guacaman.bats (add new tests to existing file)

Tasks:

- [ ] Test conn del --id  
- [ ] Test conn exists --id for existing/non-existing  
- [ ] Test conn modify --id  
- [ ] Test conn list includes id field  
- [ ] Test conngroup del --id  
- [ ] Test conngroup exists --id  
- [ ] Test conngroup modify --id  
- [ ] Test conngroup list includes id  
- [ ] Test validation errors for both/missing params  
- [ ] Test invalid ID formats (negative/zero via resolvers; non-integer rejected by argparse)  
- [ ] Backward compatibility

Acceptance Criteria:

- CLI commands tested with ID and name  
- Error messages tested  
- Output formats validated with id field  
- Backward compatibility verified

## Stage 7: Final Integration Testing

Files: All modified files, existing test suite

Tasks:

- [ ] Run full existing test suite  
- [ ] Test all commands with valid IDs realistically  
- [ ] Test with invalid IDs  
- [ ] Validate both/missing parameter rules  
- [ ] Verify backward compatibility  
- [ ] List commands always show IDs  
- [ ] Check error messages clarity

Acceptance Criteria:

- Graceful error handling  
- User-friendly messages  
- No regressions  
- All tests pass

Testing Approach

- Primary: integration tests in `tests/test_guacaman.bats` covering both name- and id-based flows and error cases; validate list output format.
- Optional (future): add pytest unit tests for db resolvers and handlers to measure coverage. Numeric coverage targets are out of scope for this feature.

Success Criteria

- Users can specify connections/groups by ID  
- All existing functions unchanged in behavior  
- Clear error messages  
- List commands always show IDs  
- Robust to edge cases
- Business rule validation for "exactly one of name or ID" is centralized in Stage 1 resolvers to avoid duplication

Error Messages and Exit Codes

- Exactly one of --id or --name must be provided  
  - Applies when both or neither are provided  
  - Exit code: 1 (argparse parse errors may exit with 2)  
- Invalid --id: must be a positive integer (> 0)  
  - Raised by resolvers if id <= 0  
  - Exit code: 1  
- Connection not found: id=<ID>/name=<NAME>  
  - Exit code: 1  
- Connection group not found: id=<ID>/name=<NAME>  
  - Exit code: 1  
- exists subcommands:  
  - 0 if entity exists  
  - 1 if entity does not exist

Implementation Benefits

- ✅ Minimal code duplication via two resolvers
- ✅ Single logic path for name and ID
- ✅ Backward compatible
- ✅ Consistent logic and output
- ✅ Easier testing, fewer code paths

CLI Integration Pattern

```python
if args.id:
    guacdb.delete_existing_connection(connection_id=args.id)
else:
    guacdb.delete_existing_connection(connection_name=args.name)
```

Database Method Enhancement Pattern

```python
def delete_existing_connection(self, connection_name=None, connection_id=None):
    conn_id = self.resolve_connection_id(connection_name, connection_id)
    # operate on conn_id only...
```

Out of Scope

- User/usergroup ID support  
- Creation with ID  
- Bulk ID operations  
- Conflict discovery  
- Performance optimization
