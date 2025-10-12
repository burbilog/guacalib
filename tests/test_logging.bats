#!/usr/bin/env bats

# Test suite for guacalib logging feature implementation
# Based on @plans/logging_plan.md success criteria and functionality

# Load the main test runner which includes setup/teardown and helper functions
load run_tests.bats


@test "Phase 1: Logging infrastructure setup" {
    # Test that logging_config module exists and can be imported
    python -c "
import sys
sys.path.insert(0, '.')
from guacalib.logging_config import setup_logging, get_logger
print('SUCCESS: logging_config module imported successfully')
" >&3

    # Test that setup_logging function is available and callable
    python -c "
import sys
sys.path.insert(0, '.')
from guacalib.logging_config import setup_logging
setup_logging(debug=False)
print('SUCCESS: setup_logging() executed without error')
" >&3

    # Test that get_logger function returns proper logger
    python -c "
import sys
sys.path.insert(0, '.')
from guacalib.logging_config import get_logger
logger = get_logger('test')
print(f'SUCCESS: get_logger() returned logger: {type(logger).__name__}')
" >&3
}

@test "Phase 1: Idempotent logging setup" {
    # Test that multiple setup_logging calls don't create duplicate handlers
    python -c "
import sys
sys.path.insert(0, '.')
from guacalib.logging_config import setup_logging, get_logger

# Setup logging multiple times
setup_logging(debug=True)
setup_logging(debug=True)
setup_logging(debug=True)

logger = get_logger('test')
logger.info('Test message - should appear once')

# Check that we don't have duplicate handlers
import logging
root_logger = logging.getLogger('guacalib')
handler_count = len(root_logger.handlers)
print(f'Handler count: {handler_count}')
assert handler_count == 1, f'Expected 1 handler, got {handler_count}'
print('SUCCESS: No duplicate handlers created')
" >&3
}

@test "Phase 2: Database layer logging functionality" {
    # Test that database operations produce appropriate log output
    guacaman --config "$TEST_CONFIG" --debug user list >test_stdout.log 2>test_stderr.log

    # Check that stdout contains user data
    grep -q "^users:" test_stdout.log
    [ "$?" -eq 0 ]

    # Check that stderr contains debug logs
    grep -q "Database connection established" test_stderr.log
    [ "$?" -eq 0 ]

    grep -q "Dispatching user command: list" test_stderr.log
    [ "$?" -eq 0 ]

    echo "SUCCESS: Database layer logging produces appropriate output" >&3
}

@test "Phase 3: CLI handler logging functionality" {
    # Test that CLI handlers produce appropriate log messages

    # Test successful operation logging (using user command which has debug logging)
    guacaman --config "$TEST_CONFIG" --debug user list >test_stdout.log 2>test_stderr.log

    # Should contain debug logs for successful operation
    grep -q "Dispatching user command: list" test_stderr.log
    [ "$?" -eq 0 ]

    echo "SUCCESS: CLI handler logging for successful operations" >&3
}

@test "Phase 3: CLI error logging functionality" {
    # Test that CLI errors are properly logged

    # Create timestamped test connection name for proper cleanup
    TEST_CONN="test_conn_logging_error_$(date +%s)"

    # Test with invalid connection parameters (should produce error logs)
    run guacaman --config "$TEST_CONFIG" --debug conn new --type vnc --name "$TEST_CONN" --hostname invalidhost --port 5900 2>&1

    # Should contain error in both user output and logs
    [[ "$output" =~ "Failed to create connection" ]]
    [ "$?" -eq 0 ]

    # When debug is enabled, should also contain log messages
    [[ "$output" =~ "Creating new connection" ]]
    [ "$?" -eq 0 ]

    [[ "$output" =~ "Failed to create connection" ]]
    [ "$?" -eq 0 ]

    echo "SUCCESS: CLI error logging functionality working" >&3
}

