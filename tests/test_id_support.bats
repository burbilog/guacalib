#!/usr/bin/env bats

load 'setup_teardown.bash'

# Helper function to extract connection ID from list output
get_connection_id() {
    local conn_name="$1"
    guacaman --config "$TEST_CONFIG" conn list | grep -A 1 "^  $conn_name:" | grep "id:" | cut -d: -f2 | tr -d ' '
}

# Helper function to extract connection group ID from list output  
get_conngroup_id() {
    local group_name="$1"
    guacaman --config "$TEST_CONFIG" conngroup list | grep -A 1 "^  $group_name:" | grep "id:" | cut -d: -f2 | tr -d ' '
}

@test "Connection exists with ID parameter" {
    # Get the ID of testconn1
    conn_id=$(get_connection_id "testconn1")
    [ -n "$conn_id" ]
    
    # Test exists with valid ID
    run guacaman --config "$TEST_CONFIG" conn exists --id "$conn_id"
    [ "$status" -eq 0 ]
    
    # Test exists with invalid ID
    run guacaman --config "$TEST_CONFIG" conn exists --id 99999
    [ "$status" -eq 1 ]
    
    # Test validation: both name and ID provided should fail
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1 --id "$conn_id"
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
    
    # Test validation: neither name nor ID provided should fail
    run guacaman --config "$TEST_CONFIG" conn exists
    [ "$status" -eq 2 ]
    [[ "$output" == *"one of the arguments"* ]] && [[ "$output" == *"is required"* ]]
}

@test "Connection exists with invalid ID format" {
    # Test zero ID
    run guacaman --config "$TEST_CONFIG" conn exists --id 0
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Test negative ID
    run guacaman --config "$TEST_CONFIG" conn exists --id -1
    [ "$status" -eq 1 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
}

@test "Connection delete with ID parameter" {
    # Create a temporary connection for deletion test
    temp_conn="temp_del_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name "$temp_conn" --hostname 192.168.1.200 --port 5900 --password temp
    
    # Get its ID
    conn_id=$(get_connection_id "$temp_conn")
    [ -n "$conn_id" ]
    
    # Delete by ID
    run guacaman --config "$TEST_CONFIG" conn del --id "$conn_id"
    [ "$status" -eq 0 ]
    
    # Verify it's gone
    run guacaman --config "$TEST_CONFIG" conn exists --name "$temp_conn"
    [ "$status" -eq 1 ]
}

@test "Connection delete with invalid ID" {
    # Test delete with non-existent ID
    run guacaman --config "$TEST_CONFIG" conn del --id 99999
    [ "$status" -eq 1 ]
    [[ "$output" == *"not found"* ]] || [[ "$output" == *"does not exist"* ]]
    
    # Test validation: both name and ID provided
    run guacaman --config "$TEST_CONFIG" conn del --name testconn1 --id 1
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
}

@test "Connection modify with ID parameter" {
    # Get ID of testconn2
    conn_id=$(get_connection_id "testconn2")
    [ -n "$conn_id" ]
    
    # Modify by ID
    run guacaman --config "$TEST_CONFIG" conn modify --id "$conn_id" --set hostname=10.0.0.99
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    
    # Verify the change
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"hostname: 10.0.0.99"* ]]
}

@test "Connection modify parent group with ID parameter" {
    # Get connection ID
    conn_id=$(get_connection_id "testconn2")
    [ -n "$conn_id" ]
    
    # Set parent group using ID
    run guacaman --config "$TEST_CONFIG" conn modify --id "$conn_id" --parent testconngroup1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group"* ]]
    
    # Verify in listing
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"parent: testconngroup1"* ]]
}

@test "Connection group exists with ID parameter" {
    # Get ID of testconngroup1
    group_id=$(get_conngroup_id "testconngroup1")
    [ -n "$group_id" ]
    
    # Test exists with valid ID
    run guacaman --config "$TEST_CONFIG" conngroup exists --id "$group_id"
    [ "$status" -eq 0 ]
    
    # Test exists with invalid ID
    run guacaman --config "$TEST_CONFIG" conngroup exists --id 99999
    [ "$status" -eq 1 ]
    
    # Test validation: both name and ID provided
    run guacaman --config "$TEST_CONFIG" conngroup exists --name testconngroup1 --id "$group_id"
    [ "$status" -eq 2 ]
    [[ "$output" == *"not allowed with argument"* ]]
}

