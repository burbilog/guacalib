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

- [ ] **Stage 1.1**: Create test file `tests/test_conngroup_permit_deny.bats`
  - Setup/teardown functions for test users and connection groups
  - Test both name-based and ID-based operations

- [ ] **Stage 1.2**: Write permission granting test cases
  - Test `guacaman conngroup modify --name <group> --permit <user>` should succeed
  - Test `guacaman conngroup modify --id <group_id> --permit <user>` should succeed
  - Single user action should be allowed only: `--permit user1 --permit user2` should fail with appropriate error
  - Test non-existent user with `--permit` should fail with appropriate error
  - Test non-existent group with `--permit` should fail with appropriate error
  - Test duplicate permission grant should handle gracefully

- [ ] **Stage 1.3**: Write permission revocation test cases
  - Test `guacaman conngroup modify --name <group> --deny <user>` should succeed
  - Test `guacaman conngroup modify --id <group_id> --deny <user>` should succeed
  - Test multiple users: `--deny user1 --deny user2` should fail with appropriate error
  - Test non-existent user with `--deny` should fail with appropriate error
  - Test revoking non-existent permission should fail with appropriate error

- [ ] **Stage 1.4**: Write permission verification test cases
  - Test that granted permissions persist and are verifiable
  - Test that revoked permissions are actually removed
  - Test permission state verification methods

- [ ] **Stage 1.5**: Write integration test cases
  - Test `--permit`/`--deny` combined with existing `--parent` operations
  - Test `--permit`/`--deny` combined with connection add/remove operations
  - Test command order independence
  - Test help text shows new parameters correctly

**TDD Principle**: Run `bats tests/test_conngroup_permit_deny.bats` - all tests should fail initially since no implementation exists yet.

### Stage 2: Minimal Implementation to Make Tests Pass

**Objective**: Implement just enough code to satisfy the failing tests.

- [ ] **Stage 2.1**: Add CLI argument parsing (minimal implementation)
  - Add `--permit USERNAME` parameter to conngroup modify subparser
  - Add `--deny USERNAME` parameter to conngroup modify subparser

- [ ] **Stage 2.2**: Implement basic database methods (just enough to pass tests)
  - Add `grant_connection_group_permission_to_user()` to `GuacamoleDB`
  - Add `revoke_connection_group_permission_from_user()` to `GuacamoleDB`
  - Add ID-based variants to support `--id` selector

- [ ] **Stage 2.3**: Implement CLI handler logic
  - Modify `handle_conngroup_command()` to detect permission operations
  - Add basic permit/deny handling with name and ID selector support
  - Add minimal error handling for test scenarios

- [ ] **Stage 2.4**: Run tests again - they should now pass
  - Fix any remaining test failures
  - Ensure error messages match test expectations

### Stage 3: Refinement and Enhancement

**Objective**: Improve implementation quality while maintaining passing tests.

- [ ] **Stage 3.1**: Add comprehensive error handling
  - Validate user existence before operations
  - Handle permission conflicts gracefully
  - Improve error message clarity and usefulness

- [ ] **Stage 3.2**: Add input validation and edge case handling
  - Validate argument combinations
  - Handle database connection errors
  - Add logging for debugging

- [ ] **Stage 3.3**: Performance and reliability improvements
  - Add transaction support for atomic operations
  - Optimize database queries
  - Add connection cleanup and resource management

**TDD Cycle**: After each enhancement, run the full test suite to ensure existing functionality remains intact and new features still work correctly.

### Stage 4: Integration Testing and Final Validation

**Objective**: Ensure the feature integrates properly with existing functionality.

- [ ] **Stage 4.1**: Run full test suite against live database
  - Execute all test cases with real database interactions
  - Verify no regressions in existing functionality

- [ ] **Stage 4.2**: Integration testing with other features
  - Test permission operations combined with connection group hierarchy
  - Verify permission inheritance from parent groups
  - Test with existing connection permission operations

### Stage 5: Documentation and Examples

**Objective**: Complete documentation and usage examples.

- [ ] **Stage 5.1**: Update README.md with new functionality
  - Add usage examples for conngroup modify --permit/--deny
  - Include both name-based and ID-based examples

- [ ] **Stage 5.2**: Update command help text and error messages
  - Ensure clear help output when no parameters provided
  - Add color coding for parameter descriptions (following existing pattern)

- [ ] **Stage 5.3**: Add debugging and permission verification capabilities
  - Extend debug_permissions.py to show connection group permissions
  - Add permission display to conngroup list command

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
