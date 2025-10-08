#!/bin/bash

# Main test runner script that ensures setup runs once before all tests
# and teardown runs once after all tests

set -e

# Source the setup and teardown functions
source tests/setup.bats
source tests/teardown.bats

# Run setup once
setup

# Run individual test files in order
echo "Running usergroup tests..."
bats tests/test_usergroup.bats

echo "Running usergroup ID tests..."
bats tests/test_usergroup_ids.bats

echo "Running user tests..."
bats tests/test_user.bats

echo "Running connection tests..."
bats tests/test_connection.bats

echo "Running connection modify tests..."
bats tests/test_connection_modify.bats

echo "Running connection group tests..."
bats tests/test_conngroup.bats

echo "Running connection group add/rm connection tests..."
bats tests/test_conngroup_addconn_rmconn.bats

echo "Running connection group permit/deny tests..."
bats tests/test_conngroup_permit_deny.bats

echo "Running ID feature tests..."
bats tests/test_ids_feature.bats

echo "Running dump command tests..."
bats tests/test_dump.bats

# Run teardown once
teardown

echo "All tests completed successfully!"
