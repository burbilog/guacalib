#!/usr/bin/env bats

load 'setup_teardown.bash'

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
