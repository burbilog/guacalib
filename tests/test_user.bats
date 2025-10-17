#!/usr/bin/env bats

# Load the main test runner which includes setup/teardown and helper functions
load run_tests.bats

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

@test "Create existing user should fail" {
    run guacaman --config "$TEST_CONFIG" user new --name testuser1 --password testpass1
    [ "$status" -ne 0 ]
    [[ "$output" == *"already exists"* ]]
}

@test "Delete non-existent user should fail" {
    run guacaman --config "$TEST_CONFIG" user del --name nonexistentuser
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}