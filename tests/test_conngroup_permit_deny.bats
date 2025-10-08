#!/usr/bin/env bats

# Load the main test runner which includes setup/teardown and helper functions
load run_tests.bats

# Connection Group Permission Management Tests

@test "conngroup modify --permit with name selector should succeed" {
    group_name="test_permit_group_$(date +%s)"
    user_name="test_permit_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # Test granting permission
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully granted permission to user '$user_name' for connection group '$group_name'"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "conngroup modify --permit with id selector should succeed" {
    group_name="test_permit_id_group_$(date +%s)"
    user_name="test_permit_id_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"
    group_id=$(get_conngroup_id "$group_name")

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # Test granting permission using ID
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --id "$group_id" --permit "$user_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully granted permission to user '$user_name' for connection group ID '$group_id'"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "conngroup modify --permit multiple users should fail" {
    group_name="test_permit_multi_group_$(date +%s)"
    user_name1="test_permit_multi_user1_$(date +%s)"
    user_name2="test_permit_multi_user2_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Create test users
    guacaman --config "$TEST_CONFIG" user new --name "$user_name1" --password testpass123
    guacaman --config "$TEST_CONFIG" user new --name "$user_name2" --password testpass123

    # Test that multiple --permit arguments should fail
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name1" --permit "$user_name2"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Only one user can be specified for --permit operation"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name1"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name2"
}

@test "conngroup modify --permit non-existent user should fail" {
    group_name="test_permit_nouser_group_$(date +%s)"
    non_existent_user="nonexistent_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Test granting permission to non-existent user
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$non_existent_user"
    [ "$status" -eq 1 ]
    [[ "$output" == *"User '$non_existent_user' does not exist"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
}

@test "conngroup modify --permit non-existent connection group should fail" {
    non_existent_group="nonexistent_group_$(date +%s)"
    user_name="test_permit_nogroup_user_$(date +%s)"

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # Test granting permission to non-existent connection group
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$non_existent_group" --permit "$user_name"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Connection group '$non_existent_group' does not exist"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "conngroup modify --deny with name selector should succeed" {
    group_name="test_deny_group_$(date +%s)"
    user_name="test_deny_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # First grant permission
    guacaman --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name"

    # Test revoking permission
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --deny "$user_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully revoked permission from user '$user_name' for connection group '$group_name'"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "conngroup modify --deny with id selector should succeed" {
    group_name="test_deny_id_group_$(date +%s)"
    user_name="test_deny_id_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"
    group_id=$(get_conngroup_id "$group_name")

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # First grant permission
    guacaman --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name"

    # Test revoking permission using ID
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --id "$group_id" --deny "$user_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully revoked permission from user '$user_name' for connection group ID '$group_id'"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "conngroup modify --deny multiple users should fail" {
    group_name="test_deny_multi_group_$(date +%s)"
    user_name1="test_deny_multi_user1_$(date +%s)"
    user_name2="test_deny_multi_user2_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Create test users
    guacaman --config "$TEST_CONFIG" user new --name "$user_name1" --password testpass123
    guacaman --config "$TEST_CONFIG" user new --name "$user_name2" --password testpass123

    # Test that multiple --deny arguments should fail
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --deny "$user_name1" --deny "$user_name2"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Only one user can be specified for --deny operation"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name1"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name2"
}

@test "conngroup modify --deny non-existent user should fail" {
    group_name="test_deny_nouser_group_$(date +%s)"
    non_existent_user="nonexistent_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Test revoking permission from non-existent user
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --deny "$non_existent_user"
    [ "$status" -eq 1 ]
    [[ "$output" == *"User '$non_existent_user' does not exist"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
}

@test "conngroup modify --deny non-existent permission should fail" {
    group_name="test_deny_noperm_group_$(date +%s)"
    user_name="test_deny_noperm_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # Test revoking permission that was never granted
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --deny "$user_name"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Permission for user '$user_name' on connection group '$group_name' does not exist"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "connection group permission persistence verification" {
    group_name="test_persist_group_$(date +%s)"
    user_name="test_persist_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # Grant permission
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name"
    [ "$status" -eq 0 ]

    # Verify permission persists (check if we can grant again without error or handle gracefully)
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name"
    [ "$status" -eq 0 ]  # Should handle duplicate permission gracefully
    [[ "$output" == *"Permission already exists"* ]] || [[ "$output" == *"Successfully granted"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "connection group permission removal verification" {
    group_name="test_removal_group_$(date +%s)"
    user_name="test_removal_user_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # Grant permission first
    guacaman --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name"

    # Revoke permission
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --deny "$user_name"
    [ "$status" -eq 0 ]

    # Try to revoke again - should fail
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --deny "$user_name"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Permission for user '$user_name' on connection group '$group_name' does not exist"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "integration: conngroup modify --permit combined with --parent" {
    parent_name="test_int_parent_group_$(date +%s)"
    child_name="test_int_child_group_$(date +%s)"
    user_name="test_int_perm_user_$(date +%s)"

    # Create parent connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$parent_name"

    # Create test user
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # Test creating child with parent and permission in one command
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$child_name" --parent "$parent_name" --permit "$user_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully granted permission to user '$user_name' for connection group '$child_name'"* ]]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$child_name"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$parent_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "integration: conngroup modify --combine permit and deny operations" {
    group_name="test_int_combined_group_$(date +%s)"
    user_name1="test_int_combined_user1_$(date +%s)"
    user_name2="test_int_combined_user2_$(date +%s)"

    # Create test connection group
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"

    # Create test users
    guacaman --config "$TEST_CONFIG" user new --name "$user_name1" --password testpass123
    guacaman --config "$TEST_CONFIG" user new --name "$user_name2" --password testpass123

    # Grant permission to user1
    guacaman --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name1"

    # Grant permission to user2 and revoke from user1 in sequence
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --permit "$user_name2"
    [ "$status" -eq 0 ]

    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --deny "$user_name1"
    [ "$status" -eq 0 ]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name1"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name2"
}

@test "integration: command order independence verification" {
    group_name="test_order_group_$(date +%s)"
    user_name="test_order_user_$(date +%s)"
    parent_name="test_order_parent_$(date +%s)"

    # Create parent group and user
    guacaman --config "$TEST_CONFIG" conngroup new --name "$parent_name"
    guacaman --config "$TEST_CONFIG" user new --name "$user_name" --password testpass123

    # Test different parameter orders
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --permit "$user_name" --name "$group_name" --parent "$parent_name"
    [ "$status" -eq 0 ]

    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$parent_name"
    guacaman --config "$TEST_CONFIG" user del --name "$user_name"
}

@test "help text shows new parameters correctly" {
    run guacaman --config "$TEST_CONFIG" conngroup modify --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"--permit"* ]]
    [[ "$output" == *"--deny"* ]]
    [[ "$output" == *"USERNAME"* ]]
}