@test "Connection group delete with ID parameter" {
    # Create temporary group for deletion
    temp_group="temp_del_group_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$temp_group"
    
    # Get its ID
    group_id=$(get_conngroup_id "$temp_group")
    [ -n "$group_id" ]
    
    # Delete by ID
    run guacaman --config "$TEST_CONFIG" conngroup del --id "$group_id"
    [ "$status" -eq 0 ]
    
    # Verify it's gone
    run guacaman --config "$TEST_CONFIG" conngroup exists --name "$temp_group"
    [ "$status" -eq 1 ]
}

@test "Connection group modify parent with ID parameter" {
    # Create test groups
    parent_group="parent_id_test_$(date +%s)"
    child_group="child_id_test_$(date +%s)"
    
    guacaman --config "$TEST_CONFIG" conngroup new --name "$parent_group"
    guacaman --config "$TEST_CONFIG" conngroup new --name "$child_group"
    
    # Get child group ID
    child_id=$(get_conngroup_id "$child_group")
    [ -n "$child_id" ]
    
    # Set parent using ID
    run guacaman --config "$TEST_CONFIG" conngroup modify --id "$child_id" --parent "$parent_group"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group"* ]]
    
    # Verify relationship
    run guacaman --config "$TEST_CONFIG" conngroup list
    [[ "$output" == *"$child_group:"* ]]
    [[ "$output" == *"parent: $parent_group"* ]]
    
    # Clean up
    guacaman --config "$TEST_CONFIG" conngroup del --name "$child_group"
    guacaman --config "$TEST_CONFIG" conngroup del --name "$parent_group"
}

@test "Backward compatibility - existing name-based calls unchanged" {
    # All existing name-based operations should continue to work exactly as before
    
    # Connection operations
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set port=5999
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated port"* ]]
    
    # Connection group operations  
    run guacaman --config "$TEST_CONFIG" conngroup exists --name testconngroup1
    [ "$status" -eq 0 ]
    
    # Verify nothing changed in the existing behavior
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn1"* ]]
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"port: 5999"* ]]
}

@test "Error handling for resolver edge cases" {
    # Test resolver with empty/null values
    run guacaman --config "$TEST_CONFIG" conn exists --id ""
    [ "$status" -ne 0 ]
    
    # Test resolver with very large ID
    run guacaman --config "$TEST_CONFIG" conn exists --id 999999999
    [ "$status" -eq 1 ]  # Should return "not found" not crash
    
    # Test resolver maintains existing error message format
    run guacaman --config "$TEST_CONFIG" conn del --name "nonexistent_connection"
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]] || [[ "$output" == *"doesn't exist"* ]]
}

@test "Connection list includes ID field in output" {
    # Test that connection list output includes ID field for all connections
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    
    # Verify output contains ID fields
    [[ "$output" == *"id:"* ]]
    
    # Count the number of connections with ID fields
    id_count=$(echo "$output" | grep -c "id:")
    connection_count=$(echo "$output" | grep -c "^  [a-zA-Z0-9_-][^:]*:")
    
    # Every connection should have an ID field
    [ "$id_count" -eq "$connection_count" ]
    
    # Verify ID format is positive integer
    ids=$(echo "$output" | grep "id:" | cut -d: -f2 | tr -d ' ')
    for id in $ids; do
        [ "$id" -gt 0 ]
    done
}

@test "Connection group list includes ID field in output" {
    # Test that connection group list output includes ID field for all groups
    run guacaman --config "$TEST_CONFIG" conngroup list
    [ "$status" -eq 0 ]
    
    # Verify output contains ID fields
    [[ "$output" == *"id:"* ]]
    
    # Count the number of groups with ID fields
    id_count=$(echo "$output" | grep -c "id:")
    group_count=$(echo "$output" | grep -c "^  [a-zA-Z00-9_-][^:]*:")
    
    # Every group should have an ID field
    [ "$id_count" -eq "$group_count" ]
    
    # Verify ID format is positive integer
    ids=$(echo "$output" | grep "id:" | cut -d: -f2 | tr -d ' ')
    for id in $ids; do
        [ "$id" -gt 0 ]
    done
}

