# TDD Plan: --id Implementation for User Groups

Overview

Add --id parameter support to uniquely identify user groups by their database IDs, following the proven patterns already implemented for connections and connection groups. We will follow a strict test-driven development (TDD) workflow: write failing tests first, then implement the minimal code to make them pass, and finally refactor.

Guiding Principles

- Tests first: No production code changes until the failing tests exist.
- Consistency: Mirror the UX, CLI parser shape, and error messaging used by connections/conngroups.
- Backward compatibility: Name-based behavior remains unchanged.
- Small, verifiable steps: Commit after each small red→green cycle.

Scope

- User group subcommands: del, exists, modify
- List output enhanced to always show ID for user groups
- Integration tests in tests/test_guacaman.bats

Out of Scope

- Changing dump output format
- Adding new database tables
- Altering permissions model

Progress Checklist (High-Level)

- [ ] Write tests (fail first)
- [ ] Implement minimal code to pass tests
- [ ] Refactor and cleanup
- [ ] Documentation updates complete

## Small Checkable Stages

### Stage UG-01: Test Infrastructure Setup
**Target: tests/run_tests.bats**
- [ ] Add helper function: `get_usergroup_id "<group_name>"` 
- [ ] Verify helper works with existing list output (should fail initially)
- **Checkable**: Run `make tests` - helper should be defined but fail to find IDs

### Stage UG-02: Parser Validation Tests (exists)
**Target: tests/test_usergroup_ids.bats**
- [ ] Test `usergroup exists` with both --name and --id → exit 2
- [ ] Test `usergroup exists` with neither → exit 2  
- [ ] Test `usergroup exists` with invalid ID (0, -1) → validation error
- **Checkable**: Run specific test block - all should fail with parser errors

### Stage UG-03: Parser Validation Tests (del)
**Target: tests/test_usergroup_ids.bats**
- [ ] Test `usergroup del` with both --name and --id → exit 2
- [ ] Test `usergroup del` with neither → exit 2
- [ ] Test `usergroup del` with invalid ID (0, -1) → validation error
- **Checkable**: Run specific test block - all should fail with parser errors

### Stage UG-04: Parser Validation Tests (modify)
**Target: tests/test_usergroup_ids.bats**
- [ ] Test `usergroup modify` with both selectors → exit 2
- [ ] Test `usergroup modify` with neither → exit 2
- [ ] Test `usergroup modify` with invalid ID → validation error
- [ ] Test `usergroup modify` with no modification flags → usage/help
- **Checkable**: Run specific test block - all should fail appropriately

### Stage UG-05: Database Layer - Resolver Function
**Target: guacalib/db.py**
- [ ] Add `resolve_usergroup_id(usergroup_name=None, usergroup_id=None)`
- [ ] Implement exactly-one-selector validation
- [ ] Implement positive integer validation
- [ ] Implement name→ID lookup with "not found" messages
- [ ] Implement ID existence verification
- **Checkable**: Unit test resolver function directly with various inputs

### Stage UG-06: Database Layer - Enhanced Methods (exists/delete)
**Target: guacalib/db.py**
- [ ] Update `usergroup_exists()` to accept optional usergroup_id parameter
- [ ] Update `delete_existing_usergroup()` to accept optional usergroup_id parameter
- [ ] Both methods use `resolve_usergroup_id()` internally
- **Checkable**: Test both methods with name and ID parameters

### Stage UG-07: Database Layer - Enhanced Methods (modify)
**Target: guacalib/db.py**
- [ ] Update `add_user_to_usergroup()` to accept optional usergroup_id
- [ ] Update `remove_user_from_usergroup()` to accept optional usergroup_id
- [ ] Both methods use `resolve_usergroup_id()` internally
- **Checkable**: Test both methods with name and ID parameters

### Stage UG-08: Database Layer - List Enhancement
**Target: guacalib/db.py**
- [ ] Update `list_usergroups_with_users_and_connections()` to include ID field
- [ ] Ensure ID is included in return structure for each group
- **Checkable**: Call method directly and verify ID field present

### Stage UG-09: CLI Parser - exists Command
**Target: guacalib/cli.py**
- [ ] Add --id parameter to `usergroup exists` subcommand
- [ ] Add mutually exclusive group for --name/--id
- [ ] Set --id type=int
- [ ] Update help text to match connection patterns
- **Checkable**: Run `guacaman usergroup exists --help` - should show --id option

### Stage UG-10: CLI Parser - del Command  
**Target: guacalib/cli.py**
- [ ] Add --id parameter to `usergroup del` subcommand
- [ ] Add mutually exclusive group for --name/--id
- [ ] Set --id type=int
- **Checkable**: Run `guacaman usergroup del --help` - should show --id option

### Stage UG-11: CLI Parser - modify Command
**Target: guacalib/cli.py**
- [ ] Add --id parameter to `usergroup modify` subcommand  
- [ ] Add mutually exclusive group for --name/--id
- [ ] Set --id type=int
- **Checkable**: Run `guacaman usergroup modify --help` - should show --id option

