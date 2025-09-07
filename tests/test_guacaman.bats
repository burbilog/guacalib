#!/usr/bin/env bats

# =============================================================================
# Stage UG-T: User Group ID Support - Parser and Selector Validation Tests
# =============================================================================
# This file keeps only the unique usergroup parser/selector validation tests to
# avoid duplication with other suite files.

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
