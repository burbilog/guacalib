#!/bin/bash

setup_file() {
    export SUITE_SETUP_DONE="${BATS_SUITE_TMPDIR}/setup_done"
    if [ ! -f "$SUITE_SETUP_DONE" ]; then
        # Check if TEST_CONFIG is set and points to a valid file
        if [ -z "$TEST_CONFIG" ] || [ ! -f "$TEST_CONFIG" ]; then
            echo "Error: TEST_CONFIG environment variable must be set to a valid config file"
            echo "Example:"
            echo "  export TEST_CONFIG=/path/to/test_config.ini"
            exit 1
        fi

        # Verify the config file contains required sections
        if ! grep -q '\[mysql\]' "$TEST_CONFIG"; then
            echo "Test config file must contain [mysql] section"
            exit 1
        fi

        # Create test groups, users and connections, ignoring errors if they already exist
        guacaman --config "$TEST_CONFIG" usergroup new --name testgroup1 || true
        guacaman --config "$TEST_CONFIG" usergroup new --name testgroup2 || true
        guacaman --config "$TEST_CONFIG" user new --name testuser1 --password testpass1 --usergroup testgroup1,testgroup2 || true
        guacaman --config "$TEST_CONFIG" user new --name testuser2 --password testpass2 || true
        guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --password vncpass1 --usergroup testgroup1 || true
        guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn2 --hostname 192.168.1.101 --port 5902 --password vncpass2 || true
        guacaman --config "$TEST_CONFIG" usergroup new --name parentgroup1 || true
        guacaman --config "$TEST_CONFIG" usergroup new --name nested/parentgroup2 || true
        guacaman --config "$TEST_CONFIG" conngroup new --name testconngroup1 || true
        guacaman --config "$TEST_CONFIG" conngroup new --name testconngroup2 --parent testconngroup1 || true

        touch "$SUITE_SETUP_DONE"
    fi
}

teardown_file() {
    export SUITE_TEARDOWN_DONE="${BATS_SUITE_TMPDIR}/teardown_done"
    if [ ! -f "$SUITE_TEARDOWN_DONE" ]; then
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

        # Additional cleanup for any leftover objects
        guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup1 || true
        guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup2 || true
        guacaman --config "$TEST_CONFIG" usergroup del --name testgroup1 || true
        guacaman --config "$TEST_CONFIG" usergroup del --name testgroup2 || true
        guacaman --config "$TEST_CONFIG" usergroup del --name parentgroup1 || true
        guacaman --config "$TEST_CONFIG" usergroup del --name nested/parentgroup2 || true

        touch "$SUITE_TEARDOWN_DONE"
    fi
}
