# Complete Specification: --id Implementation for Connections and Connection Groups

# Overview

Add --id parameter support to uniquely identify connections and connection groups by their database IDs, resolving naming ambiguity in hierarchical structures.

# Scope

 • Connection commands: delete, exists, modify
 • Connection group commands: delete, exists, modify
 • Enhanced list commands with --show-ids flag
 • Basic test coverage

# Requirements

1. CLI Parameter Changes

1.1 New Parameters

 • Add --id parameter to specific subcommands
 • Add --show-ids flag to list commands
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

guacaman conn list --show-ids
guacaman conngroup list --show-ids

2. Database Layer Requirements

2.1 Enhanced Existing Methods (Backward Compatible)

Extend existing methods to accept optional ID parameters while maintaining full backward compatibility:

def delete_existing_connection(self, connection_name=None, connection_id=None)
def delete_connection_group(self, group_name=None, group_id=None)
def modify_connection(self, connection_name=None, connection_id=None, param_name, param_value)
def modify_connection_group_parent(self, group_name=None, group_id=None, new_parent_name)
def connection_exists(self, connection_name=None, connection_id=None) -> bool
def connection_group_exists(self, group_name=None, group_id=None) -> bool

2.2 New Helper Methods (Internal Use)

Add private helper methods for ID resolution:

def _get_connection_id_by_name(self, connection_name) -> int
def _get_connection_group_id_by_name(self, group_name) -> int
def _get_connection_by_id(self, connection_id) -> dict
def _get_connection_group_by_id(self, group_id) -> dict

2.3 Enhanced List Methods

Update list methods to optionally include IDs:
def list_connections_with_conngroups_and_parents(self, include_ids=False)
def list_connection_groups(self, include_ids=False)

3. Validation Rules

 • Exactly one of --name or --id must be provided (validated in CLI handlers)
 • IDs must be positive integers (validated in CLI handlers)
 • IDs must exist in database (validated by database methods)
 • Clear error messages for invalid/non-existent IDs

4. Output Format Changes

When --show-ids flag is used, add id field to existing structure:

connections:
  testconn1:
    id: 123
    type: vnc
    hostname: 192.168.1.100
    port: 5901
    parent: production
    groups:
      - developers
    permissions:
      - user1

conngroups:
  production:
    id: 45
    parent: ROOT
    connections:
      - server01



# Implementation Plan

## Stage 1: Database Layer - Enhanced Existing Methods

Files: guacalib/db.py

Tasks:

 • [ ] Add private helper methods: _get_connection_id_by_name(), _get_connection_group_id_by_name()
 • [ ] Add private helper methods: _get_connection_by_id(), _get_connection_group_by_id()
 • [ ] Enhance delete_existing_connection() to accept optional connection_id parameter
 • [ ] Enhance delete_connection_group() to accept optional group_id parameter
 • [ ] Enhance modify_connection() to accept optional connection_id parameter
 • [ ] Enhance modify_connection_group_parent() to accept optional group_id parameter
 • [ ] Enhance connection_exists() to accept optional connection_id parameter
 • [ ] Enhance connection_group_exists() to accept optional group_id parameter
 • [ ] Add validation logic: exactly one of name or ID must be provided
 • [ ] Ensure all enhanced methods maintain backward compatibility

Acceptance Criteria:

 • All enhanced methods work with both name and ID parameters
 • Validation ensures exactly one of name or ID is provided
 • Methods handle non-existent IDs gracefully with clear error messages
 • Database errors are properly caught and re-raised
 • Existing method calls continue to work unchanged
 • No code duplication between name and ID handling paths

## Stage 2: Enhanced List Commands

Files: guacalib/db.py

Tasks:

 • [ ] Update list_connections_with_conngroups_and_parents() to accept include_ids=False parameter
 • [ ] Update list_connection_groups() to accept include_ids=False parameter
 • [ ] Modify return formats to include ID information when requested
 • [ ] Ensure ID field is added to existing YAML structure

Acceptance Criteria:

 • List methods accept include_ids=False parameter
 • When include_ids=True, output includes id field in existing structure
 • Existing functionality unchanged when include_ids=False
 • ID information is accurate and matches database

## Stage 3: CLI Argument Parser Updates

Files: guacalib/cli.py

Tasks:

 • [ ] Add --id parameter to conn delete subcommand
 • [ ] Add --id parameter to conn exists subcommand
 • [ ] Add --id parameter to conn modify subcommand
 • [ ] Add --id parameter to conngroup delete subcommand
 • [ ] Add --id parameter to conngroup exists subcommand
 • [ ] Add --id parameter to conngroup modify subcommand
 • [ ] Add --show-ids flag to conn list subcommand
 • [ ] Add --show-ids flag to conngroup list subcommand

Acceptance Criteria:

 • All new parameters are properly defined with correct types
 • Help text is clear and informative
 • Parameters are optional and don't break existing functionality

## Stage 4: Connection Command Handlers with Validation

Files: guacalib/cli_handle_conn.py

Tasks:

 • [ ] Update handle_conn_delete() to support --id parameter and pass to enhanced method
 • [ ] Update handle_conn_exists() to support --id parameter and pass to enhanced method
 • [ ] Update handle_conn_modify() to support --id parameter and pass to enhanced method
 • [ ] Update handle_conn_list() to support --show-ids flag
 • [ ] Add validation in each handler: ensure exactly one of --name or --id is provided
 • [ ] Add ID format validation (positive integer) in handlers
 • [ ] Add clear error handling for invalid/non-existent IDs
 • [ ] Pass appropriate parameters to enhanced database methods

