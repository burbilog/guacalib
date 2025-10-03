#!/usr/bin/env bats

# Load the main test runner which includes setup/teardown and helper functions
load run_tests.bats

# Usergroup ID feature tests



@test "Stage UG-01: Usergroup exists with ID parameter - parser validation" {
    # Test validation: both name and ID provided should fail
    run guacaman --config "$TEST_CONFIG" usergroup exists --name testgroup1 --id 1
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
    
    # Test validation: neither name nor ID provided should fail
    run guacaman --config "$TEST_CONFIG" usergroup exists
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments"* ]] && [[ "$output" == *"is required"* ]]
    
    # Test exists with invalid ID format - zero
    run guacaman --config "$TEST_CONFIG" usergroup exists --id 0
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Test exists with invalid ID format - negative
    run guacaman --config "$TEST_CONFIG" usergroup exists --id -1
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Test exists with invalid ID (non-existent)
    run guacaman --config "$TEST_CONFIG" usergroup exists --id 99999
    [ "$status" -eq 1 ]
}

@test "Stage UG-01: Usergroup delete with ID parameter - parser validation" {
    # Test validation: both name and ID provided should fail
    run guacaman --config "$TEST_CONFIG" usergroup del --name testgroup1 --id 1
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
    
    # Test validation: neither name nor ID provided should fail
    run guacaman --config "$TEST_CONFIG" usergroup del
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments"* ]] && [[ "$output" == *"is required"* ]]
    
    # Test delete with invalid ID format - zero
    run guacaman --config "$TEST_CONFIG" usergroup del --id 0
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Test delete with invalid ID format - negative
    run guacaman --config "$TEST_CONFIG" usergroup del --id -1
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Test delete with invalid ID (non-existent)
    run guacaman --config "$TEST_CONFIG" usergroup del --id 99999
    [ "$status" -eq 1 ]
}

@test "Stage UG-01: Usergroup modify with ID parameter - parser validation" {
    # Test validation: both name and ID provided should fail
    run guacaman --config "$TEST_CONFIG" usergroup modify --name testgroup1 --id 1 --adduser testuser1
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
    
    # Test validation: neither name nor ID provided should fail
    run guacaman --config "$TEST_CONFIG" usergroup modify --adduser testuser1
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments"* ]] && [[ "$output" == *"is required"* ]]
    
    # Test modify with invalid ID format - zero
    run guacaman --config "$TEST_CONFIG" usergroup modify --id 0 --adduser testuser1
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Test modify with invalid ID format - negative
    run guacaman --config "$TEST_CONFIG" usergroup modify --id -1 --adduser testuser1
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Test modify with invalid ID (non-existent)
    run guacaman --config "$TEST_CONFIG" usergroup modify --id 99999 --adduser testuser1
    [ "$status" -eq 1 ]
}

@test "Stage UG-02: Usergroup exists with ID parameter - functional test" {
    # Create a temporary usergroup for testing
    temp_usergroup="temp_exists_$(date +%s)"
    guacaman --config "$TEST_CONFIG" usergroup new --name "$temp_usergroup"
    
    # Get the ID of the temporary usergroup using the helper function
    temp_id=$(get_usergroup_id "$temp_usergroup")
    [ -n "$temp_id" ]
    
    # Test exists with valid ID
    run guacaman --config "$TEST_CONFIG" usergroup exists --id "$temp_id"
    [ "$status" -eq 0 ]
    
    # Test exists with invalid ID
    run guacaman --config "$TEST_CONFIG" usergroup exists --id 99999
    [ "$status" -eq 1 ]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" usergroup del --name "$temp_usergroup"
}

@test "Stage UG-03: Usergroup delete with ID parameter - functional test" {
    # Create a temporary usergroup for deletion test
    temp_usergroup="temp_del_$(date +%s)"
    guacaman --config "$TEST_CONFIG" usergroup new --name "$temp_usergroup"
    
    # Get the ID of the temporary usergroup
    temp_id=$(get_usergroup_id "$temp_usergroup")
    [ -n "$temp_id" ]
    
    # Test delete with valid ID
    run guacaman --config "$TEST_CONFIG" usergroup del --id "$temp_id"
    [ "$status" -eq 0 ]
    
    # Verify usergroup no longer exists
    run guacaman --config "$TEST_CONFIG" usergroup exists --id "$temp_id"
    [ "$status" -eq 1 ]
}

@test "Stage UG-04: Usergroup modify with ID parameter - functional test" {
    # Create a temporary usergroup for modification test
    temp_usergroup="temp_mod_$(date +%s)"
    guacaman --config "$TEST_CONFIG" usergroup new --name "$temp_usergroup"
    
    # Get the ID of the temporary usergroup
    temp_id=$(get_usergroup_id "$temp_usergroup")
    [ -n "$temp_id" ]
    
    # Test modify with valid ID - add a member
    run guacaman --config "$TEST_CONFIG" usergroup modify --id "$temp_id" --adduser testuser1
    [ "$status" -eq 0 ]
    
    # Test modify with valid ID - remove a member
    run guacaman --config "$TEST_CONFIG" usergroup modify --id "$temp_id" --rmuser testuser1
    [ "$status" -eq 0 ]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" usergroup del --name "$temp_usergroup"
}

