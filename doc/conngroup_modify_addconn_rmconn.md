# Connection Group Modify: Add/Remove Connections Feature Plan

## Overview

Extend `guacaman conngroup modify` command to support adding and removing connections to/from connection groups using `--addconn-by-name`/`--addconn-by-id` and `--rmconn-by-name`/`--rmconn-by-id` parameters. The target connection group can be specified by either `--name` or `--id`.

**Implementation Notes**: This feature requires creating new database layer methods from scratch (no existing connection-group membership management exists in the codebase) and implementing atomic transactions for batch operations.

## Scope

- Add `--addconn-by-name <connection_name>` and `--addconn-by-id <connection_id>` parameter to add connections to groups
- Add `--rmconn-by-name <connection_name>` and `--rmconn-by-id <connection_id>` parameter to remove connections from groups  
- Support both `--name` and `--id` for target connection group selection
- Validate connection existence before add/remove operations
- Handle duplicate add attempts and removal of non-members gracefully
- Comprehensive test coverage using TDD approach

## Requirements

### 1. CLI Parameter Changes

#### 1.1 New Parameters
- `--addconn-by-name <connection_name>`: Add specified connection by name to the target group
- `--rmconn-by-name <connection_name>`: Remove specified connection by name from the target group
- `--addconn-by-id <connection_id>`: Add connection by ID to the target group
- `--rmconn-by-id <connection_id>`: Remove connection by ID from the target group
- All parameters can be used multiple times in a single command
- Parameters are mutually exclusive between add/remove operations (cannot add and remove in same command)
- `--addconn-by-name` and `--addconn-by-id` can be used together in the same command
- `--rmconn-by-name` and `--rmconn-by-id` can be used together in the same command

#### 1.2 Command Syntax
```bash
# Add connection(s) to group by name (mixed name and ID support)
guacaman conngroup modify --name <group_name> --addconn-by-name <conn_name> [--addconn-by-name <conn_name2> ...] [--addconn-by-id <conn_id> ...]

# Add connection(s) to group by ID (mixed name and ID support)  
guacaman conngroup modify --id <group_id> --addconn-by-name <conn_name> [--addconn-by-name <conn_name2> ...] [--addconn-by-id <conn_id> ...]

# Remove connection(s) from group by name (mixed name and ID support)
guacaman conngroup modify --name <group_name> --rmconn-by-name <conn_name> [--rmconn-by-name <conn_name2> ...] [--rmconn-by-id <conn_id> ...]

# Remove connection(s) from group by ID (mixed name and ID support)
guacaman conngroup modify --id <group_id> --rmconn-by-name <conn_name> [--rmconn-by-name <conn_name2> ...] [--rmconn-by-id <conn_id> ...]

# Examples with mixed name/ID usage
guacaman conngroup modify --name mygroup --addconn-by-name conn1 --addconn-by-id 123 --addconn-by-name conn2
guacaman conngroup modify --id 456 --rmconn-by-name conn3 --rmconn-by-id 789 --rmconn-by-id 101
```

### 2. Business Rules

2.1 Target Group Selection
- Exactly one of `--name` or `--id` must be provided for the target group
- Group must exist in the database

2.2 Connection Validation
- All specified connections are validated to exist before any database operations begin
- Connection names are resolved to IDs for database operations, ID values are validated for existence
- Mixed usage of names and IDs is supported within the same operation
- Validation prevents partial failures by checking all connections upfront

2.3 Operation Rules
- Cannot add a connection that's already a member of the target group
- Cannot remove a connection that's not a member of the target group
- Operations are atomic - either all succeed or all fail (implemented using database transactions with rollback on failure)
- `--addconn-*` and `--rmconn-*` cannot be used in the same command

## TDD Implementation Stages

### Stage 1: Write Failing Tests (Red Phase)

**Goal**: Create comprehensive test suite that validates all requirements will fail initially
**Files**: `tests/test_conngroup_addconn_rmconn.bats` (new file)
**Success Criteria**: All tests written and confirmed to fail
**Integration**: File must be added to `tests/run_tests.sh` after connection group tests

