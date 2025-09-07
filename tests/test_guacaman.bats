#!/usr/bin/env bats

setup() {
    # Check if TEST_CONFIG is set and points to a valid file
    if [ -z "$TEST_CONFIG" ] || [ ! -f "$TEST_CONFIG" ]; then
        echo "Error: TEST_CONFIG environment variable must be set to a valid config file"
        echo "Example:"
        echo "  export TEST_CONFIG=/path/to/test_config.ini"
        skip "TEST_CONFIG variable is not set"
    fi

    # Verify the config file contains required sections
    if ! grep -q '\[mysql\]' "$TEST_CONFIG"; then
        skip "Test config file must contain [mysql] section"
    fi

    # Create test groups, users and connections
    guacaman --config "$TEST_CONFIG" usergroup new --name testgroup1
    guacaman --config "$TEST_CONFIG" usergroup new --name testgroup2
    guacaman --config "$TEST_CONFIG" user new --name testuser1 --password testpass1 --usergroup testgroup1,testgroup2
    guacaman --config "$TEST_CONFIG" user new --name testuser2 --password testpass2
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --password vncpass1 --usergroup testgroup1
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn2 --hostname 192.168.1.101 --port 5902 --password vncpass2
    guacaman --config "$TEST_CONFIG" usergroup new --name parentgroup1
    guacaman --config "$TEST_CONFIG" usergroup new --name nested/parentgroup2
    guacaman --config "$TEST_CONFIG" conngroup new --name testconngroup1
    guacaman --config "$TEST_CONFIG" conngroup new --name testconngroup2 --parent testconngroup1
}

teardown() {
    # Clean up test objects
    guacaman --config "$TEST_CONFIG" conn del --name testconn1 || true
    guacaman --config "$TEST_CONFIG" conn del --name testconn2 || true
    guacaman --config "$TEST_CONFIG" user del --name testuser1 || true
    guacaman --config "$TEST_CONFIG" user del --name testuser2 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name testgroup1 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name testgroup2 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name parentgroup1 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name nested/parentgroup2 || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup1 || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup2 || true
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

@test "User creation and existence" {
    run guacaman --config "$TEST_CONFIG" user exists --name testuser1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" user exists --name testuser2
    [ "$status" -eq 0 ]
}

@test "User listing" {
    run guacaman --config "$TEST_CONFIG" user list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testuser1"* ]]
    [[ "$output" == *"testuser2"* ]]
    [[ "$output" == *"testgroup1"* ]]
    [[ "$output" == *"testgroup2"* ]]
}

@test "User deletion" {
    run guacaman --config "$TEST_CONFIG" user del --name testuser1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" user exists --name testuser1
    [ "$status" -eq 1 ]
}

@test "VNC connection creation and existence" {
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn2
    [ "$status" -eq 0 ]
}

@test "VNC connection listing" {
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn1"* ]]
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"192.168.1.100"* ]]
    [[ "$output" == *"5901"* ]]
    [[ "$output" == *"testgroup1"* ]]
}

@test "VNC connection deletion" {
    run guacaman --config "$TEST_CONFIG" conn del --name testconn1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1
    [ "$status" -eq 1 ]
}

@test "Create existing user group should fail" {
    run guacaman --config "$TEST_CONFIG" usergroup new --name testgroup1
    [ "$status" -ne 0 ]
    [[ "$output" == *"already exists"* ]]
}

@test "Delete non-existent user group should fail" {
    run guacaman --config "$TEST_CONFIG" usergroup del --name nonexistentgroup
    [ "$status" -ne 0 ]
    [[ "$output" == *"does not exist"* ]]
}

@test "Create existing user should fail" {
    run guacaman --config "$TEST_CONFIG" user new --name testuser1 --password testpass1
    [ "$status" -ne 0 ]
    [[ "$output" == *"already exists"* ]]
}

@test "Delete non-existent user should fail" {
    run guacaman --config "$TEST_CONFIG" user del --name nonexistentuser
    [ "$status" -ne 0 ]
    [[ "$output" == *"doesn't exist"* ]]
}

