#!/bin/bash

# Unified cleanup script for test entries
# Usage: ./cleanup_test_entries.sh MODE [config_file]
#
# MODES:
#   timestamp - Clean only timestamp-based test entries (default)
#   full      - Clean timestamp entries + standard test objects
#   silent    - Like timestamp, but suppress output (for test teardown)
#
# Examples:
#   ./cleanup_test_entries.sh                      # Clean timestamped entries
#   ./cleanup_test_entries.sh full                 # Clean all test entries
#   ./cleanup_test_entries.sh silent ~/.guacaman.ini # Silent cleanup for tests

MODE="${1:-timestamp}"
CONFIG_FILE="${2:-$HOME/.guacaman.ini}"

# Validate mode
case "$MODE" in
    timestamp|full|silent) ;;
    *) echo "Error: Invalid mode '$MODE'. Use: timestamp, full, or silent"; exit 1 ;;
esac

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    echo "Usage: $0 [timestamp|full|silent] [config_file]"
    exit 1
fi

# Output based on mode
output_msg() {
    if [ "$MODE" != "silent" ]; then
        echo "$1"
    fi
}

output_msg "Cleaning up test entries using config: $CONFIG_FILE (mode: $MODE)"

# Function to clean up timestamp-based test entries
cleanup_timestamped_entries() {
    output_msg "Cleaning up connection groups..."
    guacaman --config "$CONFIG_FILE" conngroup list 2>/dev/null | grep -E "test_[a-zA-Z0-9_]+_[0-9]{10}:" | cut -d: -f1 | while read -r group; do
        if [ -n "$group" ]; then
            output_msg "  Deleting connection group: $group"
            guacaman --config "$CONFIG_FILE" conngroup del --name "$group" 2>/dev/null || true
        fi
    done

    output_msg "Cleaning up connections..."
    guacaman --config "$CONFIG_FILE" conn list 2>/dev/null | grep -E "  test_[a-zA-Z0-9_]+_[0-9]{10}:" | cut -d: -f1 | tr -d ' ' | while read -r conn; do
        if [ -n "$conn" ]; then
            output_msg "  Deleting connection: $conn"
            guacaman --config "$CONFIG_FILE" conn del --name "$conn" 2>/dev/null || true
        fi
    done

    output_msg "Cleaning up users..."
    guacaman --config "$CONFIG_FILE" user list 2>/dev/null | grep -E "test_[a-zA-Z0-9_]+_[0-9]{10}:" | cut -d: -f1 | while read -r user; do
        if [ -n "$user" ]; then
            output_msg "  Deleting user: $user"
            guacaman --config "$CONFIG_FILE" user del --name "$user" 2>/dev/null || true
        fi
    done

  output_msg "Cleaning up user groups..."
    # Clean timestamp-based user groups (test_*, temp_del_*, etc.)
    guacaman --config "$CONFIG_FILE" usergroup list 2>/dev/null | grep -E "(test_|temp_del_)[0-9]{10}:" | cut -d: -f1 | while read -r group; do
        if [ -n "$group" ]; then
            output_msg "  Deleting user group: $group"
            guacaman --config "$CONFIG_FILE" usergroup del --name "$group" 2>/dev/null || true
        fi
    done
}

# Function to clean up standard test objects
cleanup_standard_test_objects() {
    output_msg "Cleaning up standard test objects..."
    guacaman --config "$CONFIG_FILE" conn del --name testconn1 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" conn del --name testconn2 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" user del --name testuser1 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" user del --name testuser2 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" usergroup del --name testgroup1 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" usergroup del --name testgroup2 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" usergroup del --name parentgroup1 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" usergroup del --name nested/parentgroup2 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" conngroup del --name testconngroup1 >/dev/null 2>&1 || true
    guacaman --config "$CONFIG_FILE" conngroup del --name testconngroup2 >/dev/null 2>&1 || true
}

# Execute based on mode
case "$MODE" in
    timestamp)
        cleanup_timestamped_entries
        ;;
    full|silent)
        cleanup_timestamped_entries
        cleanup_standard_test_objects
        ;;
esac

output_msg "Cleanup complete!"