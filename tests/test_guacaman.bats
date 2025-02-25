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
    guacaman --config "$TEST_CONFIG" user new --name testuser1 --password testpass1 --group testgroup1,testgroup2
    guacaman --config "$TEST_CONFIG" user new --name testuser2 --password testpass2
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --vnc-password vncpass1 --group testgroup1
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn2 --hostname 192.168.1.101 --port 5902 --vnc-password vncpass2
    guacaman --config "$TEST_CONFIG" usergroup new --name parentgroup1
    guacaman --config "$TEST_CONFIG" usergroup new --name nested/parentgroup2
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
    run guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --vnc-password vncpass1
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
    [ "$status" -eq 1 ]
    [[ "$output" == *"Modifiable connection parameters"* ]]
    [[ "$output" == *"Parameters in guacamole_connection table"* ]]
    [[ "$output" == *"Parameters in guacamole_connection_parameter table"* ]]
    [[ "$output" == *"max_connections"* ]]
    [[ "$output" == *"max_connections_per_user"* ]]
    [[ "$output" == *"hostname"* ]]
    [[ "$output" == *"port"* ]]
    [[ "$output" == *"password"* ]]
    [[ "$output" == *"read-only"* ]]
}

@test "Connection modify hostname parameter" {
    # Modify the hostname
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set hostname=10.1.1.10
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    
    # Verify the change in the connection listing
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"hostname: 10.1.1.10"* ]]
}

@test "Connection modify port parameter" {
    # Modify the port
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set port=5910
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated port"* ]]
    
    # Verify the change in the connection listing
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"port: 5910"* ]]
}

@test "Connection modify password parameter" {
    # Modify the password
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set password=newvncpass
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated password"* ]]
}

@test "Connection modify read-only parameter" {
    # Set read-only to true
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set read-only=true
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Set read-only to false
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set read-only=false
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Invalid value should fail
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set read-only=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be 'true' or 'false'"* ]]
}

@test "Connection modify max_connections parameter" {
    # Modify max_connections
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set max_connections=5
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated max_connections"* ]]
    
    # Invalid value should fail
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set max_connections=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be an integer"* ]]
}

@test "Connection modify max_connections_per_user parameter" {
    # Modify max_connections_per_user
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set max_connections_per_user=3
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated max_connections_per_user"* ]]
    
    # Invalid value should fail
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set max_connections_per_user=invalid
    [ "$status" -ne 0 ]
    [[ "$output" == *"must be an integer"* ]]
}

@test "Connection modify multiple parameters at once" {
    # Modify multiple parameters
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set hostname=192.168.2.100 --set port=5905 --set read-only=true
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    [[ "$output" == *"Successfully updated port"* ]]
    [[ "$output" == *"Successfully updated read-only"* ]]
    
    # Verify the changes in the connection listing
    run guacaman --config "$TEST_CONFIG" conn list
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
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set-parent-group parentgroup1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to 'parentgroup1'"* ]]
    
    # Verify in connection list
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"groups:"* ]]
    [[ "$output" == *"- parentgroup1"* ]]
}

@test "Connection modify set nested parent group" {
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set-parent-group nested/parentgroup2
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to 'nested/parentgroup2'"* ]]
    
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"- nested/parentgroup2"* ]]
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

@test "Connection modify remove parent group" {
    # First set a group
    guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set-parent-group parentgroup1
    # Then remove it
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set-parent-group ""
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group to ''"* ]]
    
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" != *"parentgroup1"* ]]
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
    [[ "$output" == *"vnc-connections:"* ]]
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
