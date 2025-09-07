# Complete Specification: --id Implementation for User Groups

# Overview

Add --id parameter support to uniquely identify user groups by their database IDs, resolving naming ambiguity in hierarchical structures. Users are excluded from this feature as they are system-unique.

# Scope

- User group commands: del, exists, modify
- Enhanced list commands (always show IDs)
- Basic test coverage

# Requirements

1. CLI Parameter Changes

1.1 New Parameters

- Add --id parameter to specific subcommands
- --id and --name are mutually exclusive (business rule)
- --id must be a positive integer (> 0)

1.2 Affected Commands

1.2.1 User group commands

guacaman usergroup del --id <usergroup_id>  
guacaman usergroup exists --id <usergroup_id>  
guacaman usergroup modify --id <usergroup_id> [other options]

1.3 Selector semantics for modify

- The target entity must be selected by exactly one of --name or --id.
- New values to apply are expressed via existing options (e.g., --adduser, --rmuser). Selector options are not considered modifications.

2. Database Layer Requirements

## Stage 1: Database Layer - Enhanced Existing Methods

Files: guacalib/db.py

Tasks:

- [ ] Add two reusable internal helper methods:
  - `resolve_usergroup_id(usergroup_name=None, usergroup_id=None)` to validate inputs, ensure exactly one is provided, enforce id > 0, and resolve IDs from names if needed.
  - Update the following existing methods to accept optional `*_id` arguments and internally call the relevant resolver:
    - delete_existing_usergroup()
    - usergroup_exists()
    - add_user_to_usergroup()
    - remove_user_from_usergroup()
- [ ] All validation for "exactly one of name or ID" and "positive integer IDs" is performed inside the shared resolver methods.
- [ ] Ensure all enhanced methods maintain backward compatibility with existing name-based calls.
- [ ] Note: User-related methods are out of scope and unchanged in this feature.

Verification Steps:

- [ ] Implement Stage 1 tests in tests/test_guacaman.bats (integration-focus)  
- [ ] Test each enhanced method path via CLI with both name and ID selectors  
- [ ] Verify validation logic ("exactly one parameter required")  
- [ ] Test error handling for non-existent IDs  
- [ ] Confirm backward compatibility with existing name-based calls

Acceptance Criteria:

- All enhanced methods work with both name and ID parameters  
- Validation ensures exactly one of name or ID is provided  
- Methods handle non-existent IDs gracefully with clear error messages  
- Database errors are caught and re-raised  
- Existing method calls continue to work unchanged  
- No code duplication between name and ID handling paths — all handled in the two resolver helpers

## Stage 2: Enhanced List Commands

Files: guacalib/db.py, guacalib/cli_handle_usergroup.py

Tasks:

- [ ] Update `list_usergroups_with_users_and_connections()` (DB) to always include `id` in its return structure alongside existing fields.
- [ ] Modify CLI printing in `handle_usergroup_command()` (list subcommand) to display each user group's `id` directly under the group name as a separate YAML key `id: <ID>`.
- [ ] Ensure both the DB return data and the CLI output contain `id` fields in the expected structure and stable position.

Verification Steps:

- [ ] Implement Stage 2 list output format tests in tests/test_guacaman.bats  
- [ ] Verify list methods return ID information in correct format in DB and CLI layers  
- [ ] Check that ID values match actual database IDs  
- [ ] Ensure existing output structure is preserved and augmented with IDs  
- [ ] Test with empty databases and populated data

Acceptance Criteria:

- List methods always include `id` in their return structures (DB)  
- CLI output shows IDs for each entity in a clear and consistent position  
- ID information is accurate and matches database values  
- Output format remains consistent and parseable  
- ID field integration does not break existing scripts relying only on name keys

## Stage 3: CLI Argument Parser Updates

Files: guacalib/cli.py

Tasks:

