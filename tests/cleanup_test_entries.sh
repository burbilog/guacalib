#!/bin/bash

# Cleanup script for timestamp-based test entries
# Usage: ./cleanup_test_entries.sh [config_file]

CONFIG_FILE="${1:-$HOME/.guacaman.ini}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    echo "Usage: $0 [config_file]"
    exit 1
fi

echo "Cleaning up timestamp-based test entries using config: $CONFIG_FILE"

# Function to clean up timestamp-based test entries
cleanup_timestamped_entries() {
    echo "Cleaning up connection groups..."
    guacaman --config "$CONFIG_FILE" conngroup list 2>/dev/null | grep -E "test_[a-zA-Z0-9_]+_[0-9]{10}:" | cut -d: -f1 | while read -r group; do
        if [ -n "$group" ]; then
            echo "  Deleting connection group: $group"
            guacaman --config "$CONFIG_FILE" conngroup del --name "$group" 2>/dev/null || true
        fi
    done

    echo "Cleaning up connections..."
    guacaman --config "$CONFIG_FILE" conn list 2>/dev/null | grep -E "  test_[a-zA-Z0-9_]+_[0-9]{10}:" | cut -d: -f1 | tr -d ' ' | while read -r conn; do
        if [ -n "$conn" ]; then
            echo "  Deleting connection: $conn"
            guacaman --config "$CONFIG_FILE" conn del --name "$conn" 2>/dev/null || true
        fi
    done

    echo "Cleaning up users..."
    guacaman --config "$CONFIG_FILE" user list 2>/dev/null | grep -E "test_[a-zA-Z0-9_]+_[0-9]{10}:" | cut -d: -f1 | while read -r user; do
        if [ -n "$user" ]; then
            echo "  Deleting user: $user"
            guacaman --config "$CONFIG_FILE" user del --name "$user" 2>/dev/null || true
        fi
    done

    echo "Cleaning up user groups..."
    guacaman --config "$CONFIG_FILE" usergroup list 2>/dev/null | grep -E "test_[a-zA-Z0-9_]+_[0-9]{10}:" | cut -d: -f1 | while read -r group; do
        if [ -n "$group" ]; then
            echo "  Deleting user group: $group"
            guacaman --config "$CONFIG_FILE" usergroup del --name "$group" 2>/dev/null || true
        fi
    done
}

cleanup_timestamped_entries

echo "Cleanup complete!"