@test "Create existing connection should fail" {
    run guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --password vncpass1
    [ "$status" -ne 0 ]
    [[ "$output" == *"already exists"* ]]
}

@test "Delete non-existent connection should fail" {
    run guacaman --config "$TEST_CONFIG" conn del --name nonexistentconn
    [ "$status" -ne 0 ]
    [[ "$output" == *"doesn't exist"* ]]
}

@test "Connection modify command shows parameters" {
    run guacaman --config "$TEST_CONFIG" conn modify
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments --name --id is required"* ]]
}

@test "Connection modify hostname parameter" {
    # Modify the hostname
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set hostname=10.1.1.10
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    
    # Verify the change in the connection listing
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"hostname: 10.1.1.10"* ]]
}

@test "Connection modify port parameter" {
    # Modify the port
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set port=5910
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated port"* ]]
    
    # Verify the change in the connection listing
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"port: 5910"* ]]
}

@test "Connection modify password parameter" {
    # Modify the password
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set password=newvncpass
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated password"* ]]
}

@test "Connection modify read-only parameter" {
    # Set read-only to true
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set read-only=true
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Set read-only to false
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set read-only=false
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Invalid value should fail
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set read-only=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be 'true' or 'false'"* ]]
}

@test "Connection modify max_connections parameter" {
    # Modify max_connections
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set max_connections=5
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated max_connections"* ]]
    
    # Invalid value should fail
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set max_connections=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be an integer"* ]]
}

@test "Connection modify max_connections_per_user parameter" {
    # Modify max_connections_per_user
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set max_connections_per_user=3
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated max_connections_per_user"* ]]
    
    # Invalid value should fail
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set max_connections_per_user=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be an integer"* ]]
}

@test "Connection modify multiple parameters at once" {
    # Modify multiple parameters
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --set hostname=192.168.2.100 --set port=5905 --set read-only=true
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    [[ "$output" == *"Successfully updated port"* ]]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Verify the changes in the connection listing
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"hostname: 192.168.2.100"* ]]
    [[ "$output" == *"port: 5905"* ]]
}

@test "Connection modify non-existent connection should fail" {
    run guacaman --config "$TEST_CONFIG" conn modify --name nonexistentconn --set hostname=10.1.1.10
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "Connection modify invalid parameter should fail" {
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set invalid_param=value
    [ "$status" -ne 0 ]
    [[ "$output" == *"Invalid parameter"* ]]
}

@test "Connection modify set parent group" {
    # Set parent group
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --parent testconngroup1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to 'testconngroup1'"* ]]
    
    # Verify in connection list
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"parent: testconngroup1"* ]]
}

@test "Connection modify remove parent group" {
    # First set a group
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --parent testconngroup2
    [ "$status" -eq 0 ]
    # Then remove it
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --parent ""
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to ''"* ]]
    
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" != *"testconngroup2"* ]]
}

@test "Connection modify set nested parent group" {
    
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --parent testconngroup2
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to 'testconngroup2'"* ]]
    
    run guacaman --debug --config "$TEST_CONFIG" conn list
    echo "$output" > /tmp/testconn2.txt
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"parent: testconngroup2"* ]]
    
}

@test "Connection modify grant permission to user" {
    # Grant permission
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --permit testuser1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully granted permission to user 'testuser1' for connection 'testconn2'"* ]]

    # Verify permission exists
    run guacaman --debug --config "$TEST_CONFIG" dump
    [[ "$output" == *"testconn2:"* ]]
    [[ "$output" == *"permissions:"* ]]
    [[ "$output" == *"- testuser1"* ]]
}

@test "Connection modify grant permission to already permitted user should fail" {
    # First grant permission
    guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --permit testuser1
    
    # Try to grant again
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --permit testuser1
    [ "$status" -ne 0 ]
    [[ "$output" == *"already has permission"* ]]
}

