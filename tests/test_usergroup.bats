#!/usr/bin/env bats

# Load centralized setup/teardown functions
load 'setup_teardown.bash'

# Helper function to get usergroup ID by name from list output
get_usergroup_id() {
    local group_name="$1"
    guacaman --config "$TEST_CONFIG" usergroup list | \
        awk -v name="$group_name" '
            $0 ~ "^  " name ":" { in_group = 1; next }
            in_group && /^    id: / { print $2; exit }
            in_group && /^  [^[:space:]]/ { exit }  # next group
        '
}

@test "User group creation and existence" {
    run guacaman --config "$TEST_CONFIG" usergroup exists --name testgroup1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" usergroup exists --name testgroup2
    [ "$status" -eq 0 ]
}

@test "User group listing" {
    run guacaman --config "$TEST_CONFIG" usergroup list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testgroup1"* ]]
    [[ "$output" == *"testgroup2"* ]]
}

@test "User group deletion" {
    run guacaman --config "$TEST_CONFIG" usergroup del --name testgroup1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" usergroup exists --name testgroup1
    [ "$status" -eq 1 ]
}

@test "Add user to usergroup" {
    run guacaman --debug --config "$TEST_CONFIG" usergroup modify --name testgroup1 --adduser testuser2
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully added user 'testuser2' to usergroup 'testgroup1'"* ]]
    
    run guacaman --debug --config "$TEST_CONFIG" usergroup list
    [[ "$output" == *"testgroup1:"* ]]
    [[ "$output" == *"users:"* ]]
    [[ "$output" == *"- testuser2"* ]]
}

@test "Remove user from usergroup" {
    # First add the user
    run guacaman --debug --config "$TEST_CONFIG" usergroup modify --name testgroup1 --adduser testuser2
    
    # Then remove them
    run guacaman --debug --config "$TEST_CONFIG" usergroup modify --name testgroup1 --rmuser testuser2
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully removed user 'testuser2' from usergroup 'testgroup1'"* ]]
    
    run guacaman --config "$TEST_CONFIG" usergroup list
    [[ "$output" == *"testgroup1:"* ]]
    [[ "$output" != *"- testuser2"* ]]
}

@test "Add user to non-existent group should fail" {
    run guacaman --config "$TEST_CONFIG" usergroup modify --name nonexistentgroup --adduser testuser1
    [ "$status" -ne 0 ]
    [[ "$output" == *"does not exist"* ]]
}

@test "Remove user from non-existent group should fail" {
    run guacaman --config "$TEST_CONFIG" usergroup modify --name nonexistentgroup --rmuser testuser1
    [ "$status" -ne 0 ]
    [[ "$output" == *"does not exist"* ]]
}

@test "Add non-existent user to group should fail" {
    run guacaman --config "$TEST_CONFIG" usergroup modify --name testgroup1 --adduser nonexistentuser
    [ "$status" -ne 0 ]
    [[ "$output" == *"does not exist"* ]]
}

@test "Remove non-existent user from group should fail" {
    run guacaman --config "$TEST_CONFIG" usergroup modify --name testgroup1 --rmuser nonexistentuser
    [ "$status" -ne 0 ]
    [[ "$output" == *"does not exist"* ]]
}

@test "Remove user not in group should fail" {
    # First ensure testuser2 is not in testgroup1
    run guacaman --config "$TEST_CONFIG" usergroup modify --name testgroup1 --rmuser testuser2
    [ "$status" -ne 0 ]
    [[ "$output" == *"is not in group"* ]]
}

# =============================================================================
# STAGE UG-T: List output tests (IDs visible)
# =============================================================================

@test "usergroup list includes ID field for every group" {
    run guacaman --config "$TEST_CONFIG" usergroup list
    [ "$status" -eq 0 ]
    [[ "$output" == *"usergroups:"* ]]
    [[ "$output" == *"id:"* ]]
    
    # Count the number of groups with ID fields
    group_count=$(echo "$output" | grep -c "^  [a-zA-Z0-9_-][^:]*:")
    id_count=$(echo "$output" | grep -c "id:")
    [ "$id_count" -eq "$group_count" ]
}

