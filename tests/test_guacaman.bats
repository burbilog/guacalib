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
    guacaman --config "$TEST_CONFIG" group new --name testgroup1
    guacaman --config "$TEST_CONFIG" group new --name testgroup2
    guacaman --config "$TEST_CONFIG" user new --name testuser1 --password testpass1 --group testgroup1,testgroup2
    guacaman --config "$TEST_CONFIG" user new --name testuser2 --password testpass2
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --vnc-password vncpass1 --group testgroup1
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn2 --hostname 192.168.1.101 --port 5902 --vnc-password vncpass2
}

teardown() {
    # Clean up test objects
    guacaman --config "$TEST_CONFIG" conn del --name testconn1 || true
    guacaman --config "$TEST_CONFIG" conn del --name testconn2 || true
    guacaman --config "$TEST_CONFIG" user del --name testuser1 || true
    guacaman --config "$TEST_CONFIG" user del --name testuser2 || true
    guacaman --config "$TEST_CONFIG" group del --name testgroup1 || true
    guacaman --config "$TEST_CONFIG" group del --name testgroup2 || true
}

@test "Group creation and existence" {
    run guacaman --config "$TEST_CONFIG" group exists --name testgroup1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" group exists --name testgroup2
    [ "$status" -eq 0 ]
}

@test "Group listing" {
    run guacaman --config "$TEST_CONFIG" group list
    [ "$status" -eq 0 ]
    [[ "$output" == *"testgroup1"* ]]
    [[ "$output" == *"testgroup2"* ]]
}

@test "Group deletion" {
    run guacaman --config "$TEST_CONFIG" group del --name testgroup1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" group exists --name testgroup1
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

@test "Create existing group should fail" {
    run guacaman --config "$TEST_CONFIG" group new --name testgroup1
    [ "$status" -ne 0 ]
    [[ "$output" == *"already exists"* ]]
}

@test "Delete non-existent group should fail" {
    run guacaman --config "$TEST_CONFIG" group del --name nonexistentgroup
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
    
    # Verify relationships with more flexible matching
    echo "$output" | grep -Pzo 'testuser1:.*?(\n\s+- testgroup1.*?)+(\n\s+- testgroup2.*?)+' 
    echo "$output" | grep -Pzo 'testconn1:.*?(\n\s+- testgroup1.*?)+'
}
