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
    [[ "$output" == *"doesn't exist"* ]]
}

# Username validation tests

@test "Username validation: empty username should fail" {
    run guacaman --config "$TEST_CONFIG" user new --name "" --password testpass
    [ "$status" -eq 1 ]
    [[ "$output" == *"Username must be a non-empty string"* ]]
}

@test "Username validation: whitespace-only username should fail" {
    run guacaman --config "$TEST_CONFIG" user new --name "   " --password testpass
    [ "$status" -eq 1 ]
    [[ "$output" == *"cannot be empty or whitespace only"* ]]
}

@test "Username validation: invalid characters (colon) should fail" {
    run guacaman --config "$TEST_CONFIG" user new --name "test:user" --password testpass
    [ "$status" -eq 1 ]
    [[ "$output" == *"can only contain letters, numbers, underscore"* ]]
}

@test "Username validation: invalid characters (slash) should fail" {
    run guacaman --config "$TEST_CONFIG" user new --name "test/user" --password testpass
    [ "$status" -eq 1 ]
    [[ "$output" == *"can only contain letters, numbers, underscore"* ]]
}

@test "Username validation: invalid characters (space) should fail" {
    run guacaman --config "$TEST_CONFIG" user new --name "test user" --password testpass
    [ "$status" -eq 1 ]
    [[ "$output" == *"can only contain letters, numbers, underscore"* ]]
}

@test "Username validation: too long username should fail" {
    LONG_NAME=$(printf 'a%.0s' {1..129})
    run guacaman --config "$TEST_CONFIG" user new --name "$LONG_NAME" --password testpass
    [ "$status" -eq 1 ]
    [[ "$output" == *"exceeds maximum length of 128 characters"* ]]
}

@test "Username validation: exactly 128 characters should succeed" {
    LONG_NAME=$(printf 'a%.0s' {1..128})
    run guacaman --config "$TEST_CONFIG" user new --name "$LONG_NAME" --password testpass
    [ "$status" -eq 0 ]

    # Cleanup
    guacaman --config "$TEST_CONFIG" user del --name "$LONG_NAME" >/dev/null 2>&1 || true
}

@test "Username validation: valid characters (underscore, hyphen, period, at) should succeed" {
    run guacaman --config "$TEST_CONFIG" user new --name "test-user_123.name@test" --password testpass
    [ "$status" -eq 0 ]

    # Verify user exists
    run guacaman --config "$TEST_CONFIG" user exists --name "test-user_123.name@test"
    [ "$status" -eq 0 ]

    # Cleanup
    guacaman --config "$TEST_CONFIG" user del --name "test-user_123.name@test" >/dev/null 2>&1 || true
}

@test "Username validation: delete with empty username should fail" {
    run guacaman --config "$TEST_CONFIG" user del --name ""
    [ "$status" -eq 1 ]
    [[ "$output" == *"Username must be a non-empty string"* ]]
}

@test "Username validation: exists with empty username should fail" {
    run guacaman --config "$TEST_CONFIG" user exists --name ""
    [ "$status" -eq 1 ]
    [[ "$output" == *"Username must be a non-empty string"* ]]
}

@test "Username validation: modify with invalid characters should fail" {
    run guacaman --config "$TEST_CONFIG" user modify --name "test:user" --password newpass
    [ "$status" -eq 1 ]
    [[ "$output" == *"can only contain letters, numbers, underscore"* ]]
}