@test "Phase 4: CLI integration with --debug flag" {
    # Test that --debug flag enables debug logging

    # Test without debug flag
    guacaman --config "$TEST_CONFIG" user list >test_stdout.log 2>test_stderr.log

    # Should not contain debug messages in stderr
    if grep -q "Dispatching user command" test_stderr.log; then
        echo "ERROR: Debug messages found without --debug flag"
        return 1
    fi

    # Test with debug flag
    guacaman --config "$TEST_CONFIG" --debug user list >test_stdout.log 2>test_stderr.log

    # Should contain debug messages in stderr
    grep -q "Dispatching user command: list" test_stderr.log
    [ "$?" -eq 0 ]

    grep -q "Database connection established" test_stderr.log
    [ "$?" -eq 0 ]

    echo "SUCCESS: --debug flag properly enables debug logging" >&3
}

@test "Phase 4: Environment variable support - GUACALIB_LOG_LEVEL" {
    # Test that GUACALIB_LOG_LEVEL environment variable works

    # Test with INFO level
    run env GUACALIB_LOG_LEVEL=INFO guacaman --config "$TEST_CONFIG" user list 2>&1

    # Should contain INFO level logs
    [[ "$output" =~ "Database connection established" ]]
    [ "$?" -eq 0 ]

    # Should not contain DEBUG level logs
    if [[ "$output" =~ "Dispatching user command" ]]; then
        echo "ERROR: DEBUG logs found with INFO level"
        return 1
    fi

    echo "SUCCESS: GUACALIB_LOG_LEVEL environment variable working" >&3
}

@test "Phase 4: Environment variable support - GUACALIB_LOG_FORMAT" {
    # Test that GUACALIB_LOG_FORMAT environment variable works

    run env GUACALIB_LOG_FORMAT='[%(levelname)s] %(message)s' guacaman --config "$TEST_CONFIG" --debug user list 2>&1

    # Should contain logs with custom format
    [[ "$output" =~ "[INFO] Database connection established" ]]
    [ "$?" -eq 0 ]

    [[ "$output" =~ "[DEBUG] Dispatching user command: list" ]]
    [ "$?" -eq 0 ]

    echo "SUCCESS: GUACALIB_LOG_FORMAT environment variable working" >&3
}

@test "Phase 4: Invalid environment variables handling" {
    # Test that invalid environment variables are handled gracefully

    # Test with invalid log level
    run env GUACALIB_LOG_LEVEL=INVALID_LEVEL guacaman --config "$TEST_CONFIG" user list 2>&1

    # Should fall back to default behavior and show warning
    [[ "$output" =~ "Warning: Invalid GUACALIB_LOG_LEVEL" ]]
    [ "$?" -eq 0 ]

    # Should still work (user data should be present)
    [[ "$output" =~ "users:" ]]
    [ "$?" -eq 0 ]

    echo "SUCCESS: Invalid environment variables handled gracefully" >&3
}

@test "Phase 5: Stdout/stderr separation" {
    # Test that user data goes to stdout and logs go to stderr

    guacaman --config "$TEST_CONFIG" --debug user list >test_stdout.log 2>test_stderr.log

    # Check that stdout contains user data
    grep -q "^users:" test_stdout.log
    [ "$?" -eq 0 ]

    # Check that stdout does NOT contain log messages
    if grep -q "Database connection established" test_stdout.log; then
        echo "ERROR: Log messages found in stdout"
        return 1
    fi

    # Check that stderr contains log messages
    grep -q "Database connection established" test_stderr.log
    [ "$?" -eq 0 ]

    grep -q "Dispatching user command: list" test_stderr.log
    [ "$?" -eq 0 ]

    # Check that stderr does NOT contain user data
    if grep -q "^users:" test_stderr.log; then
        echo "ERROR: User data found in stderr"
        return 1
    fi

    echo "SUCCESS: Proper stdout/stderr separation maintained" >&3
}

@test "Phase 5: Library integration without auto-configuration" {
    # Test that importing guacalib as library doesn't auto-configure logging

    python -c "
import sys
import os
sys.path.insert(0, '.')
import logging

# Clear any existing handlers
root_logger = logging.getLogger()
root_logger.handlers.clear()

# Import guacalib - should NOT auto-configure logging
from guacalib import GuacamoleDB

# Check that no guacalib handlers were added
guacalib_logger = logging.getLogger('guacalib')
handler_count = len(guacalib_logger.handlers)
print(f'Handler count after import: {handler_count}')
assert handler_count == 0, f'Expected 0 handlers, got {handler_count}'
print('SUCCESS: Import does not auto-configure logging')
" >&3
}

