# Connection Group Permission Management Feature

## Overview

Extend `guacaman conngroup modify` command to support `--permit` and `--deny` parameters for managing user permissions on connection groups, similar to the existing `conn modify --permit/--deny <user>` functionality.

## Current State Analysis

Based on the existing codebase:

1. **Connection Permissions**: Use `guacamole_connection_permission` table with `entity_id`, `connection_id`, and `permission` columns
2. **Database Methods**: `grant_connection_permission_to_user()` and `revoke_connection_permission_from_user()` exist for individual connections
3. **CLI Pattern**: Connection modify supports `--permit USERNAME` and `--deny USERNAME` parameters
4. **Connection Group Support**: No existing permission management for connection groups

## Proposed Implementation

### User Interface

Add `--permit USERNAME` and `--deny USERNAME` parameters to `guacaman conngroup modify` command:

```bash
# Grant permission to user for connection group
guacaman conngroup modify --name <group_name> --permit <username>
guacaman conngroup modify --id <group_id> --permit <username>

# Revoke permission from user for connection group
guacaman conngroup modify --name <group_name> --deny <username>
guacaman conngroup modify --id <group_id> --deny <username>
```

### Database Schema

Guacamole uses the same `guacamole_connection_permission` table for both individual connections and connection groups. The `connection_id` field can reference:
- Individual connections (`guacamole_connection.connection_id`)
- Connection groups (`guacamole_connection_group.connection_id`)

## TDD-Based Implementation Plan

### Stage 1: Write Failing Tests First

**Objective**: Create comprehensive tests that will initially fail, driving the implementation.

- [x] **Stage 1.1**: Create test file `tests/test_conngroup_permit_deny.bats`
  - [x] Setup/teardown functions for test users and connection groups
  - [x] Test both name-based and ID-based operations

- [x] **Stage 1.2**: Write permission granting test cases
  - [x] Test `guacaman conngroup modify --name <group> --permit <user>` should succeed
  - [x] Test `guacaman conngroup modify --id <group_id> --permit <user>` should succeed
  - [x] Single user action should be allowed only: `--permit user1 --permit user2` should fail with appropriate error
  - [x] Test non-existent user with `--permit` should fail with appropriate error
  - [x] Test non-existent group with `--permit` should fail with appropriate error
  - [x] Test duplicate permission grant should handle gracefully

- [x] **Stage 1.3**: Write permission revocation test cases
  - [x] Test `guacaman conngroup modify --name <group> --deny <user>` should succeed
  - [x] Test `guacaman conngroup modify --id <group_id> --deny <user>` should succeed
  - [x] Test multiple users: `--deny user1 --deny user2` should fail with appropriate error
  - [x] Test non-existent user with `--deny` should fail with appropriate error
  - [x] Test revoking non-existent permission should fail with appropriate error

- [x] **Stage 1.4**: Write permission verification test cases
  - [x] Test that granted permissions persist and are verifiable
  - [x] Test that revoked permissions are actually removed
  - [x] Test permission state verification methods

- [x] **Stage 1.5**: Write integration test cases
  - [x] Test `--permit`/`--deny` combined with existing `--parent` operations
  - [ ] Test `--permit`/`--deny` combined with connection add/remove operations (optional - separate feature)
  - [x] Test command order independence
  - [x] Test help text shows new parameters correctly

**TDD Principle**: Run `bats tests/test_conngroup_permit_deny.bats` - all tests should fail initially since no implementation exists yet.

### Stage 2: Minimal Implementation to Make Tests Pass

**Objective**: Implement just enough code to satisfy the failing tests.

- [x] **Stage 2.1**: Add CLI argument parsing (minimal implementation)
  - [x] Add `--permit USERNAME` parameter to conngroup modify subparser
  - [x] Add `--deny USERNAME` parameter to conngroup modify subparser

- [x] **Stage 2.2**: Implement basic database methods (just enough to pass tests)
  - [x] Add `grant_connection_group_permission_to_user()` to `GuacamoleDB`
  - [x] Add `revoke_connection_group_permission_from_user()` to `GuacamoleDB`
  - [x] Add ID-based variants to support `--id` selector

- [x] **Stage 2.3**: Implement CLI handler logic
  - [x] Modify `handle_conngroup_command()` to detect permission operations
  - [x] Add basic permit/deny handling with name and ID selector support
  - [x] Add minimal error handling for test scenarios

- [x] **Stage 2.4**: Run tests again - they should now pass
  - [x] Fix any remaining test failures
  - [x] Ensure error messages match test expectations

### Stage 3: Refinement and Enhancement

**Objective**: Improve implementation quality while maintaining passing tests.

- [x] **Stage 3.1**: Add comprehensive error handling
  - [x] Validate user existence before operations
  - [x] Handle permission conflicts gracefully
  - [x] Improve error message clarity and usefulness

- [x] **Stage 3.2**: Add input validation and edge case handling
  - [x] Validate argument combinations
  - [x] Handle database connection errors
  - [x] Add logging for debugging

- [x] **Stage 3.3**: Performance and reliability improvements
  - [x] Add transaction support for atomic operations
  - [x] Optimize database queries
  - [x] Add connection cleanup and resource management

**TDD Cycle**: After each enhancement, run the full test suite to ensure existing functionality remains intact and new features still work correctly.

### Stage 4: Integration Testing and Final Validation

**Objective**: Ensure the feature integrates properly with existing functionality.

- [x] **Stage 4.1**: Run full test suite against live database
  - [x] Execute all test cases with real database interactions
  - [x] Verify no regressions in existing functionality

- [x] **Stage 4.2**: Integration testing with other features
  - [x] Test permission operations combined with connection group hierarchy
  - [x] Verify permission inheritance from parent groups
  - [x] Test with existing connection permission operations

### Stage 5: Documentation and Examples

**Objective**: Complete documentation and usage examples.

- [x] **Stage 5.1**: Update README.md with new functionality
  - [x] Add usage examples for conngroup modify --permit/--deny
  - [x] Include both name-based and ID-based examples

- [x] **Stage 5.2**: Update command help text and error messages
  - [x] Ensure clear help output when no parameters provided
  - [x] Add color coding for parameter descriptions (following existing pattern)

- [x] **Stage 5.3**: Add debugging and permission verification capabilities
  - [x] Extend debug_permissions.py to show connection group permissions
  - [x] Add connection group details to debug output

## Implementation Notes

### Database Considerations
- Connection group permissions use the same `guacamole_connection_permission` table as individual connections
- Permission type is always 'READ' for Guacamole access permissions
- User entity lookup requires `type = 'USER'` filter to avoid group entity conflicts

### CLI Consistency
- Follow existing patterns from connection permission management
- Support both `--name` and `--id` selection methods
- Use the same color coding and output formatting as other commands

### Error Handling
- Validate user existence before permission operations
- Check for existing permissions to prevent duplicate grants
- Handle missing permissions gracefully during revocation
- Provide clear, actionable error messages for all failure scenarios

## Success Criteria

1. **Functional**: Users can grant/deny permissions for connection groups using both name and ID selectors
2. **Consistent**: Behavior matches existing connection permission management patterns
3. **Robust**: Comprehensive error handling and edge case coverage
4. **Testable**: Full test suite covering all functionality
5. **Well-documented**: Clear usage examples and help text

## Post-Implementation Considerations

- Performance impact on large permission sets
- Integration with connection group hierarchy and inheritance
- Potential for permission conflict resolution tools
- Batch permission management capabilities for larger deployments
