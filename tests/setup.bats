#!/usr/bin/env bats

# Global setup function that runs once before all tests
setup() {
    # Check if TEST_CONFIG is set and points to a valid file
    if [ -z "$TEST_CONFIG" ] || [ ! -f "$TEST_CONFIG" ]; then
        echo "Error: TEST_CONFIG environment variable must be set to a valid config file"
        echo "Example:"
        echo "  export TEST_CONFIG=/path/to/test_config.ini"
        skip "TEST_CONFIG variable is not set"
    fi

    # Verify the config file contains required sections
    if ! grep -q '\[mysql\]' "$TEST_CONFIG"; then
        skip "Test config file must contain [mysql] section"
    fi

    # Clean up any existing test objects first
    guacaman --config "$TEST_CONFIG" conn del --name testconn1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" conn del --name testconn2 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" user del --name testuser1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" user del --name testuser2 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" usergroup del --name testgroup1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" usergroup del --name testgroup2 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" usergroup del --name parentgroup1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" usergroup del --name nested/parentgroup2 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup1 2>/dev/null || true
    guacaman --config "$TEST_CONFIG" conngroup del --name testconngroup2 2>/dev/null || true

    # Create test groups, users and connections
    guacaman --config "$TEST_CONFIG" usergroup new --name testgroup1
    guacaman --config "$TEST_CONFIG" usergroup new --name testgroup2
    guacaman --config "$TEST_CONFIG" user new --name testuser1 --password testpass1 --usergroup testgroup1,testgroup2
    guacaman --config "$TEST_CONFIG" user new --name testuser2 --password testpass2
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn1 --hostname 192.168.1.100 --port 5901 --password vncpass1 --usergroup testgroup1
    guacaman --config "$TEST_CONFIG" conn new --type vnc --name testconn2 --hostname 192.168.1.101 --port 5902 --password vncpass2
    guacaman --config "$TEST_CONFIG" usergroup new --name parentgroup1
    guacaman --config "$TEST_CONFIG" usergroup new --name nested/parentgroup2
    guacaman --config "$TEST_CONFIG" conngroup new --name testconngroup1
    guacaman --config "$TEST_CONFIG" conngroup new --name testconngroup2 --parent testconngroup1
}