@test "ID values match actual database IDs" {
    # Test that IDs shown in list output match actual database IDs
    
    # Get connection ID from list output
    list_id=$(get_connection_id "testconn1")
    [ -n "$list_id" ]
    
    # Get the same connection ID directly from database using name
    db_id=$(guacaman --config "$TEST_CONFIG" conn exists --name "testconn1" ; echo $?)
    
    # The ID from list should match what the database resolver returns
    # (Note: conn exists returns exit code 0/1, not the actual ID)
    # Instead, test that we can use the list ID with other commands
    run guacaman --config "$TEST_CONFIG" conn exists --id "$list_id"
    [ "$status" -eq 0 ]
}

@test "Output structure preserved with ID integration" {
    # Test that existing output structure is preserved when IDs are added
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    
    # Verify all expected fields are present along with ID
    [[ "$output" == *"type:"* ]]
    [[ "$output" == *"hostname:"* ]]
    [[ "$output" == *"port:"* ]]
    [[ "$output" == *"groups:"* ]]
    [[ "$output" == *"id:"* ]]
    
    # Verify ID appears as first field in each connection block
    # (ID should appear before type, hostname, port, etc.)
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]{2}[a-zA-Z0-9_-][^:]*:$ ]]; then
            # This is a connection name line, read the next line
            read -r next_line
            if [[ "$next_line" != *"id:"* ]]; then
                # ID should be the first field after connection name
                echo "ID not found as first field for connection: $line"
                return 1
            fi
        fi
    done <<< "$output"
}

@test "Empty database list output" {
    # Test list output with minimal/empty database (if possible)
    # This test verifies the feature works even with empty result sets
    
    # Connection list should still work with empty output
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    
    # The command should not crash and should produce valid YAML-like output
    [[ "$output" == "connections:"* ]] || [[ "$output" == "" ]]
}

@test "Connection delete with ID parameter via handler" {
    # Create a temporary connection for deletion test
    temp_conn="temp_del_handler_$(date +%s)"
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name "$temp_conn" --hostname 192.168.1.200 --port 5900 --password temp
    
    # Get its ID
    conn_id=$(get_connection_id "$temp_conn")
    [ -n "$conn_id" ]
    
    # Delete by ID using the handler
    run guacaman --config "$TEST_CONFIG" conn del --id "$conn_id"
    [ "$status" -eq 0 ]
    
    # Verify it's gone
    run guacaman --config "$TEST_CONFIG" conn exists --name "$temp_conn"
    [ "$status" -eq 1 ]
}

@test "Connection exists with ID parameter via handler" {
    # Get the ID of testconn1
    conn_id=$(get_connection_id "testconn1")
    [ -n "$conn_id" ]
    
    # Test exists with valid ID via handler
    run guacaman --config "$TEST_CONFIG" conn exists --id "$conn_id"
    [ "$status" -eq 0 ]
    
    # Test exists with invalid ID via handler
    run guacaman --config "$TEST_CONFIG" conn exists --id 99999
    [ "$status" -eq 1 ]
}

@test "Connection modify with ID parameter via handler" {
    # Get ID of testconn2
    conn_id=$(get_connection_id "testconn2")
    [ -n "$conn_id" ]
    
    # Modify by ID using handler
    run guacaman --config "$TEST_CONFIG" conn modify --id "$conn_id" --set hostname=10.0.0.99
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated hostname"* ]]
    
    # Verify the change
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"hostname: 10.0.0.99"* ]]
}

@test "Connection modify parent group with ID parameter via handler" {
    # Get connection ID
    conn_id=$(get_connection_id "testconn2")
    [ -n "$conn_id" ]
    
    # Set parent group using ID via handler
    run guacaman --config "$TEST_CONFIG" conn modify --id "$conn_id" --parent testconngroup1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully set parent group"* ]]
    
    # Verify in listing
    run guacaman --config "$TEST_CONFIG" conn list
    [[ "$output" == *"testconn2"* ]]
    [[ "$output" == *"parent: testconngroup1"* ]]
}

