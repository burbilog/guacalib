#!/usr/bin/env bats

load 'setup_teardown.bash'

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
