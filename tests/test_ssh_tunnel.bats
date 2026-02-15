#!/usr/bin/env bats
#
# Test SSH tunnel functionality
#
# Prerequisites:
#   ssh-keygen -t ed25519 -f ~/.ssh/test_id_ed25519 -N ""
#   cat ~/.ssh/test_id_ed25519.pub >> ~/.ssh/authorized_keys
#   chmod 600 ~/.ssh/authorized_keys
#

# Config file for tests
TEST_SSH_CONFIG="/tmp/guacaman_ssh_test.ini"

setup() {
    # Check if SSH test keys exist
    if [ ! -f ~/.ssh/test_id_ed25519 ]; then
        skip "SSH test key not found. Run: ssh-keygen -t ed25519 -f ~/.ssh/test_id_ed25519 -N ''"
    fi

    if [ ! -f ~/.ssh/test_id_ed25519.pub ]; then
        skip "SSH test public key not found"
    fi

    # Check if test key is in authorized_keys
    if ! grep -q "$(cat ~/.ssh/test_id_ed25519.pub | cut -d' ' -f2)" ~/.ssh/authorized_keys 2>/dev/null; then
        skip "SSH test key not in authorized_keys. Run: cat ~/.ssh/test_id_ed25519.pub >> ~/.ssh/authorized_keys"
    fi
}

teardown() {
    rm -f "$TEST_SSH_CONFIG"
}

@test "SSH test key exists" {
    [ -f ~/.ssh/test_id_ed25519 ]
    [ -f ~/.ssh/test_id_ed25519.pub ]
}

@test "SSH test key in authorized_keys" {
    grep -q "$(cat ~/.ssh/test_id_ed25519.pub | cut -d' ' -f2)" ~/.ssh/authorized_keys
}

@test "SSH connection to localhost works" {
    ssh -i ~/.ssh/test_id_ed25519 -o StrictHostKeyChecking=no \
        -o BatchMode=yes -o ConnectTimeout=5 localhost "echo OK" | grep -q "OK"
}

@test "sshtunnel package is installed" {
    pip show sshtunnel >/dev/null 2>&1 || pip install sshtunnel >/dev/null 2>&1
    python3 -c "from sshtunnel import SSHTunnelForwarder; print('OK')" | grep -q "OK"
}

@test "SSH tunnel config parsing - from config file" {
    # Create test config with SSH tunnel settings
    cat > "$TEST_SSH_CONFIG" <<EOF
[mysql]
host = remote-server.example.com
user = guacamole_user
password = test_password
database = guacamole_db

[ssh_tunnel]
enabled = true
host = ssh-gateway.example.com
port = 22
user = ssh_user
private_key = /home/user/.ssh/id_rsa
EOF

    # Test config parsing
    python3 -c "
from guacalib.repositories.base import BaseGuacamoleRepository
config = BaseGuacamoleRepository.read_ssh_tunnel_config('$TEST_SSH_CONFIG')
assert config is not None
assert config['enabled'] == True
assert config['host'] == 'ssh-gateway.example.com'
assert config['port'] == 22
assert config['user'] == 'ssh_user'
assert config['private_key'] == '/home/user/.ssh/id_rsa'
print('OK')
" | grep -q "OK"
}

@test "SSH tunnel config parsing - disabled by default" {
    # Create test config without SSH tunnel
    cat > "$TEST_SSH_CONFIG" <<EOF
[mysql]
host = localhost
user = guacamole_user
password = test_password
database = guacamole_db
EOF

    # Test config parsing
    python3 -c "
from guacalib.repositories.base import BaseGuacamoleRepository
config = BaseGuacamoleRepository.read_ssh_tunnel_config('$TEST_SSH_CONFIG')
assert config is None, f'Expected None, got {config}'
print('OK')
" | grep -q "OK"
}