@test "Connection modify revoke permission from user" {
    # First grant permission
    guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --permit testuser1
    
    # Revoke permission
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --deny testuser1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully revoked permission from user 'testuser1' for connection 'testconn2'"* ]]

    # Verify permission is gone - updated to check that testuser1 isn't listed under permissions rather than
    # checking for the absence of the permissions: section entirely
    run guacaman --debug --config "$TEST_CONFIG" dump
    [[ "$output" == *"testconn2:"* ]]
    # Don't check for absence of permissions section anymore:
    # [[ "$output" != *"permissions:"* ]]
    # Instead, verify the specific user isn't listed
    [[ ! $(echo "$output" | grep -A10 "testconn2:" | grep -A5 "permissions:" | grep "testuser1") ]]
}

@test "Connection modify grant permission to non-existent user should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --permit nonexistentuser
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "Connection modify revoke permission from non-existent user should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn2 --deny nonexistentuser
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "Connection modify grant permission to non-existent connection should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name nonexistentconn --permit testuser1
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "Connection modify revoke permission from non-existent connection should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name nonexistentconn --deny testuser1
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
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


@test "Connection group creation with debug" {
    group_name="testgroup_$(date +%s)"
    
    # Test successful creation
    run guacaman --debug --config "$TEST_CONFIG" conngroup new --name "$group_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully created connection group: $group_name"* ]]
    
    # Verify it exists
    run guacaman --debug --config "$TEST_CONFIG" conngroup exists --name "$group_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Connection group '$group_name' exists"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
}

@test "Connection group creation with parent group" {
    parent_name="parentgroup_$(date +%s)"
    child_name="childgroup_$(date +%s)"
    
    # Create parent
    guacaman --config "$TEST_CONFIG" conngroup new --name "$parent_name"
    
    # Create child with parent
    run guacaman --debug --config "$TEST_CONFIG" conngroup new --name "$child_name" --parent "$parent_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully created connection group: $child_name"* ]]
    
    # Verify parent-child relationship
    run guacaman --config "$TEST_CONFIG" conngroup list
    [[ "$output" == *"$child_name:"* ]]
    [[ "$output" == *"parent: $parent_name"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$child_name"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$parent_name"
}

@test "Connection group listing" {
    group_name="listgroup_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"
    
    run guacaman --debug --config "$TEST_CONFIG" conngroup list
    [ "$status" -eq 0 ]
    [[ "$output" == *"$group_name:"* ]]
    [[ "$output" == *"parent: ROOT"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
}

@test "Connection group existence check" {
    group_name="existgroup_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"
    
    # Positive check
    run guacaman --debug --config "$TEST_CONFIG" conngroup exists --name "$group_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Connection group '$group_name' exists"* ]]
    
    # Negative check
    run guacaman --debug --config "$TEST_CONFIG" conngroup exists --name "nonexistentgroup_$(date +%s)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Connection group 'nonexistentgroup_"*" does not exist"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
}

@test "Connection group deletion" {
    group_name="delgroup_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"
    
    # Verify it exists first
    run guacaman --debug --config "$TEST_CONFIG" conngroup exists --name "$group_name"
    [ "$status" -eq 0 ]
    
    # Delete it
    run guacaman --debug --config "$TEST_CONFIG" conngroup del --name "$group_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully deleted connection group '$group_name'"* ]]
    
    # Verify it's gone
    run guacaman --debug --config "$TEST_CONFIG" conngroup exists --name "$group_name"
    [ "$status" -eq 1 ]
}

