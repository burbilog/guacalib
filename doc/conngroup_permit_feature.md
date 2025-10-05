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

### Stage 1: Database Layer - Permission Methods

**Objective**: Implement database methods for connection group permission management.

- [ ] **Stage 1.1**: Add `grant_connection_group_permission_to_user(username, connection_group_name)` method to `GuacamoleDB` class
  - Get connection group ID from `guacamole_connection_group` table
  - Get user entity ID from `guacamole_entity` table
  - Check for existing permission to prevent duplicates
  - Insert permission record with 'READ' permission type
  - Return success/failure status

- [ ] **Stage 1.2**: Add `revoke_connection_group_permission_from_user(username, connection_group_name)` method to `GuacamodeDB` class
  - Get connection group ID from `guacamole_connection_group` table
  - Get user entity ID from `guacamole_entity` table
  - Check for existing permission before revoking
  - Delete permission record
  - Return success/failure status

- [ ] **Stage 1.3**: Add ID-based variants of both methods for `--id` parameter support
  - `grant_connection_group_permission_to_user_by_id(username, connection_group_id)`
  - `revoke_connection_group_permission_from_user_by_id(username, connection_group_id)`

### Stage 2: CLI Argument Parsing

**Objective**: Add `--permit` and `--deny` arguments to conngroup modify subcommand.

- [ ] **Stage 2.1**: Add `--permit USERNAME` parameter to conngroup modify subparser
  - Use `add_argument('--permit', metavar='USERNAME', help='Grant permission to user')`
  - Allow multiple permits by using `action='append'`

- [ ] **Stage 2.2**: Add `--deny USERNAME` parameter to conngroup modify subparser
  - Use `add_argument('--deny', metavar='USERNAME', help='Revoke permission from user')`
  - Allow multiple denies by using `action='append'`

- [ ] **Stage 2.3**: Update help text to include new parameters alongside existing ones

### Stage 3: CLI Handler Implementation

**Objective**: Implement the command handling logic in `cli_handle_conngroup.py`.

- [ ] **Stage 3.1**: Modify `handle_conngroup_command()` modify branch to detect permission operations
  - Check if `args.permit` or `args.deny` are provided
  - Add permission operation to the existing modification validation logic

- [ ] **Stage 3.2**: Implement permit handling logic
  - Support both name-based (`--name`) and ID-based (`--id`) group selection
  - Iterate through multiple permit users if provided
  - Call appropriate database method based on selector type
  - Provide success feedback for each user

- [ ] **Stage 3.3**: Implement deny handling logic
  - Support both name-based (`--name`) and ID-based (`--id`) group selection
  - Iterate through multiple deny users if provided
  - Call appropriate database method based on selector type
  - Provide success feedback for each user

- [ ] **Stage 3.4**: Add error handling and validation
  - Validate user existence before permission operations
  - Handle permission conflicts (already permitted/not permitted)
  - Provide clear error messages for debugging

### Stage 4: Testing Infrastructure

**Objective**: Create comprehensive test suite for the new functionality.

- [ ] **Stage 4.1**: Create test file `tests/test_conngroup_permit_deny.bats`
  - Setup/teardown test users and connection groups
  - Test both name-based and ID-based operations
  - Test multiple users in single command

- [ ] **Stage 4.2**: Test permission granting scenarios
  - Grant permission to single user with `--name` selector
  - Grant permission to single user with `--id` selector
  - Grant permission to multiple users in one command
  - Attempt to grant permission to non-existent user (should fail)
  - Attempt to grant permission for non-existent group (should fail)

- [ ] **Stage 4.3**: Test permission revocation scenarios
  - Revoke permission from single user with `--name` selector
  - Revoke permission from single user with `--id` selector
  - Revoke permission from multiple users in one command
  - Attempt to revoke permission from non-existent user (should fail)
  - Attempt to revoke permission not previously granted (should fail)

- [ ] **Stage 4.4**: Test permission state verification
  - Use permission listing/debugging to verify granted permissions
  - Test that permissions persist after group modification
  - Test that permissions are correctly revoked

- [ ] **Stage 4.5**: Integration tests with existing modify operations
  - Test `--permit`/`--deny` combined with `--parent` operations
  - Test `--permit`/`--deny` combined with connection add/remove operations
  - Test order independence of operations

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
- Support multiple users per command for consistency with other operations

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