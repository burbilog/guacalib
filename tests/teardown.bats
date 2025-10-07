#!/usr/bin/env bats

# Function to clean up all timestamp-based test entries
cleanup_timestamped_entries() {
    # Clean up test connection groups with timestamp patterns
    guacaman --config "$TEST_CONFIG" conngroup list >/dev/null 2>&1 | grep -E "test_[a-zA-Z_]+_[0-9]{10}:" | cut -d: -f1 | while read -r group; do
        [ -n "$group" ] && guacaman --config "$TEST_CONFIG" conngroup del --name "$group" >/dev/null 2>&1 || true
    done

    # Clean up test connections with timestamp patterns
    guacaman --config "$TEST_CONFIG" conn list >/dev/null 2>&1 | grep -E "  test_[a-zA-Z_]+_[0-9]{10}:" | cut -d: -f1 | tr -d ' ' | while read -r conn; do
        [ -n "$conn" ] && guacaman --config "$TEST_CONFIG" conn del --name "$conn" >/dev/null 2>&1 || true
    done

    # Clean up test users with timestamp patterns
    guacaman --config "$TEST_CONFIG" user list >/dev/null 2>&1 | grep -E "test_[a-zA-Z_]+_[0-9]{10}" | while read -r user; do
        [ -n "$user" ] && guacaman --config "$TEST_CONFIG" user del --name "$user" >/dev/null 2>&1 || true
    done

    # Clean up test user groups with timestamp patterns
    guacaman --config "$TEST_CONFIG" usergroup list >/dev/null 2>&1 | grep -E "test_[a-zA-Z_]+_[0-9]{10}" | while read -r group; do
        [ -n "$group" ] && guacaman --config "$TEST_CONFIG" usergroup del --name "$group" >/dev/null 2>&1 || true
    done
}

# Global teardown function - called once after all tests complete
teardown() {
    # Clean up timestamped test entries first (in case tests failed)
    cleanup_timestamped_entries

    # Clean up standard test objects
    guacaman --config "$TEST_CONFIG" conn del --name testconn1 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" conn del --name testconn2 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" user del --name testuser1 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" user del --name testuser2 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name testgroup1 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name testgroup2 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name parentgroup1 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" usergroup del --name nested/parentgroup2 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup1 >/dev/null 2>&1 || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup2 >/dev/null 2>&1 || true
}