**Test Cases to Write**:
```bash
# CLI Integration Tests (Full workflow)
@test "conngroup modify help shows new parameters - should fail initially"
@test "--addconn-by-name parameter accepts multiple values - should fail initially"
@test "--rmconn-by-name parameter accepts multiple values - should fail initially"
@test "--addconn-by-id parameter accepts multiple values - should fail initially"
@test "--rmconn-by-id parameter accepts multiple values - should fail initially"
@test "--addconn-by-name and --rmconn-by-name are mutually exclusive - should fail initially"
@test "--addconn-by-id and --rmconn-by-id are mutually exclusive - should fail initially"

# Add Connection Tests (Name and ID)
@test "add connections to group with various inputs (single, multiple, mixed name/ID) - should fail initially"
@test "fail to add non-existent connection - should fail initially"
@test "fail to add to non-existent group - should fail initially"
@test "fail to add duplicate connection to group - should fail initially"

# Remove Connection Tests (Name and ID)
@test "remove connections from group with various inputs (single, multiple, mixed name/ID) - should fail initially"
@test "fail to remove non-existent connection - should fail initially"
@test "fail to remove from non-existent group - should fail initially"
@test "fail to remove non-member connection - should fail initially"

# Validation and Error Tests
@test "reject both --addconn-by-name and --rmconn-by-name in same command - should fail initially"
@test "reject both --addconn-by-id and --rmconn-by-id in same command - should fail initially"
@test "reject --addconn-by-name and --rmconn-by-id in same command - should fail initially"
@test "reject --addconn-by-id and --rmconn-by-name in same command - should fail initially"
@test "reject mixed add/remove operations - should fail initially"
@test "reject non-existent target group - should fail initially"
@test "reject non-existent connection - should fail initially"
@test "reject adding already-member connection - should fail initially"
@test "reject removing non-member connection - should fail initially"

# Output Format Tests
@test "success message format for single connection - should fail initially"
@test "success message format for multiple connections - should fail initially"
@test "success message format for mixed name/ID operations - should fail initially"
@test "error message format for validation failures - should fail initially"
@test "exit codes for all scenarios - should fail initially"
```

**Tasks**:
- [ ] Write all test cases above
- [ ] Add `test_conngroup_addconn_rmconn.bats` to `tests/run_tests.sh` after connection group tests
- [ ] Run tests - confirm ALL fail (Red)
- [ ] Document any test failures for reference

### Stage 2: Implement Database Operations (Green Phase - Part 1)

**Goal**: Implement core database methods to make database-related tests pass
**Files**: `guacalib/db.py`
**Success Criteria**: Database operation tests pass

**Background**: No existing database methods exist for managing connection-group memberships. These core methods need to be created from scratch and will interact with the `guacamole_connection.parent_id` field to assign connections to connection groups.

**Implementation Tasks**:
- [ ] Verify resolver dependencies exist (`resolve_connection_id()`, `resolve_conngroup_id()`)
- [ ] Add `add_connection_to_group(connection_name_or_id, group_name=None, group_id=None)` method - handles adding single connection to a group using parent_id field
- [ ] Add `remove_connection_from_group(connection_name_or_id, group_name=None, group_id=None)` method - handles removing single connection from a group by setting parent_id to NULL
- [ ] Add `get_group_connections(group_name=None, group_id=None)` helper method - list connections currently in a specific group
- [ ] Add `is_connection_in_group(connection_name_or_id, group_name=None, group_id=None)` validation method - check if connection is already a member
- [ ] Add `resolve_connection_name_or_id(connection_name_or_id)` helper to handle both names and IDs - integrates with existing resolvers
- [ ] Implement transaction rollback on any operation failure to ensure atomicity
- [ ] Run tests - database operation tests should PASS (Green)
- [ ] Refactor database code if needed