### Stage UG-12: CLI Handler - exists Command
**Target: guacalib/cli_handle_usergroup.py**
- [ ] Update `handle_usergroup_command()` for exists subcommand
- [ ] Add `validate_selector(args, "usergroup")` call
- [ ] Pass usergroup_id to database method when args.id provided
- **Checkable**: Run UG-02 tests - should now pass parser validation

### Stage UG-13: CLI Handler - del Command
**Target: guacalib/cli_handle_usergroup.py**
- [ ] Update del subcommand handler
- [ ] Add `validate_selector(args, "usergroup")` call
- [ ] Pass usergroup_id to database method when args.id provided
- **Checkable**: Run UG-03 tests - should now pass parser validation

### Stage UG-14: CLI Handler - modify Command
**Target: guacalib/cli_handle_usergroup.py**
- [ ] Update modify subcommand handler
- [ ] Add `validate_selector(args, "usergroup")` call
- [ ] Pass usergroup_id to database methods when args.id provided
- **Checkable**: Run UG-04 tests - should now pass parser validation

### Stage UG-15: CLI Handler - List Enhancement
**Target: guacalib/cli_handle_usergroup.py**
- [ ] Update list subcommand to display id: field
- [ ] Maintain existing output structure with ID added
- **Checkable**: Run `guacaman usergroup list` - should show id: field

### Stage UG-16: Integration Tests - exists Functionality
**Target: tests/test_usergroup_ids.bats**
- [ ] Test `exists --id <valid_id>` returns 0
- [ ] Test `exists --id <nonexistent_id>` returns 1
- [ ] Test backward compatibility with --name
- **Checkable**: Run specific test block - all should pass

### Stage UG-17: Integration Tests - delete Functionality
**Target: tests/test_usergroup_ids.bats**
- [ ] Test `del --id <valid_id>` succeeds
- [ ] Test `del --id <nonexistent_id>` fails appropriately
- [ ] Test backward compatibility with --name
- **Checkable**: Run specific test block - all should pass

### Stage UG-18: Integration Tests - modify Functionality
**Target: tests/test_usergroup_ids.bats**
- [ ] Test `modify --id <group_id> --adduser user` succeeds
- [ ] Test `modify --id <group_id> --rmuser user` succeeds
- [ ] Test error cases (nonexistent user/group, non-member removal)
- [ ] Test backward compatibility with --name
- **Checkable**: Run specific test block - all should pass

### Stage UG-19: Integration Tests - List Output
**Target: tests/test_usergroup_ids.bats**
- [ ] Test list includes ID field for all groups
- [ ] Test ID values are positive integers
- [ ] Test output structure preserved
- **Checkable**: Run specific test block - all should pass

### Stage UG-20: Full Regression Testing
**Target: Entire test suite**
- [ ] Run all existing tests to ensure no regressions
- [ ] Run all new usergroup ID tests
- [ ] Verify error message consistency with connections/conngroups
- **Checkable**: `make tests` - all tests should pass

### Stage UG-21: Documentation Updates
**Target: README.md and feature spec**
- [ ] Update README with new --id parameter examples
- [ ] Mark feature spec as complete
- [ ] Update any relevant help text
- **Checkable**: Review documentation for accuracy

## Example Test Snippets (bats, indicative)

Note: These are planning examples; actual tests will be added in tests/test_usergroup_ids.bats.

- Selector validation for exists:
```bash
run guacaman --config "$TEST_CONFIG" usergroup exists --name g --id 1
[ "$status" -eq 2 ]
[[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"Exactly one of --name or --id must be provided"* ]]

run guacaman --config "$TEST_CONFIG" usergroup exists
[ "$status" -eq 2 ]
[[ "$output" == *"one of the arguments --name --id is required"* ]] || [[ "$output" == *"Exactly one"* ]]
```

- List includes ID:
```bash
run guacaman --config "$TEST_CONFIG" usergroup list
[ "$status" -eq 0 ]
[[ "$output" == *"usergroups:"* ]]
[[ "$output" == *"id:"* ]]
ids=$(echo "$output" | grep -A1 "^  [^:]\+:" | grep "id:" | cut -d: -f2 | tr -d ' ')
for id in $ids; do [ "$id" -gt 0 ]; done
```

- Modify by ID:
```bash
gid=$(get_usergroup_id "testgroup1")
run guacaman --config "$TEST_CONFIG" usergroup modify --id "$gid" --adduser testuser1
[ "$status" -eq 0 ]
[[ "$output" == *"Successfully added user 'testuser1' to usergroup 'testgroup1'"* ]]
```

## Risks and Edge Cases

- Groups with identical names should not exist (DB uniqueness by entity name); ensure resolver messages are deterministic.
- Large ID values: must gracefully return "not found" without crashing.
- Output parsing in tests should be robust to minor whitespace differences (use grep patterns accordingly).

## Implementation Patterns (Reference)

- Use existing resolve_connection_id / resolve_conngroup_id as templates for resolve_usergroup_id.
- Use validate_selector(args, "usergroup") uniformly in handlers.
- Keep list output structure aligned with existing list handlers.

## Definition of Done

- [ ] Tests for usergroup IDs are merged and initially failing on main
- [ ] Database layer and CLI code implemented to make tests pass
- [ ] Code reviewed for consistency with AGENTS.md (types, clarity, errors)
- [ ] Documentation updated (this file) and README if CLI flags surface to users