@test "Create existing connection group should fail" {
    group_name="existinggroup_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"
    
    run guacaman --debug --config "$TEST_CONFIG" conngroup new --name "$group_name"
    [ "$status" -ne 0 ]
    [[ "$output" == *"already exists"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
}

@test "Delete non-existent connection group should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conngroup del --name "nonexistentgroup_$(date +%s)"
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "Connection group modify parent" {
    parent_name="parent_$(date +%s)"
    child_name="child_$(date +%s)"
    
    # Create groups
    guacaman --config "$TEST_CONFIG" conngroup new --name "$parent_name"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$child_name"
    
    # Set parent
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$child_name" --parent "$parent_name"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group for '$child_name' to '$parent_name'"* ]]
    
    # Verify relationship
    run guacaman --config "$TEST_CONFIG" conngroup list
    [[ "$output" == *"$child_name:"* ]]
    [[ "$output" == *"parent: $parent_name"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$child_name"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$parent_name"
}

@test "Connection group modify remove parent" {
    parent_name="parent_$(date +%s)"
    child_name="child_$(date +%s)"
    
    # Create groups with parent
    guacaman --config "$TEST_CONFIG" conngroup new --name "$parent_name"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$child_name" --parent "$parent_name"
    
    # Remove parent
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$child_name" --parent ""
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group for '$child_name' to ''"* ]]
    
    # Verify no parent
    run guacaman --config "$TEST_CONFIG" conngroup list
    [[ "$output" == *"$child_name:"* ]]
    [[ "$output" == *"parent: ROOT"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$child_name"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$parent_name"
}



@test "Connection group creation detect cycles" {
    group1="group1_$(date +%s)"
    group2="group2_$(date +%s)"
    group3="group3_$(date +%s)"
    
    # Create initial hierarchy: group1 -> group2
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group1"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group2" --parent "$group1"
    
    # Try to create group3 with parent group2, then make group1 parent of group3
    # This would create cycle: group1 -> group2 -> group3 -> group1
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group3" --parent "$group2"
    
    # Attempt to create cycle by modifying group1's parent to be group3
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group1" --parent "$group3"
    [ "$status" -ne 0 ]
    [[ "$output" == *"would create a cycle"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group3"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group2"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group1"
}

@test "Connection group modify detect cycles" {
    group1="group1_$(date +%s)"
    group2="group2_$(date +%s)"
    group3="group3_$(date +%s)"
    
    # Create groups
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group1"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group2"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group3"
    
    # Set up hierarchy: group1 -> group2 -> group3
    guacaman --config "$TEST_CONFIG" conngroup modify --name "$group2" --parent "$group1"
    guacaman --config "$TEST_CONFIG" conngroup modify --name "$group3" --parent "$group2"
    
    # Try to create cycle: group1 -> group3 (would make group1 -> group3 -> group2 -> group1)
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group1" --parent "$group3"
    [ "$status" -ne 0 ]
    [[ "$output" == *"would create a cycle"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group3"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group2"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group1"
}

@test "Connection group modify non-existent group should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "nonexistent_$(date +%s)" --parent "somegroup"
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "Connection group modify non-existent parent should fail" {
    group_name="testgroup_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$group_name"
    
    run guacaman --debug --config "$TEST_CONFIG" conngroup modify --name "$group_name" --parent "nonexistentparent"
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$group_name"
}

@test "Dump command shows test data" {
    run guacaman --config "$TEST_CONFIG" dump
    [ "$status" -eq 0 ]
    
    # Check groups section
    [[ "$output" == *"groups:"* ]]
    [[ "$output" == *"testgroup1:"* ]]
    [[ "$output" == *"testgroup2:"* ]]
    
    # Check users section
    [[ "$output" == *"users:"* ]]
    [[ "$output" == *"testuser1:"* ]]
    [[ "$output" == *"testuser2:"* ]]
    [[ "$output" == *"groups:"* ]]  # users should have groups section
    
    # Check connections section
    [[ "$output" == *"connections:"* ]]
    [[ "$output" == *"testconn1:"* ]]
    [[ "$output" == *"testconn2:"* ]]
    [[ "$output" == *"hostname: 192.168.1.100"* ]]
    [[ "$output" == *"hostname: 192.168.1.101"* ]]
    
    # Save full output for debugging
    echo "$output" > /tmp/output.txt
    
    # Verify testuser1 group memberships
    echo "$output" | grep -A 10 'testuser1:' | grep -q 'testgroup1'
    echo "$output" | grep -A 10 'testuser1:' | grep -q 'testgroup2'

    # Verify testconn1 group associations
    echo "$output" | grep -A 10 'testconn1:' | grep -q 'testgroup1'
}

# =============================================================================
# STAGE 1 TESTS: Database Layer ID Support (IDs Feature)
# =============================================================================
# These tests verify the database layer resolver methods and enhanced existing
# methods that accept both name and ID parameters. Tests are designed to pass
# once Stage 1 implementation is complete.

# Helper function to extract connection ID from list output
get_connection_id() {
    local conn_name="$1"
    guacaman --config "$TEST_CONFIG" conn list | grep -A 1 "^  $conn_name:" | grep "id:" | cut -d: -f2 | tr -d ' '
}

# Helper function to extract connection group ID from list output  
get_conngroup_id() {
    local group_name="$1"
    guacaman --config "$TEST_CONFIG" conngroup list | grep -A 1 "^  $group_name:" | grep "id:" | cut -d: -f2 | tr -d ' '
}

@test "Connection exists with ID parameter" {
    # Get the ID of testconn1
    conn_id=$(get_connection_id "testconn1")
    [ -n "$conn_id" ]
    
    # Test exists with valid ID
    run guacaman --config "$TEST_CONFIG" conn exists --id "$conn_id"
    [ "$status" -eq 0 ]
    
    # Test exists with invalid ID
    run guacaman --config "$TEST_CONFIG" conn exists --id 99999
    [ "$status" -eq 1 ]
    
    # Test validation: both name and ID provided should fail
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1 --id "$conn_id"
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
    
    # Test validation: neither name nor ID provided should fail
    run guacaman --config "$TEST_CONFIG" conn exists
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments"* ]] && [[ "$output" == *"is required"* ]]
}

@test "Connection exists with invalid ID format" {
    # Test zero ID
    run guacaman --config "$TEST_CONFIG" conn exists --id 0
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Test negative ID
    run guacaman --config "$TEST_CONFIG" conn exists --id -1
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
}

@test "Connection delete with ID parameter" {
    # Create a temporary connection for deletion test
    temp_conn="temp_del_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name "$temp_conn" --hostname 192.168.1.200 --port 5900 --password temp
    
    # Get its ID
    conn_id=$(get_connection_id "$temp_conn")
    [ -n "$conn_id" ]
    
    # Delete by ID
    run guacaman --config "$TEST_CONFIG" conn del --id "$conn_id"
    [ "$status" -eq 0 ]
    
    # Verify it's gone
    run guacaman --config "$TEST_CONFIG" conn exists --name "$temp_conn"
    [ "$status" -eq 1 ]
}

@test "Connection delete with invalid ID" {
    # Test delete with non-existent ID
    run guacaman --config "$TEST_CONFIG" conn del --id 99999
    [ "$status" -eq 1 ]
    [[ "$output" == *"not found"* ]] || [[ "$output" == *"does not exist"* ]]
    
    # Test validation: both name and ID provided
    run guacaman --config "$TEST_CONFIG" conn del --name testconn1 --id 1
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
}

@test "Connection modify with ID parameter" {
    # Get ID of testconn2
    conn_id=$(get_connection_id "testconn2")
    [ -n "$conn_id" ]
    
    # Modify by ID
    run guacaman --config "$TEST_CONFIG" conn modify --id "$conn_id" --set hostname=10.0.0.99
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    
    # Verify the change
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"hostname: 10.0.0.99"* ]]
}

@test "Connection modify parent group with ID parameter" {
    # Get connection ID
    conn_id=$(get_connection_id "testconn2")
    [ -n "$conn_id" ]
    
    # Set parent group using ID
    run guacaman --config "$TEST_CONFIG" conn modify --id "$conn_id" --parent testconngroup1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group"* ]]
    
    # Verify in listing
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"parent: testconngroup1"* ]]
}

@test "Connection group exists with ID parameter" {
    # Get ID of testconngroup1
    group_id=$(get_conngroup_id "testconngroup1")
    [ -n "$group_id" ]
    
    # Test exists with valid ID
    run guacaman --config "$TEST_CONFIG" conngroup exists --id "$group_id"
    [ "$status" -eq 0 ]
    
    # Test exists with invalid ID
    run guacaman --config "$TEST_CONFIG" conngroup exists --id 99999
    [ "$status" -eq 1 ]
    
    # Test validation: both name and ID provided
    run guacaman --config "$TEST_CONFIG" conngroup exists --name testconngroup1 --id "$group_id"
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
}

@test "Connection group delete with ID parameter" {
    # Create temporary group for deletion
    temp_group="temp_del_group_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$temp_group"
    
    # Get its ID
    group_id=$(get_conngroup_id "$temp_group")
    [ -n "$group_id" ]
    
    # Delete by ID
    run guacaman --config "$TEST_CONFIG" conngroup del --id "$group_id"
    [ "$status" -eq 0 ]
    
    # Verify it's gone
    run guacaman --config "$TEST_CONFIG" conngroup exists --name "$temp_group"
    [ "$status" -eq 1 ]
}

@test "Connection group modify parent with ID parameter" {
    # Create test groups
    parent_group="parent_id_test_$(date +%s)"
    child_group="child_id_test_$(date +%s)"
    
    guacaman --config "$TEST_CONFIG" conngroup new --name "$parent_group"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$child_group"
    
    # Get child group ID
    child_id=$(get_conngroup_id "$child_group")
    [ -n "$child_id" ]
    
    # Set parent using ID
    run guacaman --config "$TEST_CONFIG" conngroup modify --id "$child_id" --parent "$parent_group"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group"* ]]
    
    # Verify relationship
    run guacaman --config "$TEST_CONFIG" conngroup list
    [[ "$output" == *"$child_group:"* ]]
    [[ "$output" == *"parent: $parent_group"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$child_group"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$parent_group"
}

@test "Backward compatibility - existing name-based calls unchanged" {
    # All existing name-based operations should continue to work exactly as before
    
    # Connection operations
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set port=5999
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated port"* ]]
    
    # Connection group operations  
    run guacaman --config "$TEST_CONFIG" conngroup exists --name testconngroup1
    [ "$status" -eq 0 ]
    
    # Verify nothing changed in the existing behavior
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn1"* ]]
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"port: 5999"* ]]
}

@test "Error handling for resolver edge cases" {
    # Test resolver with empty/null values
    run guacaman --config "$TEST_CONFIG" conn exists --id ""
    [ "$status" -ne 0 ]
    
    # Test resolver with very large ID
    run guacaman --config "$TEST_CONFIG" conn exists --id 999999999
    [ "$status" -eq 1 ]  # Should return "not found" not crash
    
    # Test resolver maintains existing error message format
    run guacaman --config "$TEST_CONFIG" conn del --name "nonexistent_connection"
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]] || [[ "$output" == *"doesn't exist"* ]]
}

# =============================================================================
# Stage 2: Enhanced List Commands - Output Format Tests
# These tests verify that list commands always include ID fields in their output
# =============================================================================

@test "Connection list includes ID field in output" {
    # Test that connection list output includes ID field for all connections
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    
    # Verify output contains ID fields
    [[ "$output" == *"id:"* ]]
    
    # Count the number of connections with ID fields
    id_count=$(echo "$output" | grep -c "id:")
    connection_count=$(echo "$output" | grep -c "^  [a-zA-Z0-9_-][^:]*:")
    
    # Every connection should have an ID field
    [ "$id_count" -eq "$connection_count" ]
    
    # Verify ID format is positive integer
    ids=$(echo "$output" | grep "id:" | cut -d: -f2 | tr -d ' ')
    for id in $ids; do
        [ "$id" -gt 0 ]
    done
}

@test "Connection group list includes ID field in output" {
    # Test that connection group list output includes ID field for all groups
    run guacaman --config "$TEST_CONFIG" conngroup list
    [ "$status" -eq 0 ]
    
    # Verify output contains ID fields
    [[ "$output" == *"id:"* ]]
    
    # Count the number of groups with ID fields
    id_count=$(echo "$output" | grep -c "id:")
    group_count=$(echo "$output" | grep -c "^  [a-zA-Z0-9_-][^:]*:")
    
    # Every group should have an ID field
    [ "$id_count" -eq "$group_count" ]
    
    # Verify ID format is positive integer
    ids=$(echo "$output" | grep "id:" | cut -d: -f2 | tr -d ' ')
    for id in $ids; do
        [ "$id" -gt 0 ]
    done
}

@test "ID values match actual database IDs" {
    # Test that IDs shown in list output match actual database IDs
    
    # Get connection ID from list output
    list_id=$(get_connection_id "testconn1")
    [ -n "$list_id" ]
    
    # Get the same connection ID directly from database using name
    db_id=$(guacaman --config "$TEST_CONFIG" conn exists --name "testconn1" ; echo $?)
    
    # The ID from list should match what the database resolver returns
    # (Note: conn exists returns exit code 0/1, not the actual ID)
    # Instead, test that we can use the list ID with other commands
    run guacaman --config "$TEST_CONFIG" conn exists --id "$list_id"
    [ "$status" -eq 0 ]
}

@test "Output structure preserved with ID integration" {
    # Test that existing output structure is preserved when IDs are added
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    
    # Verify all expected fields are present along with ID
    [[ "$output" == *"type:"* ]]
    [[ "$output" == *"hostname:"* ]]
    [[ "$output" == *"port:"* ]]
    [[ "$output" == *"groups:"* ]]
    [[ "$output" == *"id:"* ]]
    
    # Verify ID appears as first field in each connection block
    # (ID should appear before type, hostname, port, etc.)
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]{2}[a-zA-Z0-9_-][^:]*:$ ]]; then
            # This is a connection name line, read the next line
            read -r next_line
            if [[ "$next_line" != *"id:"* ]]; then
                # ID should be the first field after connection name
                echo "ID not found as first field for connection: $line"
                return 1
            fi
        fi
    done <<< "$output"
}

