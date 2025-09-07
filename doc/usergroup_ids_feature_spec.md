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

Stage UG-T: Author Tests First

Target file: tests/test_guacaman.bats

Helper utilities
- [x] Add helper: get_usergroup_id "<group_name>" to parse ID from usergroup list output once IDs are present.

Parser and selector validation tests (CLI-level, mirrors connection tests)
- [x] usergroup exists: requires exactly one selector
  - [x] both --name and --id provided → parser error (exit 2) with helpful text
  - [x] neither provided → parser error (exit 2)
  - [x] invalid ID formats (0, negative) → error message referencing positive integer, non-zero
- [x] usergroup del: same selector validation cases as above
- [x] usergroup modify: same selector validation cases as above when any of --adduser/--rmuser provided
- [x] usergroup modify with no modification flags shows usage/help text (gracefully exits like conn modify)

List output tests (IDs visible)
- [ ] usergroup list includes ID field for every group
- [ ] ID is positive integer for all groups
- [ ] Output structure preserved:
  - [ ] Keep:
    - usergroups:
      - group_name:
        - id:
        - users:
        - connections:
- [ ] Optional: list by specific --id (if we introduce it) prints only that group (match connection/conngroup behavior)

Existence by ID tests
- [ ] Create test groups in setup
- [ ] exists --id <valid_id> returns 0
- [ ] exists --id <nonexistent_id> returns 1
- [ ] exists --id with invalid ID (0, -1) prints validation error and non-zero exit

Delete by ID tests
- [ ] Create a temporary user group
- [ ] del --id <valid_id> succeeds (exit 0)
- [ ] Subsequent exists --name <group_name> returns 1
- [ ] del --id <nonexistent_id> returns non-zero with “not found”/“does not exist” style message

Modify by ID tests
- [ ] Prepare: ensure an existing user userA and a group G
- [ ] modify --id <G_id> --adduser userA succeeds and shows success message consistent with name-based flow
- [ ] usergroup list shows userA under users for group G
- [ ] modify --id <G_id> --rmuser userA succeeds and shows success message
- [ ] Removing non-member should fail with “is not in group” message
- [ ] add/rm with nonexistent user should fail with “does not exist” message
- [ ] add/rm against nonexistent group ID should fail with “not found/does not exist”

Backward compatibility tests
- [ ] All existing name-based operations continue to work as before (exists/del/modify/list)
- [ ] Mixed validation: providing both name and ID is rejected
- [ ] Existing test suites continue to pass (no changes required to previous name-based tests)

Error message parity tests
- [ ] Resolver “not found” messages for usergroups by ID match connection/conngroup style
- [ ] Validation messages for invalid IDs match connection/conngroup style

Stage UG-I: Implement After Tests Are Red

Database layer (guacalib/db.py)
- [ ] Add resolve_usergroup_id(usergroup_name=None, usergroup_id=None)
  - [ ] Exactly one selector validation
  - [ ] Positive integer validation for IDs
  - [ ] Name→ID lookup with clear “not found” message
  - [ ] ID existence verification with clear “not found” message
- [ ] Add get_usergroup_name_by_id(usergroup_id)
- [ ] Update methods to accept either name or ID and internally resolve to ID:
  - [ ] delete_existing_usergroup(usergroup_name=None, usergroup_id=None)
  - [ ] usergroup_exists(usergroup_name=None, usergroup_id=None)
  - [ ] add_user_to_usergroup(username, usergroup_name=None, usergroup_id=None)
  - [ ] remove_user_from_usergroup(username, usergroup_name=None, usergroup_id=None)
- [ ] Update list_usergroups_with_users_and_connections() to include each group’s ID in the return structure

CLI parser (guacalib/cli.py)
- [ ] usergroup exists: add mutually exclusive --name/--id (type=int, positive_int validator where used elsewhere)
- [ ] usergroup del: add mutually exclusive --name/--id
- [ ] usergroup modify: add mutually exclusive --name/--id
- [ ] Optional: usergroup list: add --id (to mirror conn/conngroup list capabilities)
- [ ] Help texts mirror connection/conngroup patterns

Handlers (guacalib/cli_handle_usergroup.py)
- [ ] Use validate_selector(args, "usergroup") for del/exists/modify
- [ ] del: call guacdb.delete_existing_usergroup(usergroup_id=args.id) or by name
- [ ] exists: call guacdb.usergroup_exists(usergroup_id=args.id) or by name
- [ ] modify: support --adduser/--rmuser with either selector (pass *_id to DB)
- [ ] list: display id: field in output (and filter by --id if parser supports it)
- [ ] Use same error handling style/messages as connection/conngroup handlers

Refactor and cleanup
- [ ] Ensure messages in CLI reflect either group name or resolved name when operating by ID
- [ ] Share helper message formatting if needed
- [ ] Keep consistency with AGENTS.md guidelines

Success Criteria

- [ ] All newly added tests pass
- [ ] All existing tests remain green
- [ ] User experience matches connections/conngroups
- [ ] Clear, consistent error messages
- [ ] IDs always displayed in usergroup list

Example Test Snippets (bats, indicative)

Note: These are planning examples; actual tests will be added in tests/test_guacaman.bats.

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

Risks and Edge Cases

- Groups with identical names should not exist (DB uniqueness by entity name); ensure resolver messages are deterministic.
- Large ID values: must gracefully return “not found” without crashing.
- Output parsing in tests should be robust to minor whitespace differences (use grep patterns accordingly).

Implementation Patterns (Reference)

- Use existing resolve_connection_id / resolve_conngroup_id as templates for resolve_usergroup_id.
- Use validate_selector(args, "usergroup") uniformly in handlers.
- Keep list output structure aligned with existing list handlers.

Definition of Done

- [ ] Tests for usergroup IDs are merged and initially failing on main
- [ ] Database layer and CLI code implemented to make tests pass
- [ ] Code reviewed for consistency with AGENTS.md (types, clarity, errors)
- [ ] Documentation updated (this file) and README if CLI flags surface to users
