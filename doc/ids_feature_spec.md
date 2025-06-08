# Complete Specification: --id Implementation for Connections and Connection Groups

# Overview

Add --id parameter support to uniquely identify connections and connection groups by their database IDs, resolving naming ambiguity in hierarchical
structures.


# Scope

 • Connection commands: delete, exists, modify
 • Connection group commands: delete, exists, modify
 • Enhanced list commands with --show-ids flag
 • Comprehensive test coverage


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

1.2.2 Enhanced list commands

guacaman conn list --show-ids
guacaman conngroup list --show-ids


2. Database Layer Requirements

2.1 New Methods Needed


def get_connection_by_id(self, connection_id) -> dict
def get_connection_group_by_id(self, group_id) -> dict
def connection_id_exists(self, connection_id) -> bool
def connection_group_id_exists(self, group_id) -> bool


2.2 Modified Methods

Update existing methods to accept optional connection_id or group_id:


def delete_existing_connection(self, connection_name=None, connection_id=None)
def modify_connection(self, connection_name=None, connection_id=None, ...)
def delete_connection_group(self, group_name=None, group_id=None)
def modify_connection_group_parent(self, group_name=None, group_id=None, ...)


3. Validation Rules

 • Exactly one of --name or --id must be provided
 • IDs must be positive integers
 • IDs must exist in database
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


5. Discovery Mechanism

When --name matches multiple items, provide helpful suggestions:


$ guacaman conn delete --name server01
Error: Multiple connections found with name 'server01':
  ID: 123, Path: ROOT/production/server01
  ID: 456, Path: ROOT/development/server01
Use --id to specify which connection, or use 'guacaman conn list --show-ids' to see all IDs.



# Implementation Plan

## Stage 1: Database Layer Foundation

Files: guacalib/db.py

Tasks:

 • [ ] Add get_connection_by_id(self, connection_id) method
 • [ ] Add get_connection_group_by_id(self, group_id) method
 • [ ] Add connection_id_exists(self, connection_id) method
 • [ ] Add connection_group_id_exists(self, group_id) method
 • [ ] Add ID validation helper method _validate_positive_integer(self, value, name)

Acceptance Criteria:

 • All new methods return expected data types
 • ID validation rejects negative numbers, zero, non-integers
 • Methods handle non-existent IDs gracefully
 • Database errors are properly caught and re-raised

## Stage 2: Database Layer - Modify Existing Methods

Files: guacalib/db.py

Tasks:

 • [ ] Update delete_existing_connection() to accept connection_id parameter
 • [ ] Update modify_connection() to accept connection_id parameter
 • [ ] Update delete_connection_group() to accept group_id parameter
 • [ ] Update modify_connection_group_parent() to accept group_id parameter
 • [ ] Add parameter validation: exactly one of name/id must be provided

Acceptance Criteria:

 • Methods work with both name and ID parameters
 • Proper validation ensures only one identifier is provided
 • Backward compatibility maintained for name-only calls
 • Clear error messages for invalid parameter combinations

## Stage 3: Enhanced List Commands

Files: guacalib/db.py

Tasks:

 • [ ] Update list_connections_with_conngroups_and_parents() to optionally include IDs
 • [ ] Update list_connection_groups() to optionally include IDs
 • [ ] Modify return formats to include ID information when requested
 • [ ] Ensure ID field is added to existing YAML structure

Acceptance Criteria:

 • List methods accept include_ids=False parameter
 • When include_ids=True, output includes id field in existing structure
 • Existing functionality unchanged when include_ids=False
 • ID information is accurate and matches database

## Stage 4: CLI Argument Parser Updates

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

## Stage 5: Connection Command Handlers

Files: guacalib/cli_handle_conn.py

Tasks:

 • [ ] Update handle_conn_delete() to support --id parameter
 • [ ] Update handle_conn_exists() to support --id parameter
 • [ ] Update handle_conn_modify() to support --id parameter
 • [ ] Update handle_conn_list() to support --show-ids flag
 • [ ] Add validation: ensure exactly one of --name or --id is provided
 • [ ] Add ID format validation and error handling
 • [ ] Add discovery helper: when name matches multiple items, suggest using --id

Acceptance Criteria:

 • Commands work correctly with both --name and --id
 • Proper error messages for invalid IDs or missing parameters
 • List command shows IDs when --show-ids flag is used
 • Discovery mechanism helps users when naming conflicts occur
 • Backward compatibility maintained

## Stage 6: Connection Group Command Handlers

Files: guacalib/cli_handle_conngroup.py

Tasks:

 • [ ] Update handle_conngroup_command() for delete subcommand with --id
 • [ ] Update handle_conngroup_command() for exists subcommand with --id
 • [ ] Update handle_conngroup_command() for modify subcommand with --id
 • [ ] Update list subcommand to support --show-ids flag
 • [ ] Add validation: ensure exactly one of --name or --id is provided
 • [ ] Add ID format validation and error handling
 • [ ] Add discovery helper: when name matches multiple items, suggest using --id