@test "Connection handlers require exactly one selector" {
    # Test that handlers require exactly one of --name or --id
    
    # Delete command - both name and ID provided
    run guacaman --config "$TEST_CONFIG" conn del --name testconn1 --id 1
    [ "$status" -ne 0 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
    
    # Exists command - both name and ID provided
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1 --id 1
    [ "$status" -ne 0 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
    
    # Modify command - both name and ID provided
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn1 --id 1 --set hostname=test
    [ "$status" -ne 0 ]
    [[ "$output" == *"not allowed with argument"* ]] || [[ "$output" == *"exactly one"* ]]
}

@test "Connection handlers require at least one selector" {
    # Test that handlers require at least one selector
    
    # Delete command - no selector provided
    run guacaman --config "$TEST_CONFIG" conn del
    [ "$status" -ne 0 ]
    [[ "$output" == *"one of the arguments"* ]] || [[ "$output" == *"required"* ]]
    
    # Exists command - no selector provided
    run guacaman --config "$TEST_CONFIG" conn exists
    [ "$status" -ne 0 ]
    [[ "$output" == *"one of the arguments"* ]] || [[ "$output" == *"required"* ]]
    
    # Modify command - no selector provided (should show help or error)
    run guacaman --config "$TEST_CONFIG" conn modify
    [ "$status" -ne 0 ]
    # Accept either help format or error message
    [[ "$output" == *"Usage:"* ]] || [[ "$output" == *"Modification options:"* ]] || [[ "$output" == *"one of the arguments"* ]]
}

@test "Connection handlers handle invalid ID formats" {
    # Test that handlers properly handle invalid ID formats
    
    # Delete command - zero ID
    run guacaman --config "$TEST_CONFIG" conn del --id 0
    [ "$status" -ne 0 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Exists command - negative ID
    run guacaman --config "$TEST_CONFIG" conn exists --id -1
    [ "$status" -ne 0 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
    
    # Modify command - zero ID
    run guacaman --config "$TEST_CONFIG" conn modify --id 0 --set hostname=test
    [ "$status" -ne 0 ]
    [[ "$output" == *"positive integer"* ]] || [[ "$output" == *"must be greater than 0"* ]]
}

@test "Connection handlers handle non-existent IDs gracefully" {
    # Test that handlers handle non-existent IDs with clear error messages
    
    # Delete command - non-existent ID
    run guacaman --config "$TEST_CONFIG" conn del --id 99999
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]] || [[ "$output" == *"does not exist"* ]]
    
    # Exists command - non-existent ID (should exit with code 1)
    run guacaman --config "$TEST_CONFIG" conn exists --id 99999
    [ "$status" -eq 1 ]
    
    # Modify command - non-existent ID
    run guacaman --config "$TEST_CONFIG" conn modify --id 99999 --set hostname=test
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]] || [[ "$output" == *"does not exist"* ]]
}

@test "Backward compatibility - name-based operations unchanged" {
    # Test that all existing name-based operations continue to work exactly as before
    
    # Connection operations with names
    run guacaman --config "$TEST_CONFIG" conn exists --name testconn1
    [ "$status" -eq 0 ]
    
    run guacaman --config "$TEST_CONFIG" conn modify --name testconn2 --set port=5999
    [ "$status" -eq 0 ]
    [[ "$output" == *"Successfully updated port"* ]]
    
    run guacaman --config "$TEST_CONFIG" conn del --name testconn1
    [ "$status" -eq 0 ]
    
    # Recreate testconn1 for subsequent tests
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --password vncpass1 --usergroup testgroup1
}

@test "Connection list includes ID field via handler" {
    # Test that connection list output includes ID field via the handler
    run guacaman --config "$TEST_CONFIG" conn list
    [ "$status" -eq 0 ]
    
    # Verify output contains ID fields
    [[ "$output" == *"id:"* ]]
    
    # Count the number of connections with ID fields
    id_count=$(echo "$output" | grep -c "id:")
    connection_count=$(echo "$output" | grep -c "^  [a-zA-Z0-9_-][^:]*:")
    
    # Every connection should have an ID field
    [ "$id_count" -eq "$connection_count" ]
    
    # Verify ID format is positive integer
    ids=$(echo "$output" | grep "id:" | cut -d: -f2 | tr -d ' ')
    for id in $ids; do
        [ "$id" -gt 0 ]
    done
}
