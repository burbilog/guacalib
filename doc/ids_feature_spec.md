# Complete Specification: --id Implementation for Connections and Connection Groups

# Overview

Add --id parameter support to uniquely identify connections and connection groups by their database IDs, resolving naming ambiguity in hierarchical structures.

# Scope

 • Connection commands: delete, exists, modify
 • Connection group commands: delete, exists, modify
 • Enhanced list commands (always show IDs)
 • Basic test coverage

# Requirements

1. CLI Parameter Changes

1.1 New Parameters

 • Add --id parameter to specific subcommands
 • --id and --name are mutually exclusive
 • --id must be a positive integer

1.2 Affected Commands

1.2.1 Connection commands

guacaman conn delete --id <connection_id>  
guacaman conn exists --id <connection_id>  
guacaman conn modify --id <connection_id> [other options]

1.2.2 Connection group commands

guacaman conngroup delete --id <group_id>  
guacaman conngroup exists --id <group_id>  
guacaman conngroup modify --id <group_id> [other options]

1.2.3 Enhanced list commands

guacaman conn list  
guacaman conngroup list

2. Database Layer Requirements

## Stage 1: Database Layer - Enhanced Existing Methods

Files: guacalib/db.py

Tasks:

 • [ ] Add **two** reusable internal helper methods:
    - `resolve_connection_id(connection_name=None, connection_id=None)` to validate inputs, ensure exactly one is provided, check ID validity, and resolve IDs from names if needed.
    - `resolve_conngroup_id(group_name=None, group_id=None)` to do the same for connection groups.
 • [ ] Update the following existing methods to accept optional `*_id` arguments and internally call the relevant resolver:
    - delete_existing_connection()
    - delete_connection_group()
    - modify_connection()
    - modify_connection_group_parent()
    - modify_connection_parent_group()
    - connection_exists()
    - connection_group_exists()
    - grant_connection_permission_to_user()
    - revoke_connection_permission_from_user()
    - get_connection_user_permissions()
 • [ ] All validation for “exactly one of name or ID” and “positive integer IDs” performed inside the shared resolver methods.
 • [ ] Ensure all enhanced methods maintain backward compatibility with existing name-based calls.

Verification Steps:

 • [ ] Implement Stage 1 database method tests in tests/test_guacaman.bats  
 • [ ] Test each enhanced method with both name and ID parameters  
 • [ ] Verify validation logic (exactly one parameter required)  
 • [ ] Test error handling for non-existent IDs  
 • [ ] Confirm backward compatibility with existing method calls

Acceptance Criteria:

 • All enhanced methods work with both name and ID parameters  
 • Validation ensures exactly one of name or ID is provided  
 • Methods handle non-existent IDs gracefully with clear error messages  
 • Database errors are caught and re-raised  
 • Existing method calls continue to work unchanged  
 • No code duplication between name and ID handling paths — all handled in the two resolver helpers

## Stage 2: Enhanced List Commands

Files: guacalib/db.py, guacalib/cli_handle_conn.py, guacalib/cli_handle_conngroup.py

Tasks:

 • [ ] Update `list_connections_with_conngroups_and_parents()` (DB) to always include `id` in its return structure alongside existing fields.
 • [ ] Update `list_connection_groups()` (DB) to always include `id` in its return structure.
 • [ ] Modify CLI printing in `handle_conn_list()` to display each connection’s `id`.
 • [ ] Modify CLI printing in `handle_conngroup_command()` (list subcommand) to display each connection group’s `id`.
 • [ ] Ensure both the DB return data and the CLI output contain `id` fields in the expected structure.

Verification Steps:

 • [ ] Implement Stage 2 list output format tests in tests/test_guacaman.bats  
 • [ ] Verify list methods return ID information in correct format in DB and CLI layers  
 • [ ] Check that ID values match actual database IDs  
 • [ ] Ensure existing output structure is preserved and augmented with IDs  
 • [ ] Test with empty databases and populated data

Acceptance Criteria:

 • List methods always include `id` in their return structures (DB)  
 • CLI output shows IDs for each entity in a clear and consistent position  
 • ID information is accurate and matches database values  
 • Output format remains consistent and parseable  
 • ID field integration does not break existing scripts relying only on name keys

## Stage 3: CLI Argument Parser Updates

Files: guacalib/cli.py

Tasks:

 • [ ] Add --id parameter to conn delete subcommand
 • [ ] Add --id parameter to conn exists subcommand
 • [ ] Add --id parameter to conn modify subcommand
 • [ ] Add --id parameter to conngroup delete subcommand
 • [ ] Add --id parameter to conngroup exists subcommand
 • [ ] Add --id parameter to conngroup modify subcommand

