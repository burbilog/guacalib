#!/usr/bin/env bats

# Load the main test runner which includes setup/teardown and helper functions
load run_tests.bats

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

@test "Create existing connection should fail" {
    run guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --password vncpass1
    [ "$status" -ne 0 ]
    [[ "$output" == *"already exists"* ]]
}

@test "Delete non-existent connection should fail" {
    run guacaman --config "$TEST_CONFIG" conn del --name nonexistentconn
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