Acceptance Criteria:

 • Commands work correctly with both --name and --id
 • Proper error messages for invalid IDs or missing parameters
 • List command shows IDs when --show-ids flag is used
 • Discovery mechanism helps users when naming conflicts occur
 • Backward compatibility maintained

## Stage 7: Unit Tests - Database Layer

Files: tests/test_db_id_support.py (new file)

Tasks:

 • [ ] Test get_connection_by_id() with valid IDs
 • [ ] Test get_connection_by_id() with non-existent IDs
 • [ ] Test get_connection_group_by_id() with valid IDs
 • [ ] Test get_connection_group_by_id() with non-existent IDs
 • [ ] Test connection_id_exists() with existing and non-existing IDs
 • [ ] Test connection_group_id_exists() with existing and non-existing IDs
 • [ ] Test _validate_positive_integer() with valid and invalid inputs
 • [ ] Test modified methods with both name and ID parameters
 • [ ] Test parameter validation (both provided, neither provided)
 • [ ] Test list methods with include_ids parameter

Acceptance Criteria:

 • All database methods tested with valid and invalid inputs
 • Edge cases covered (None, negative numbers, strings, etc.)
 • Database connection mocking works correctly
 • Tests are isolated and don't depend on external database state

## Stage 8: Integration Tests - CLI Commands

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
 • [ ] Test discovery mechanism when multiple items have same name

Acceptance Criteria:

 • All CLI commands tested with valid and invalid inputs
 • Error messages are tested for correctness
 • Output formats are validated with ID fields present
 • Backward compatibility is verified
 • Tests use proper test database setup/teardown
 • Discovery mechanism provides helpful suggestions

## Stage 9: Error Handling Tests

Files: tests/test_guacaman.bats (add error handling tests)

Tasks:

 • [ ] Test invalid ID formats (negative, zero, non-integer, string)
 • [ ] Test non-existent IDs return appropriate error messages
 • [ ] Test parameter validation errors are clear and helpful
 • [ ] Test error message consistency across all commands
 • [ ] Test that error messages suggest correct usage

Acceptance Criteria:

 • All error conditions produce appropriate error messages
 • Error messages are user-friendly and actionable
 • Error handling doesn't leak sensitive information
 • Consistent error message format across commands

## Stage 10: Integration Testing & Final Validation

Files: All modified files, existing test suite

Tasks:

 • [ ] Run full existing test suite to ensure no regressions
 • [ ] Test all commands with valid IDs in realistic scenarios
 • [ ] Test all commands with invalid IDs (non-existent, negative, non-integer)
 • [ ] Test parameter validation (both name and ID provided, neither provided)
 • [ ] Test backward compatibility (existing scripts still work)
 • [ ] Test list commands with and without --show-ids
 • [ ] Verify error messages are clear and helpful
 • [ ] Verify ID operations don't significantly impact response time
 • [ ] Test with realistic dataset sizes (100-1000 connections)

Acceptance Criteria:

 • All error conditions handled gracefully
 • Error messages are user-friendly and actionable
 • No regression in existing functionality
 • Performance impact is minimal (< 10% slower than name-based operations)
 • All tests pass consistently

# Stage 11: Documentation and Examples

Files: README.md, help text, inline documentation

Tasks:

 • [ ] Update CLI help text for all modified commands
 • [ ] Add examples of ID-based operations to README
 • [ ] Document the --show-ids flag usage
 • [ ] Add troubleshooting section for ID-related issues
 • [ ] Update API documentation for new database methods
 • [ ] Add migration guide for users with naming conflicts
 • [ ] Document when to use --id vs --name

Acceptance Criteria:

 • Documentation is clear and comprehensive
 • Examples are practical and tested
 • Help text is consistent across all commands
 • Migration path is well-documented
 • Users understand when and how to use ID-based operations


Test Coverage Requirements

Unit Test Coverage

 • Database Layer: 100% coverage of new methods, 95% coverage of modified methods
 • CLI Handlers: 90% coverage of new ID-handling code paths
 • Validation Logic: 100% coverage of all validation scenarios

Integration Test Coverage

 • Happy Path: All commands work with valid IDs
 • Error Cases: All error conditions produce correct messages
 • Edge Cases: Boundary conditions (ID=1, very large IDs, etc.)
 • Backward Compatibility: All existing functionality unchanged
 • Discovery Mechanism: Helpful suggestions when naming conflicts occur

Performance Test Requirements

 • ID-based operations should be no more than 10% slower than name-based
 • List commands with --show-ids should be no more than 20% slower
 • Memory usage should not increase significantly


Success Criteria

 • Users can identify connections/groups by ID when names are ambiguous
 • All existing functionality continues to work unchanged
 • Clear error messages guide users when they make mistakes
 • List commands provide easy way to discover IDs
 • Discovery mechanism helps users resolve naming conflicts
 • Implementation is robust and handles edge cases
 • Test coverage meets specified requirements
 • Performance impact is within acceptable limits


Out of Scope

 • User and usergroup ID support (future enhancement)
 • Connection creation with ID specification
 • Bulk operations with ID lists
 • ID-based search/filtering beyond basic existence checks
 • GUI integration or web interface changes