Verification Steps:

 • [ ] Implement Stage 3 CLI argument parser tests in tests/test_guacaman.bats  
 • [ ] Test argument parser help text includes --id parameters  
 • [ ] Verify --id parameter accepts integer values  
 • [ ] Test that --id and --name are properly parsed as separate options  
 • [ ] Check help text clarity

Acceptance Criteria:

 • All new parameters defined with correct types  
 • Help text is accurate  
 • Parameters are optional and don’t break existing functionality  
 • Parser handles --id and --name correctly

## Stage 4: Connection Command Handlers with Validation

Files: guacalib/cli_handle_conn.py

Tasks:

 • [ ] Update handle_conn_delete(), handle_conn_exists(), handle_conn_modify() to support --id and pass to enhanced DB methods
 • [ ] Update handle_conn_list() to always show IDs
 • [ ] Add syntax-level validation in handlers: ensure that at least one of --name or --id is provided (business rule validation will be centralized in Stage 1 resolvers)
 • [ ] Add ID format validation (positive integer, strictly greater than 0) in handlers
 • [ ] Proper error handling for invalid or non-existent IDs
 • [ ] Pass correct params to DB methods

Verification Steps:

 • [ ] Implement Stage 4 tests in tests/test_guacaman.bats  
 • [ ] Test everything with both valid and invalid IDs/names  
 • [ ] Verify list command shows IDs in output  
 • [ ] Test backward compatibility with --name usage

Acceptance Criteria:

 • Works with both name and ID  
 • Validation in handlers  
 • Correct DB calls  
 • Clear error messages for invalid IDs  
 • Backward compatible  
 • Matches existing error formatting

## Stage 5: Connection Group Command Handlers with Validation

Files: guacalib/cli_handle_conngroup.py

Tasks:

 • [ ] Update relevant branches to support --id and pass to enhanced DB methods
 • [ ] Update list subcommand to show IDs
 • [ ] Add syntax-level validation in handlers: ensure at least one parameter is provided, format for ID is a positive integer >0 (business rule validation kept in Stage 1 resolvers)
 • [ ] Add ID format validation (>0, integer)
 • [ ] Handle invalid/non-existent IDs
 • [ ] Pass correct params to DB

Verification Steps:

 • [ ] Implement Stage 5 tests in tests/test_guacaman.bats  
 • [ ] Test with valid and invalid IDs  
 • [ ] Validate errors for multiple/both/missing params  
 • [ ] Verify list output shows IDs  
 • [ ] Confirm backward compatibility  
 • [ ] Verify cycle detection works with IDs

Acceptance Criteria:

 • Works with both name and ID  
 • Validation rules in handlers  
 • Correct parameters passed to DB  
 • Clear error messages  
 • Backward compatibility  
 • Cycle detection intact

## Stage 6: Integration Tests

Files: tests/test_guacaman.bats (add new tests to existing file)

Tasks:

 • [ ] Test conn delete --id  
 • [ ] Test conn exists --id for existing/non-existing  
 • [ ] Test conn modify --id  
 • [ ] Test conn list includes id field  
 • [ ] Test conngroup delete --id  
 • [ ] Test conngroup exists --id  
 • [ ] Test conngroup modify --id  
 • [ ] Test conngroup list includes id  
 • [ ] Test validation errors for both/missing params  
 • [ ] Test invalid ID formats  
 • [ ] Backward compatibility

Acceptance Criteria:

 • CLI commands tested with ID and name  
 • Error messages tested  
 • Output formats validated with ID field  
 • Backward compatibility verified

## Stage 7: Final Integration Testing

Files: All modified files, existing test suite

Tasks:

 • [ ] Run full existing test suite  
 • [ ] Test all commands with valid IDs realistically  
 • [ ] Test with invalid IDs  
 • [ ] Validate both/missing parameter rules  
 • [ ] Verify backward compatibility  
 • [ ] List commands always show IDs  
 • [ ] Check error messages clarity

Acceptance Criteria:

 • Graceful error handling  
 • User-friendly messages  
 • No regressions  
 • All tests pass

Test Coverage Requirements

 • DB layer: 80% coverage of new methods  
 • CLI handlers: 85% coverage of new ID-handling paths  
 • Integration: all major cases and errors covered

Success Criteria

 • Users can specify connections/groups by ID  
 • All existing functions unchanged in behavior  
 • Clear error messages  
 • List commands always show IDs  
 • Robust to edge cases
 • Business rule validation for "exactly one of name or ID" is centralized in Stage 1 resolvers to avoid duplication

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

 • User/usergroup ID support  
 • Creation with ID  
 • Bulk ID operations  
 • Conflict discovery  
 • Performance optimization
