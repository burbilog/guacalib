#!/usr/bin/env bats

# Main test runner that ensures setup runs once before all tests
# and teardown runs once after all tests

# Load setup and teardown functions
load setup.bats
load teardown.bats

# Run individual test files in order
@test "Run usergroup tests" {
    bats tests/test_usergroup.bats
}

@test "Run user tests" {
    bats tests/test_user.bats
}

@test "Run connection tests" {
    bats tests/test_connection.bats
}

@test "Run connection modify tests" {
    bats tests/test_connection_modify.bats
}

@test "Run connection group tests" {
    bats tests/test_conngroup.bats
}

@test "Run ID feature tests" {
    bats tests/test_ids_feature.bats
}

@test "Run dump command tests" {
    bats tests/test_dump.bats
}