@test "Phase 5: Library integration with explicit configuration" {
    # Test that library users can configure logging explicitly

    python -c "
import sys
import os
sys.path.insert(0, '.')
from guacalib import setup_logging, get_logger

# Configure logging explicitly
setup_logging(debug=True)

# Get a logger and test it
logger = get_logger('library_test')
logger.info('Library logging test message')

print('SUCCESS: Library can configure logging explicitly')
" >&3
}

@test "Phase 5: Backward compatibility - CLI output unchanged" {
    # Test that CLI output format remains unchanged

    # Test user list output format
    guacaman --config "$TEST_CONFIG" user list >test_stdout.log 2>/dev/null

    # Should start with "users:"
    head -1 test_stdout.log | grep -q "^users:$"
    [ "$?" -eq 0 ]

    # Should contain user entries with proper YAML format
    grep -q "  admin:" test_stdout.log
    [ "$?" -eq 0 ]

    grep -q "    usergroups:" test_stdout.log
    [ "$?" -eq 0 ]

    # Test connection list output format
    guacaman --config "$TEST_CONFIG" conn list >test_stdout.log 2>/dev/null

    # Should start with "connections:"
    head -1 test_stdout.log | grep -q "^connections:$"
    [ "$?" -eq 0 ]

    echo "SUCCESS: CLI output format remains unchanged" >&3
}

@test "Phase 5: Backward compatibility - --debug flag behavior" {
    # Test that --debug flag behavior is preserved

    # Test that --debug flag still works as expected
    run guacaman --config "$TEST_CONFIG" --debug user list 2>&1

    # Should contain both user data and debug information
    [[ "$output" =~ "users:" ]]
    [ "$?" -eq 0 ]

    [[ "$output" =~ "Database connection established" ]]
    [ "$?" -eq 0 ]

    [[ "$output" =~ "Dispatching user command: list" ]]
    [ "$?" -eq 0 ]

    echo "SUCCESS: --debug flag behavior preserved" >&3
}

@test "Phase 5: Security - no credential exposure in logs" {
    # Test that credentials are not exposed in logs

    # This test ensures that sensitive data is not logged
    # We test by creating a connection with a password and checking logs

    # Create timestamped test connection name for proper cleanup
    TEST_CONN="test_conn_logging_security_$(date +%s)"

    run guacaman --config "$TEST_CONFIG" --debug conn new --type vnc --name "$TEST_CONN" --hostname testhost --port 5900 --password "secret123" 2>&1

    # The command should fail (testhost doesn't exist), but logs should not contain the password
    if [[ "$output" =~ "secret123" ]]; then
        echo "ERROR: Password found in log output"
        return 1
    fi

    # Should not contain any credential-like patterns
    if [[ "$output" =~ (password|secret|token|key).*=.*[a-zA-Z0-9]{8,} ]]; then
        echo "ERROR: Potential credential exposure in logs"
        return 1
    fi

    echo "SUCCESS: No credential exposure in logs" >&3
}


@test "Integration test: End-to-end logging workflow" {
    # Test complete workflow: environment variables + CLI + library integration

    # Test with environment variables + CLI
    run env GUACALIB_LOG_LEVEL=INFO GUACALIB_LOG_FORMAT='[%(name)s] %(message)s' guacaman --config "$TEST_CONFIG" --debug user list 2>&1

    # Should contain logs with custom format
    [[ "$output" =~ "[guacalib.db] Database connection established" ]]
    [ "$?" -eq 0 ]

    # Should contain user data
    [[ "$output" =~ "users:" ]]
    [ "$?" -eq 0 ]

    # Test library usage in same context
    python -c "
import sys
import os
sys.path.insert(0, '.')
from guacalib import setup_logging, get_logger

# Should work alongside CLI usage
setup_logging(debug=False)
logger = get_logger('integration_test')
logger.info('Integration test message')
print('SUCCESS: End-to-end workflow working')
" >&3

    echo "SUCCESS: End-to-end logging workflow validated" >&3
}