- [ ] Add --id parameter to usergroup del subcommand
- [ ] Add --id parameter to usergroup exists subcommand
- [ ] Add --id parameter to usergroup modify subcommand
- [ ] Add a mutually exclusive group for --name and --id in each affected subparser; do not mark the group as required to preserve backward compatibility. Set --id type=int.
- [ ] Ensure help text clearly states: "Exactly one of --name or --id must be provided."

Verification Steps:

- [ ] Implement Stage 3 CLI argument parser tests in tests/test_guacaman.bats  
- [ ] Test argument parser help text includes --id parameters and the exclusivity note  
- [ ] Verify --id parameter accepts integer values  
- [ ] Test that --id and --name are properly parsed as separate options  
- [ ] Check help text clarity

Acceptance Criteria:

- [ ] All new parameters defined with correct types  
- [ ] Help text is accurate  
- [ ] Parameters are optional and don't break existing functionality  
- [ ] Parser handles --id and --name correctly

## Stage 4: User Group Command Handlers with Validation

Files: guacalib/cli_handle_usergroup.py

Tasks:

- [ ] Update handle_usergroup_del(), handle_usergroup_exists(), handle_usergroup_modify() to support --id and pass to enhanced DB methods
- [ ] Update handle_usergroup_list() to always show IDs
- [ ] Add syntax-level validation in handlers: ensure that at least one of --name or --id is provided
- [ ] Do not duplicate business-rule validation in handlers; "exactly one" and "positive integer" checks live in Stage 1 resolvers
- [ ] Proper error handling for invalid or non-existent IDs (surfaces resolver/DB errors with clear messages)
- [ ] Pass correct params to DB methods

Verification Steps:

- [ ] Implement Stage 4 tests in tests/test_guacaman.bats  
- [ ] Test everything with both valid and invalid IDs/names  
- [ ] Verify list command shows IDs in output  
- [ ] Test backward compatibility with --name usage

Acceptance Criteria:

- [ ] Works with both name and ID  
- [ ] Validation in handlers for presence of at least one selector  
- [ ] Correct DB calls  
- [ ] Clear error messages for invalid IDs  
- [ ] Backward compatible  
- [ ] Matches existing error formatting

## Stage 5: Integration Tests

Files: tests/test_guacaman.bats (add new tests to existing file)

Tasks:

- [ ] Test usergroup del --id  
- [ ] Test usergroup exists --id for existing/non-existing  
- [ ] Test usergroup modify --id  
- [ ] Test usergroup list includes id field  
- [ ] Test validation errors for both/missing params  
- [ ] Test invalid ID formats (negative/zero via resolvers; non-integer rejected by argparse)  
- [ ] Backward compatibility

Acceptance Criteria:

- CLI commands tested with ID and name  
- Error messages tested  
- Output formats validated with id field  
- Backward compatibility verified

## Stage 6: Final Integration Testing

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

- [ ] Graceful error handling  
- [ ] User-friendly messages  
- [ ] No regressions  
- [ ] All tests pass

Testing Approach

- Primary: integration tests in `tests/test_guacaman.bats` covering both name- and id-based flows and error cases; validate list output format.
- Optional (future): add pytest unit tests for db resolvers and handlers to measure coverage. Numeric coverage targets are out of scope for this feature.

Success Criteria

- Users can specify user groups by ID  
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
- User group not found: id=<ID>/name=<NAME>  
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
    guacdb.delete_existing_usergroup(usergroup_id=args.id)
else:
    guacdb.delete_existing_usergroup(usergroup_name=args.name)
```

Database Method Enhancement Pattern

```python
def delete_existing_usergroup(self, usergroup_name=None, usergroup_id=None):
    usergroup_id = self.resolve_usergroup_id(usergroup_name, usergroup_id)
    # operate on usergroup_id only...
```

Out of Scope

- User ID support  
- Creation with ID  
- Bulk ID operations  
- Conflict discovery  
- Performance optimization
