#!/usr/bin/env bats

# Global teardown function - called once after all tests complete
teardown() {
    # Clean up test objects
    guacaman --config "$TEST_CONFIG" conn del --name testconn1 || true
    guacaman --config "$TEST_CONFIG" conn del --name testconn2 || true
    guacaman --config "$TEST_CONFIG" user del --name testuser1 || true
    guacaman --config "$TEST_CONFIG" user del --name testuser2 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name testgroup1 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name testgroup2 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name parentgroup1 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name nested/parentgroup2 || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup1 || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup2 || true
}