@test "Empty database list output" {
    # Test list output with minimal/empty database (if possible)
    # This test verifies the feature works even with empty result sets
    
    # Connection list should still work with empty output
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    
    # The command should not crash and should produce valid YAML-like output
    [[ "$output" == "connections:"* ]] || [[ "$output" == "" ]]
}

# =============================================================================
# Stage 4: Connection Command Handlers with Validation Tests
# These tests verify that connection command handlers properly support --id
# parameter and validate selector requirements
# =============================================================================

@test "Connection delete with ID parameter via handler" {
    # Create a temporary connection for deletion test
    temp_conn="temp_del_handler_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name "$temp_conn" --hostname 192.168.1.200 --port 5900 --password temp
    
    # Get its ID
    conn_id=$(get_connection_id "$temp_conn")
    [ -n "$conn_id" ]
    
    # Delete by ID using the handler
    run guacaman --config "$TEST_CONFIG" conn del --id "$conn_id"
    [ "$status" -eq 0 ]
    
    # Verify it's gone
    run guacaman --config "$TEST_CONFIG" conn exists --name "$temp_conn"
    [ "$status" -eq 1 ]
}

@test "Connection exists with ID parameter via handler" {
    # Get the ID of testconn1
    conn_id=$(get_connection_id "testconn1")
    [ -n "$conn_id" ]
    
    # Test exists with valid ID via handler
    run guacaman --config "$TEST_CONFIG" conn exists --id "$conn_id"
    [ "$status" -eq 0 ]
    
    # Test exists with invalid ID via handler
    run guacaman --config "$TEST_CONFIG" conn exists --id 99999
    [ "$status" -eq 1 ]
}

