# Streamlined Specification: --id Implementation for User Groups

# Overview

Add --id parameter support to uniquely identify user groups by their database IDs, following the proven patterns already implemented for connections and connection groups.

# Scope

- User group commands: del, exists, modify
- Enhanced list commands (always show IDs)
- Basic test coverage

# Requirements

## Stage 1: Database Layer + Handler Validation (Combined)

Files: guacalib/db.py, guacalib/cli_handle_usergroup.py

### Database Tasks:

- [ ] Add `resolve_usergroup_id(usergroup_name=None, usergroup_id=None)` resolver following existing patterns
- [ ] Update existing methods to accept optional `*_id` arguments:
  - `delete_existing_usergroup()`
  - `usergroup_exists()`
  - `add_user_to_usergroup()`
  - `remove_user_from_usergroup()`
- [ ] Update `list_usergroups_with_users_and_connections()` to include `id` in return structure
- [ ] Add `get_usergroup_name_by_id()` helper method

### Handler Tasks:

- [ ] Update handlers to use `validate_selector()` function (already exists in cli.py)
- [ ] Update handlers to support --id parameter and pass to enhanced DB methods
- [ ] Update list handler to display IDs in output
- [ ] Use existing error handling patterns

### Validation Strategy:

- CLI: Use existing `validate_selector(args, "usergroup")` function
- Database: Centralize validation in `resolve_usergroup_id()` like other resolvers
- Follow exact same patterns as connection/conngroup implementations

## Stage 2: CLI Argument Parser Updates

Files: guacalib/cli.py

Tasks:

- [ ] Add --id parameter to usergroup del, exists, modify subcommands
- [ ] Use mutually exclusive groups like existing connection commands
- [ ] Copy help text patterns from connection commands

## Stage 3: Integration Tests

Files: tests/test_guacaman.bats

Tasks:

- [ ] Copy and adapt existing connection ID tests for usergroups
- [ ] Test usergroup del/exists/modify with --id
- [ ] Test list command includes id field
- [ ] Test validation errors and backward compatibility

## Implementation Patterns

### CLI Integration (copy from connections):
```python
# Validate exactly one selector provided
from .cli import validate_selector
validate_selector(args, "usergroup")

if hasattr(args, 'id') and args.id is not None:
    guacdb.delete_existing_usergroup(usergroup_id=args.id)
else:
    guacdb.delete_existing_usergroup(usergroup_name=args.name)
```

### Database Method Enhancement (copy from connections):
```python
def delete_existing_usergroup(self, usergroup_name=None, usergroup_id=None):
    resolved_usergroup_id = self.resolve_usergroup_id(usergroup_name, usergroup_id)
    # operate on resolved_usergroup_id only...
```

### Resolver Implementation (copy from connections):
```python
def resolve_usergroup_id(self, usergroup_name=None, usergroup_id=None):
    # Validate exactly one parameter provided
    if (usergroup_name is None) == (usergroup_id is None):
        raise ValueError("Exactly one of usergroup_name or usergroup_id must be provided")
    
    # If ID provided, validate and return it
    if usergroup_id is not None:
        if usergroup_id <= 0:
            raise ValueError("Usergroup ID must be a positive integer greater than 0")
        # Verify the usergroup exists and return ID
        # ... implementation follows connection pattern
    
    # If name provided, resolve to ID
    # ... implementation follows connection pattern
```

## Success Criteria

- Users can specify user groups by ID using same syntax as connections
- All existing functionality unchanged
- Clear error messages matching existing patterns
- List commands show IDs in consistent format
- Robust error handling following existing patterns

## Benefits of Streamlined Approach

- ✅ Reuses proven patterns from connections/conngroups
- ✅ Leverages existing `validate_selector()` function
- ✅ Minimal code duplication
- ✅ Consistent user experience across all entity types
- ✅ Faster implementation with lower risk
- ✅ Easier testing by copying existing test patterns