Acceptance Criteria:

 • Commands work correctly with both --name and --id
 • Validation logic clearly implemented in command handlers
 • Handlers call enhanced database methods with correct parameters
 • Proper error messages for invalid IDs or missing parameters
 • List command shows IDs when --show-ids flag is used
 • Backward compatibility maintained
 • Error messages follow existing format (using sys.exit(1))

## Stage 5: Connection Group Command Handlers with Validation

Files: guacalib/cli_handle_conngroup.py

Tasks:

 • [ ] Update handle_conngroup_command() for delete subcommand with --id and pass to enhanced method
 • [ ] Update handle_conngroup_command() for exists subcommand with --id and pass to enhanced method
 • [ ] Update handle_conngroup_command() for modify subcommand with --id and pass to enhanced method
 • [ ] Update list subcommand to support --show-ids flag
 • [ ] Add validation in each handler: ensure exactly one of --name or --id is provided
 • [ ] Add ID format validation (positive integer) in handlers
 • [ ] Add clear error handling for invalid/non-existent IDs
 • [ ] Pass appropriate parameters to enhanced database methods

Acceptance Criteria:

 • Commands work correctly with both --name and --id
 • Validation logic clearly implemented in command handlers
 • Handlers call enhanced database methods with correct parameters
 • Proper error messages for invalid IDs or missing parameters
 • List command shows IDs when --show-ids flag is used
 • Backward compatibility maintained
 • Error messages follow existing format (using sys.exit(1))

## Stage 6: Integration Tests

Files: tests/test_guacaman.bats (add new tests to existing file)

Tasks:

 • [ ] Test conn delete --id with valid connection ID
 • [ ] Test conn delete --id with non-existent connection ID
 • [ ] Test conn exists --id with existing and non-existing IDs
 • [ ] Test conn modify --id with valid connection ID
 • [ ] Test conn list --show-ids output format includes ID field
 • [ ] Test conngroup delete --id with valid group ID
 • [ ] Test conngroup delete --id with non-existent group ID
 • [ ] Test conngroup exists --id with existing and non-existing IDs
 • [ ] Test conngroup modify --id with valid group ID
 • [ ] Test conngroup list --show-ids output format includes ID field
 • [ ] Test parameter validation errors (both --name and --id provided)
 • [ ] Test parameter validation errors (neither --name nor --id provided)
 • [ ] Test invalid ID formats (negative, zero, non-integer)
 • [ ] Test backward compatibility (existing commands still work)

Acceptance Criteria:

 • All CLI commands tested with valid and invalid inputs
 • Error messages are tested for correctness
 • Output formats are validated with ID fields present
 • Backward compatibility is verified
 • Tests use proper test database setup/teardown

## Stage 7: Final Integration Testing

Files: All modified files, existing test suite

Tasks:

 • [ ] Run full existing test suite to ensure no regressions
 • [ ] Test all commands with valid IDs in realistic scenarios
 • [ ] Test all commands with invalid IDs (non-existent, negative, non-integer)
 • [ ] Test parameter validation (both name and ID provided, neither provided)
 • [ ] Test backward compatibility (existing scripts still work)
 • [ ] Test list commands with and without --show-ids
 • [ ] Verify error messages are clear and helpful

Acceptance Criteria:

 • All error conditions handled gracefully
 • Error messages are user-friendly and actionable
 • No regression in existing functionality
 • All tests pass consistently

Test Coverage Requirements

 • Database Layer: 80% coverage of new methods
 • CLI Handlers: 85% coverage of new ID-handling code paths
 • Integration Tests: Cover all major use cases and error conditions

Success Criteria

 • Users can identify connections/groups by ID when names are ambiguous
 • All existing functionality continues to work unchanged
 • Clear error messages guide users when they make mistakes
 • List commands provide easy way to discover IDs
 • Implementation is robust and handles edge cases

## Implementation Benefits

This approach provides several key advantages:

- ✅ **No code duplication** - Single implementation path for each operation
- ✅ **Single code path** to maintain - Bug fixes apply to both name and ID operations
- ✅ **Backward compatibility** - All existing method calls continue to work unchanged
- ✅ **Consistent behavior** - Name and ID operations use identical logic
- ✅ **Reduced complexity** - Much less boilerplate code than separate methods
- ✅ **Easier testing** - Single code path reduces test complexity
- ✅ **Future-proof** - Easy to add additional identification methods later

## CLI Integration Pattern

CLI handlers will use simple parameter passing:

```python
# Example CLI handler pattern
if args.id:
    guacdb.delete_existing_connection(connection_id=args.id)
else:
    guacdb.delete_existing_connection(connection_name=args.name)
```

## Database Method Enhancement Pattern

```python
# Example enhanced method signature
def delete_existing_connection(self, connection_name=None, connection_id=None):
    # Validation: exactly one must be provided
    if not connection_name and not connection_id:
        raise ValueError("Either connection_name or connection_id must be provided")
    if connection_name and connection_id:
        raise ValueError("Cannot specify both connection_name and connection_id")
    
    # Get connection_id if name was provided
    if connection_name:
        connection_id = self._get_connection_id_by_name(connection_name)
    
    # Rest of method uses connection_id (existing logic unchanged)
```

Out of Scope

 • User and usergroup ID support (future enhancement)
 • Connection creation with ID specification
 • Bulk operations with ID lists
 • Discovery mechanism for naming conflicts (can be added later)
 • Performance optimization beyond basic functionality