### Stage 3: Implement CLI Parser and Handler (Green Phase - Part 2)

**Goal**: Add CLI parameters and handler logic to make remaining tests pass
**Files**: `guacalib/cli_handle_conngroup.py`
**Success Criteria**: All tests pass

**Implementation Tasks**:
- [ ] Add `--addconn-by-name` parameter to conngroup modify subparser
- [ ] Add `--rmconn-by-name` parameter to conngroup modify subparser  
- [ ] Add `--addconn-by-id` parameter to conngroup modify subparser
- [ ] Add `--rmconn-by-id` parameter to conngroup modify subparser
- [ ] Support multiple values for all parameters (nargs='*')
- [ ] Add mutual exclusion group between add operations and remove operations
- [ ] Update help text to clearly explain usage and restrictions
- [ ] Update `handle_conngroup_command()` modify branch to handle new parameters
- [ ] Add validation for parameter combinations and business rules
- [ ] Implement batch processing for multiple connections (mixed names and IDs)
- [ ] Ensure proper error handling and user-friendly messages
- [ ] Run all tests - they should PASS (Green)
- [ ] Refactor code for clarity

### Stage 4: Documentation and Regression Testing (Final Phase)

**Goal**: Complete documentation and ensure no regressions
**Files**: `README.md`, existing test suite
**Success Criteria**: Documentation updated, all existing tests still pass

**Tasks**:
- [ ] Update CLI usage examples in README
- [ ] Add section on connection group membership management
- [ ] Document all new parameters and their restrictions
- [ ] Add troubleshooting guide for common scenarios
- [ ] Run complete test suite via `make tests` to ensure no regressions
- [ ] Test new functionality with realistic data sets
- [ ] Performance testing with large groups and many connections
- [ ] Code review and security validation



## Error Messages and Exit Codes

### Standard Exit Codes
- `0`: Success (operation completed)
- `1`: Business rule violation or validation error
- `2`: Command line argument error
- `3`: Database connection or system error

### Error Message Specifications

#### Target Group Errors
- `Connection group not found: name=<GROUP_NAME>/id=<GROUP_ID>`
- `Exactly one of --name or --id must be provided for target group`

#### Connection Errors  
- `Connection not found: <CONNECTION_NAME_OR_ID>`
- `Connection '<CONNECTION_NAME_OR_ID>' is already a member of group '<GROUP_NAME>'`
- `Connection '<CONNECTION_NAME_OR_ID>' is not a member of group '<GROUP_NAME>'`

#### Parameter Errors
- `Cannot use any --addconn-* and --rmconn-* in the same command`
- `At least one connection must be specified with --addconn-* or --rmconn-*`
- `No connections specified for operation`

#### Success Messages
- `Added connection '<CONNECTION_NAME_OR_ID>' to group '<GROUP_NAME>'`
- `Added N connections to group '<GROUP_NAME>': conn1, conn2, ...`
- `Removed connection '<CONNECTION_NAME_OR_ID>' from group '<GROUP_NAME>'`
- `Removed N connections from group '<GROUP_NAME>': conn1, conn2, ...`

## Implementation Benefits

- ✅ Atomic operations prevent partial state changes
- ✅ Comprehensive validation prevents data inconsistencies  
- ✅ Batch operations improve efficiency for multiple connections
- ✅ Clear error messages improve user experience
- ✅ Backward compatibility maintained
- ✅ Consistent with existing CLI patterns
- ✅ Full test coverage ensures reliability

## Out of Scope

- Wildcard or pattern-based connection selection
- Moving connections between groups (remove from one, add to another)
- Bulk import/export of group memberships
- Permission validation for group membership changes
- Audit logging of membership changes

## Success Criteria

- Users can add/remove connections to/from groups using simple CLI commands
- All operations are atomic and validated
- Clear feedback provided for success and failure cases
- Existing functionality remains unchanged
- Comprehensive test coverage ensures reliability
- Documentation is complete and accurate
