#!/usr/bin/env bats

# Connection modify tests

setup() {
    # Create test objects specifically for modify tests
    guacaman --config "$TEST_CONFIG" conngroup new --name testconngroup_modify1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" conngroup new --name testconngroup_modify2 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" user new --name testuser_modify --password testpass_modify 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" user new --name testuser1 --password testpass1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn_modify --hostname 192.168.1.102 --port 5903 --password vncpass_modify
}

teardown() {
    # Clean up the test objects
    guacaman --config "$TEST_CONFIG" conn del --name testconn_modify 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" user del --name testuser_modify 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" user del --name testuser1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup_modify1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup_modify2 2>/dev/null || true
}

@test "Connection modify command shows parameters" {
    run guacaman --config "$TEST_CONFIG" conn modify
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments --name --id is required"* ]]
}

@test "Connection modify hostname parameter" {
    # Modify the hostname
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set hostname=10.1.1.10
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    
    # Verify the change in the connection listing
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn_modify"* ]]
    [[ "$output" == *"hostname: 10.1.1.10"* ]]
}

@test "Connection modify port parameter" {
    # Modify the port
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set port=5910
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated port"* ]]
    
    # Verify the change in the connection listing
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn_modify"* ]]
    [[ "$output" == *"port: 5910"* ]]
}

@test "Connection modify password parameter" {
    # Modify the password
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set password=newvncpass
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated password"* ]]
}

@test "Connection modify read-only parameter" {
    # Set read-only to true
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set read-only=true
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Set read-only to false
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set read-only=false
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Invalid value should fail
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set read-only=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be 'true' or 'false'"* ]]
}

@test "Connection modify max_connections parameter" {
    # Modify max_connections
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set max_connections=5
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated max_connections"* ]]
    
    # Invalid value should fail
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set max_connections=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be an integer"* ]]
}

@test "Connection modify max_connections_per_user parameter" {
    # Modify max_connections_per_user
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set max_connections_per_user=3
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated max_connections_per_user"* ]]
    
    # Invalid value should fail
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set max_connections_per_user=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be an integer"* ]]
}

@test "Connection modify multiple parameters at once" {
    # Modify multiple parameters
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --set hostname=192.168.2.100 --set port=5905 --set read-only=true
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    [[ "$output" == *"Successfully updated port"* ]]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Verify the changes in the connection listing
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn_modify"* ]]
    [[ "$output" == *"hostname: 192.168.2.100"* ]]
    [[ "$output" == *"port: 5905"* ]]
}

@test "Connection modify non-existent connection should fail" {
    run guacaman --config "$TEST_CONFIG" conn modify --name nonexistentconn --set hostname=10.1.1.10
    [ "$status" -ne 0 ]
    [[ "$output" == *"doesn't exist"* ]]
}

@test "Connection modify invalid parameter should fail" {
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn_modify --set invalid_param=value
    [ "$status" -ne 0 ]
    [[ "$output" == *"Invalid parameter"* ]]
}

@test "Connection modify set parent group" {
    # Set parent group
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --parent testconngroup_modify1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to 'testconngroup_modify1'"* ]]
    
    # Verify in connection list
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn_modify"* ]]
    [[ "$output" == *"parent: testconngroup_modify1"* ]]
}

@test "Connection modify remove parent group" {
    # First set a group
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --parent testconngroup_modify2
    [ "$status" -eq 0 ]
    # Then remove it
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --parent ""
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to ''"* ]]
    
    run guacaman --debug --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn_modify"* ]]
    [[ "$output" != *"testconngroup_modify2"* ]]
}

@test "Connection modify set nested parent group" {
    
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --parent testconngroup_modify2
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to 'testconngroup_modify2'"* ]]
    
    run guacaman --debug --config "$TEST_CONFIG" conn list
    echo "$output" > /tmp/testconn_modify.txt
    [[ "$output" == *"testconn_modify"* ]]
    [[ "$output" == *"parent: testconngroup_modify2"* ]]
    
}

@test "Connection modify grant permission to user" {
    # Grant permission
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --permit testuser1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully granted permission to user 'testuser1' for connection 'testconn_modify'"* ]]

    # Verify permission exists
    run guacaman --debug --config "$TEST_CONFIG" dump
    [[ "$output" == *"testconn_modify:"* ]]
    [[ "$output" == *"permissions:"* ]]
    [[ "$output" == *"- testuser1"* ]]
}

@test "Connection modify grant permission to already permitted user should fail" {
    # First grant permission
    guacaman --config "$TEST_CONFIG" conn modify --name testconn_modify --permit testuser1
    
    # Try to grant again
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --permit testuser1
    [ "$status" -ne 0 ]
    [[ "$output" == *"already has permission"* ]]
}

@test "Connection modify revoke permission from user" {
    # First grant permission
    guacaman --config "$TEST_CONFIG" conn modify --name testconn_modify --permit testuser1
    
    # Revoke permission
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --deny testuser1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully revoked permission from user 'testuser1' for connection 'testconn_modify'"* ]]

    # Verify permission is gone - updated to check that testuser1 isn't listed under permissions rather than
    # checking for the absence of the permissions: section entirely
    run guacaman --debug --config "$TEST_CONFIG" dump
    [[ "$output" == *"testconn_modify:"* ]]
    # Don't check for absence of permissions section anymore:
    # [[ "$output" != *"permissions:"* ]]
    # Instead, verify the specific user isn't listed
    [[ ! $(echo "$output" | grep -A10 "testconn_modify:" | grep -A5 "permissions:" | grep "testuser1") ]]
}

@test "Connection modify grant permission to non-existent user should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --permit nonexistentuser
    [ "$status" -ne 0 ]
    [[ "$output" == *"doesn't exist"* ]]
}

@test "Connection modify revoke permission from non-existent user should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name testconn_modify --deny nonexistentuser
    [ "$status" -ne 0 ]
    [[ "$output" == *"doesn't exist"* ]]
}

@test "Connection modify grant permission to non-existent connection should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name nonexistentconn --permit testuser1
    [ "$status" -ne 0 ]
    [[ "$output" == *"doesn't exist"* ]]
}

@test "Connection modify revoke permission from non-existent connection should fail" {
    run guacaman --debug --config "$TEST_CONFIG" conn modify --name nonexistentconn --deny testuser1
    [ "$status" -ne 0 ]
    [[ "$output" == *"doesn't exist"* ]]
}