@test "SSH tunnel config parsing - from environment variables" {
    # Test env var parsing
    export GUACALIB_SSH_TUNNEL_ENABLED=true
    export GUACALIB_SSH_TUNNEL_HOST=env-gateway.example.com
    export GUACALIB_SSH_TUNNEL_PORT=2222
    export GUACALIB_SSH_TUNNEL_USER=env_user
    export GUACALIB_SSH_TUNNEL_PASSWORD=env_password

    python3 -c "
from guacalib.repositories.base import BaseGuacamoleRepository
import os
# Reset cached env vars by calling with non-existent file
config = BaseGuacamoleRepository.read_ssh_tunnel_config('/non/existent/file')
assert config is not None
assert config['enabled'] == True
assert config['host'] == 'env-gateway.example.com'
assert config['port'] == 2222
assert config['user'] == 'env_user'
assert config['password'] == 'env_password'
print('OK')
" | grep -q "OK"

    # Cleanup
    unset GUACALIB_SSH_TUNNEL_ENABLED
    unset GUACALIB_SSH_TUNNEL_HOST
    unset GUACALIB_SSH_TUNNEL_PORT
    unset GUACALIB_SSH_TUNNEL_USER
    unset GUACALIB_SSH_TUNNEL_PASSWORD
}

@test "MySQL over SSH tunnel - create and delete user" {
    # Skip if no TEST_CONFIG set
    if [ -z "$TEST_CONFIG" ]; then
        skip "TEST_CONFIG not set"
    fi

    # Read MySQL config from TEST_CONFIG
    MYSQL_HOST=$(grep '^host' "$TEST_CONFIG" | cut -d'=' -f2 | tr -d ' ')
    MYSQL_USER=$(grep '^user' "$TEST_CONFIG" | head -1 | cut -d'=' -f2 | tr -d ' ')
    MYSQL_PASSWORD=$(grep '^password' "$TEST_CONFIG" | cut -d'=' -f2 | tr -d ' ')
    MYSQL_DATABASE=$(grep '^database' "$TEST_CONFIG" | cut -d'=' -f2 | tr -d ' ')

    # Create test config with SSH tunnel to localhost
    cat > "$TEST_SSH_CONFIG" <<EOF
[mysql]
host = $MYSQL_HOST
user = $MYSQL_USER
password = $MYSQL_PASSWORD
database = $MYSQL_DATABASE

[ssh_tunnel]
enabled = true
host = localhost
port = 22
user = $USER
private_key = $HOME/.ssh/test_id_ed25519
EOF
    chmod 600 "$TEST_SSH_CONFIG"

    # Generate unique test username
    TEST_USER="ssh_tunnel_test_$$_$(date +%s)"

    # Test: Create user via SSH tunnel
    run guacaman --config "$TEST_SSH_CONFIG" user new --name "$TEST_USER" --password testpassword123
    [ "$status" -eq 0 ]

    # Verify user exists
    run guacaman --config "$TEST_SSH_CONFIG" user list
    [ "$status" -eq 0 ]
    echo "$output" | grep -q "$TEST_USER"

    # Cleanup: Delete user
    run guacaman --config "$TEST_SSH_CONFIG" user del --name "$TEST_USER"
    [ "$status" -eq 0 ]

    # Verify user deleted
    run guacaman --config "$TEST_SSH_CONFIG" user list
    [ "$status" -eq 0 ]
    ! echo "$output" | grep -q "$TEST_USER"
}

@test "GuacamoleDB facade works with SSH tunnel" {
    # Skip if no TEST_CONFIG set
    if [ -z "$TEST_CONFIG" ]; then
        skip "TEST_CONFIG not set"
    fi

    # Read MySQL config from TEST_CONFIG
    MYSQL_HOST=$(grep '^host' "$TEST_CONFIG" | cut -d'=' -f2 | tr -d ' ')
    MYSQL_USER=$(grep '^user' "$TEST_CONFIG" | head -1 | cut -d'=' -f2 | tr -d ' ')
    MYSQL_PASSWORD=$(grep '^password' "$TEST_CONFIG" | cut -d'=' -f2 | tr -d ' ')
    MYSQL_DATABASE=$(grep '^database' "$TEST_CONFIG" | cut -d'=' -f2 | tr -d ' ')

    # Create test config with SSH tunnel to localhost
    cat > "$TEST_SSH_CONFIG" <<EOF
[mysql]
host = $MYSQL_HOST
user = $MYSQL_USER
password = $MYSQL_PASSWORD
database = $MYSQL_DATABASE

[ssh_tunnel]
enabled = true
host = localhost
port = 22
user = $USER
private_key = $HOME/.ssh/test_id_ed25519
EOF
    chmod 600 "$TEST_SSH_CONFIG"

    # Test facade
    python3 -c "
import sys
from guacalib import GuacamoleDB

try:
    with GuacamoleDB('$TEST_SSH_CONFIG', debug=True) as db:
        users = db.list_users()
        assert isinstance(users, list)
        print('OK')
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    raise
" 2>&1 | grep -q "OK"
}