@test "usergroup list ID is positive integer for all groups" {
    run guacaman --config "$TEST_CONFIG" usergroup list
    [ "$status" -eq 0 ]
    # Extract all ID values
    ids=$(echo "$output" | grep -A1 "^  [a-zA-Z0-9_-][^:]*:" | grep "id:" | cut -d: -f2 | tr -d ' ')
    for id in $ids; do
        [ "$id" -gt 0 ]
    done
}

@test "usergroup list output structure preserved" {
    run guacaman --config "$TEST_CONFIG" usergroup list
    [ "$status" -eq 0 ]
    # Check that the output has the expected structure: group name, then id, then users and connections
    [[ "$output" == *"usergroups:"* ]]
    [[ "$output" == *"testgroup1:"* ]]
    [[ "$output" == *"id:"* ]]
    [[ "$output" == *"users:"* ]]
    [[ "$output" == *"connections:"* ]]
}

@test "usergroup list: filter by specific --id" {
    # Get the ID of a test group
    gid=$(get_usergroup_id "testgroup1")

    # List only that group
    run guacaman --config "$TEST_CONFIG" usergroup list --id "$gid"
    [ "$status" -eq 0 ]

    # Should only contain that specific group, not others
    [[ "$output" == *"testgroup1"* ]]
    [[ "$output" != *"testgroup2"* ]]

    # Verify it includes the ID field
    [[ "$output" == *"id: $gid"* ]]
}

# =============================================================================
# STAGE UG-T: User Group ID Support - Parser and Selector Validation Tests
# (moved from tests/test_guacaman.bats)
# =============================================================================

@test "usergroup exists: requires exactly one selector" {
    # Both --name and --id provided → parser error (exit 2)
    run guacaman --config "$TEST_CONFIG" usergroup exists --name testgroup1 --id 1
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
    
    # Neither provided → parser error (exit 2)
    run guacaman --config "$TEST_CONFIG" usergroup exists
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments"* ]] && [[ "$output" == *"is required"* ]]
}

@test "usergroup exists: invalid ID formats" {
    # Zero ID
    run guacaman --config "$TEST_CONFIG" usergroup exists --id 0
    [ "$status" -eq 2 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Negative ID
    run guacaman --config "$TEST_CONFIG" usergroup exists --id -1
    [ "$status" -eq 2 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
}

@test "usergroup del: requires exactly one selector" {
    # Both --name and --id provided → parser error (exit 2)
    run guacaman --config "$TEST_CONFIG" usergroup del --name testgroup1 --id 1
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
    
    # Neither provided → parser error (exit 2)
    run guacaman --config "$TEST_CONFIG" usergroup del
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments"* ]] && [[ "$output" == *"is required"* ]]
}

@test "usergroup del: invalid ID formats" {
    # Zero ID
    run guacaman --config "$TEST_CONFIG" usergroup del --id 0
    [ "$status" -eq 2 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Negative ID
    run guacaman --config "$TEST_CONFIG" usergroup del --id -1
    [ "$status" -eq 2 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
}

@test "usergroup modify: requires exactly one selector when modification flags provided" {
    # Both --name and --id provided → parser error (exit 2)
    run guacaman --config "$TEST_CONFIG" usergroup modify --name testgroup1 --id 1 --adduser testuser1
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
    
    # Neither provided → parser error (exit 2)
    run guacaman --config "$TEST_CONFIG" usergroup modify --adduser testuser1
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments"* ]] && [[ "$output" == *"is required"* ]]
}

@test "usergroup modify: invalid ID formats" {
    # Zero ID
    run guacaman --config "$TEST_CONFIG" usergroup modify --id 0 --adduser testuser1
    [ "$status" -eq 2 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Negative ID
    run guacaman --config "$TEST_CONFIG" usergroup modify --id -1 --adduser testuser1
    [ "$status" -eq 2 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
}

@test "usergroup modify: no modification flags shows usage/help text" {
    # Should show help and exit gracefully (exit code 0 for help)
    run guacaman --config "$TEST_CONFIG" usergroup modify
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage:"* ]] || [[ "$output" == *"Modification options:"* ]]
    
    # Should also show help when only selector provided
    run guacaman --config "$TEST_CONFIG" usergroup modify --name testgroup1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage:"* ]] || [[ "$output" == *"Modification options:"* ]]
}
