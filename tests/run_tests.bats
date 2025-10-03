#!/usr/bin/env bats

# Main test runner that ensures setup runs once before all tests
# and teardown runs once after all tests

# Load setup and teardown functions
load setup.bats
load teardown.bats

# This file doesn't contain any tests itself, but ensures setup/teardown are called
# Individual test files will be loaded by the test runner in the correct order

# Helper functions that are used across multiple test files
get_connection_id() {
    local conn_name="$1"
    guacaman --config "$TEST_CONFIG" conn list | grep -A 1 "^  $conn_name:" | grep "id:" | cut -d: -f2 | tr -d ' '
}

get_conngroup_id() {
    local group_name="$1"
    guacaman --config "$TEST_CONFIG" conngroup list | grep -A 1 "^  $group_name:" | grep "id:" | cut -d: -f2 | tr -d ' '
}

get_usergroup_id() {
    local group_name="$1"
    guacaman --config "$TEST_CONFIG" usergroup list | grep -A 1 "^  $group_name:" | grep "id:" | cut -d: -f2 | tr -d ' '
}