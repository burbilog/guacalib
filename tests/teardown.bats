#!/usr/bin/env bats

# Function to clean up all timestamp-based test entries
cleanup_timestamped_entries() {
    # Clean up test connection groups with timestamp patterns
    guacaman --config "$TEST_CONFIG" conngroup list 2>/dev/null | grep -E "test_[a-zA-Z_]+_[0-9]{10}:" | cut -d: -f1 | while read -r group; do
        [ -n "$group" ] && guacaman --config "$TEST_CONFIG" conngroup del --name "$group" 2>/dev/null || true
    done

    # Clean up test connections with timestamp patterns
    guacaman --config "$TEST_CONFIG" conn list 2>/dev/null | grep -E "  test_[a-zA-Z_]+_[0-9]{10}:" | cut -d: -f1 | tr -d ' ' | while read -r conn; do
        [ -n "$conn" ] && guacaman --config "$TEST_CONFIG" conn del --name "$conn" 2>/dev/null || true
    done

    # Clean up test users with timestamp patterns
    guacaman --config "$TEST_CONFIG" user list 2>/dev/null | grep -E "test_[a-zA-Z_]+_[0-9]{10}" | while read -r user; do
        [ -n "$user" ] && guacaman --config "$TEST_CONFIG" user del --name "$user" 2>/dev/null || true
    done

    # Clean up test user groups with timestamp patterns
    guacaman --config "$TEST_CONFIG" usergroup list 2>/dev/null | grep -E "test_[a-zA-Z_]+_[0-9]{10}" | while read -r group; do
        [ -n "$group" ] && guacaman --config "$TEST_CONFIG" usergroup del --name "$group" 2>/dev/null || true
    done
}

# Global teardown function - called once after all tests complete
teardown() {
    # Clean up timestamped test entries first (in case tests failed)
    cleanup_timestamped_entries

    # Clean up standard test objects
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