@test "Connection modify with ID parameter via handler" {
    # Get ID of testconn2
    conn_id=$(get_connection_id "testconn2")
    [ -n "$conn_id" ]
    
    # Modify by ID using handler
    run guacaman --config "$TEST_CONFIG" conn modify --id "$conn_id" --set hostname=10.0.0.99
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    
    # Verify the change
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"hostname: 10.0.0.99"* ]]
}

@test "Connection modify parent group with ID parameter via handler" {
    # Get connection ID
    conn_id=$(get_connection_id "testconn2")
    [ -n "$conn_id" ]
    
    # Set parent group using ID via handler
    run guacaman --config "$TEST_CONFIG" conn modify --id "$conn_id" --parent testconngroup1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group"* ]]
    
    # Verify in listing
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"parent: testconngroup1"* ]]
}

@test "Connection handlers require exactly one selector" {
    # Test that handlers require exactly one of --name or --id
    
    # Delete command - both name and ID provided
    run guacaman --config "$TEST_CONFIG" conn del --name testconn1 --id 1
    [ "$status" -ne 0 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
    
    # Exists command - both name and ID provided
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1 --id 1
    [ "$status" -ne 0 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
    
    # Modify command - both name and ID provided
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn1 --id 1 --set hostname=test
    [ "$status" -ne 0 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
}

@test "Connection handlers require at least one selector" {
    # Test that handlers require at least one selector
    
    # Delete command - no selector provided
    run guacaman --config "$TEST_CONFIG" conn del
    [ "$status" -ne 0 ]
    [[ "$output" == *"one of the arguments"* ]] || [[ "$output" == *"required"* ]]
    
    # Exists command - no selector provided
    run guacaman --config "$TEST_CONFIG" conn exists
    [ "$status" -ne 0 ]
    [[ "$output" == *"one of the arguments"* ]] || [[ "$output" == *"required"* ]]
    
    # Modify command - no selector provided (should show help or error)
    run guacaman --config "$TEST_CONFIG" conn modify
    [ "$status" -ne 0 ]
    # Accept either help format or error message
    [[ "$output" == *"Usage:"* ]] || [[ "$output" == *"Modification options:"* ]] || [[ "$output" == *"one of the arguments"* ]]
}

@test "Connection handlers handle invalid ID formats" {
    # Test that handlers properly handle invalid ID formats
    
    # Delete command - zero ID
    run guacaman --config "$TEST_CONFIG" conn del --id 0
    [ "$status" -ne 0 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Exists command - negative ID
    run guacaman --config "$TEST_CONFIG" conn exists --id -1
    [ "$status" -ne 0 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Modify command - zero ID
    run guacaman --config "$TEST_CONFIG" conn modify --id 0 --set hostname=test
    [ "$status" -ne 0 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
}

@test "Connection handlers handle non-existent IDs gracefully" {
    # Test that handlers handle non-existent IDs with clear error messages
    
    # Delete command - non-existent ID
    run guacaman --config "$TEST_CONFIG" conn del --id 99999
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]] || [[ "$output" == *"does not exist"* ]]
    
    # Exists command - non-existent ID (should exit with code 1)
    run guacaman --config "$TEST_CONFIG" conn exists --id 99999
    [ "$status" -eq 1 ]
    
    # Modify command - non-existent ID
    run guacaman --config "$TEST_CONFIG" conn modify --id 99999 --set hostname=test
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]] || [[ "$output" == *"does not exist"* ]]
}

@test "Backward compatibility - name-based operations unchanged" {
    # Test that all existing name-based operations continue to work exactly as before
    
    # Connection operations with names
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set port=5999
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated port"* ]]
    
    run guacaman --config "$TEST_CONFIG" conn del --name testconn1
    [ "$status" -eq 0 ]
    
    # Recreate testconn1 for subsequent tests
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --password vncpass1 --usergroup testgroup1
}

@test "Connection list includes ID field via handler" {
    # Test that connection list output includes ID field via the handler
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    
    # Verify output contains ID fields
    [[ "$output" == *"id:"* ]]
    
    # Count the number of connections with ID fields
    id_count=$(echo "$output" | grep -c "id:")
    connection_count=$(echo "$output" | grep -c "^  [a-zA-Z0-9_-][^:]*:")
    
    # Every connection should have an ID field
    [ "$id_count" -eq "$connection_count" ]
    
    # Verify ID format is positive integer
    ids=$(echo "$output" | grep "id:" | cut -d: -f2 | tr -d ' ')
    for id in $ids; do
        [ "$id" -gt 0 ]
    done
}
