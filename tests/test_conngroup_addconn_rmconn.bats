#!/usr/bin/env bats

# Test file for conngroup modify addconn/rmconn functionality
# Target: ~8 core test cases for single connection per operation

@test "conngroup modify help shows new parameter - should fail initially" {
    run guacaman conngroup modify --help
    [ "$status" -eq 0 ]
    # Check if help shows new parameters (will fail initially)
    [[ "$output" =~ "--addconn-by-name" ]] || [[ "$output" =~ "--rmconn-by-name" ]]
}

@test "add connection to group by name - should fail initially" {
    # Setup: create test group and connection
    TEST_GROUP="test_add_conn_group_$(date +%s)"
    TEST_CONN="test_conn_$(date +%s)"

    guacaman conngroup new --name "$TEST_GROUP"
    guacaman conn new --name "$TEST_CONN" --type vnc --hostname 127.0.0.1 --port 5900 --password test123

    # Test add connection by name
    run guacaman conngroup modify --name "$TEST_GROUP" --addconn-by-name "$TEST_CONN"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Added connection" ]]

    # Cleanup
    guacaman conngroup del --name "$TEST_GROUP"
    guacaman conn del --name "$TEST_CONN"
}

@test "add connection to group by id - should fail initially" {
    # Setup: create test group and connection, get their IDs
    TEST_GROUP="test_add_conn_group_id_$(date +%s)"
    TEST_CONN="test_conn_id_$(date +%s)"

    guacaman conngroup new --name "$TEST_GROUP"
    guacaman conn new --name "$TEST_CONN" --type vnc --hostname 127.0.0.1 --port 5900 --password test123

    GROUP_ID=$(guacaman conngroup list | grep "$TEST_GROUP" -A1 | grep "id:" | awk '{print $2}')
    CONN_ID=$(guacaman conn list | grep "$TEST_CONN" -A1 | grep "id:" | awk '{print $2}')

    # Test add connection by ID
    run guacaman conngroup modify --id "$GROUP_ID" --addconn-by-id "$CONN_ID"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Added connection" ]]

    # Cleanup
    guacaman conngroup del --id "$GROUP_ID"
    guacaman conn del --id "$CONN_ID"
}

@test "remove connection from group by name - should fail initially" {
    # Setup: create group, add connection to it
    TEST_GROUP="test_rm_conn_group_$(date +%s)"
    TEST_CONN="test_rm_conn_$(date +%s)"

    guacaman conngroup new --name "$TEST_GROUP"
    guacaman conn new --name "$TEST_CONN" --type vnc --hostname 127.0.0.1 --port 5900 --password test123

    # Add connection to group first
    guacaman conngroup modify --name "$TEST_GROUP" --addconn-by-name "$TEST_CONN" 2>/dev/null || true

    # Test remove connection by name
    run guacaman conngroup modify --name "$TEST_GROUP" --rmconn-by-name "$TEST_CONN"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Removed connection" ]]

    # Cleanup
    guacaman conngroup del --name "$TEST_GROUP"
    guacaman conn del --name "$TEST_CONN"
}

@test "remove connection from group by id - should fail initially" {
    # Setup: create group, add connection to it, get IDs
    TEST_GROUP="test_rm_conn_group_id_$(date +%s)"
    TEST_CONN="test_rm_conn_id_$(date +%s)"

    guacaman conngroup new --name "$TEST_GROUP"
    guacaman conn new --name "$TEST_CONN" --type vnc --hostname 127.0.0.1 --port 5900 --password test123

    GROUP_ID=$(guacaman conngroup list | grep "$TEST_GROUP" -A1 | grep "id:" | awk '{print $2}')
    CONN_ID=$(guacaman conn list | grep "$TEST_CONN" -A1 | grep "id:" | awk '{print $2}')

    # Add connection to group first
    guacaman conngroup modify --id "$GROUP_ID" --addconn-by-id "$CONN_ID" 2>/dev/null || true

    # Test remove connection by ID
    run guacaman conngroup modify --id "$GROUP_ID" --rmconn-by-id "$CONN_ID"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Removed connection" ]]

    # Cleanup
    guacaman conngroup del --id "$GROUP_ID"
    guacaman conn del --id "$CONN_ID"
}

@test "fail to add non-existent connection - should fail initially" {
    TEST_GROUP="test_add_nonexistent_$(date +%s)"
    guacaman conngroup new --name "$TEST_GROUP"

    run guacaman conngroup modify --name "$TEST_GROUP" --addconn-by-name "nonexistent_conn"
    [ "$status" -eq 1 ]
    [[ "$output" =~ "not found" ]]

    guacaman conngroup del --name "$TEST_GROUP"
}

@test "fail to operate on non-existent group - should fail initially" {
    TEST_CONN="test_conn_group_$(date +%s)"
    guacaman conn new --name "$TEST_CONN" --type vnc --hostname 127.0.0.1 --port 5900 --password test123

    run guacaman conngroup modify --name "nonexistent_group" --addconn-by-name "$TEST_CONN"
    [ "$status" -eq 1 ]
    [[ "$output" =~ "not found" ]]

    guacaman conn del --name "$TEST_CONN"
}

@test "mutual exclusion between add and remove parameters - should fail initially" {
    TEST_GROUP="test_mutual_exclusion_$(date +%s)"
    guacaman conngroup new --name "$TEST_GROUP"

    # Try to use both add and remove in same command (should fail)
    run guacaman conngroup modify --name "$TEST_GROUP" --addconn-by-name "conn1" --rmconn-by-name "conn2"
    [ "$status" -eq 2 ]
    [[ "$output" =~ "not allowed with argument" ]]

    guacaman conngroup del --name "$TEST_GROUP"
}