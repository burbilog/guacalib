# Guacamole Management Library and CLI Utility

A comprehensive Python library and command-line tool for managing Apache Guacamole users, groups, connections, and connection groups. Provides direct MySQL database access with secure operations and YAML output.

## Features

### CLI Utility

- User management (create, delete, modify, list)
- User group management (create, delete, modify membership)
- Connection management (create, delete, modify parameters)
- Connection group management (create, delete, modify hierarchy)
- Comprehensive listing commands with YAML output
- Data dump functionality
- Version information
- Secure database operations with parameterized queries
- Detailed error handling and validation

### Python Library

- Full programmatic access to all management features
- Context manager for automatic connection handling
- Type-safe parameter handling
- Comprehensive error reporting
- Advanced permission management with atomic operations
- Entity resolution with both name and ID support
- Connection group cycle detection
- Debug utilities for troubleshooting
- Transaction-safe operations

## Installation from PyPI

Just install it with pip:
```bash
pip install guacalib
```

## Installation from repository

1. Clone the repository:
```bash
git clone https://github.com/burbilog/guacalib.git
cd guacalib
```

2. Install the library:
```bash
pip install .
```

## Setting up configuration file

Create a database configuration file in $HOME called  `.guacaman.ini` for guacaman command line utility:
```ini
[mysql]
host = localhost
user = guacamole_user
password = your_password
database = guacamole_db
```
Ensure permissions are strict:
```bash
chmod 0600 $HOME/.guacaman.ini
```

## Python Library Usage

The `guacalib` library provides programmatic access to all Guacamole management features. Here are some examples:

### Basic Setup
```python
from guacalib import GuacamoleDB

# Initialize with config file
guacdb = GuacamoleDB('~/.guacaman.ini')

# Use context manager for automatic cleanup
with GuacamoleDB('~/.guacaman.ini') as guacdb:
    # Your code here
```

### Logging Configuration

When using guacalib as a library, you can configure logging to capture debug output. The library uses Python's standard `logging` module with logger name `"guacalib"`.

**Simple approach - enable debug mode:**
```python
# Debug mode automatically configures a basic logger
with GuacamoleDB('~/.guacaman.ini', debug=True) as guacdb:
    guacdb.create_user('test', 'password')
    # Debug output will be printed to stderr
```

**Advanced approach - custom logging configuration:**
```python
import logging
from guacalib import GuacamoleDB

# Configure the guacalib logger yourself
logger = logging.getLogger('guacalib')
logger.setLevel(logging.DEBUG)

# Add custom handler (e.g., to file)
handler = logging.FileHandler('/var/log/guacalib.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)

# Now use the library
with GuacamoleDB('~/.guacaman.ini') as guacdb:
    # All debug messages go to your log file
    guacdb.create_user('test', 'password')
```

**Integration with existing logging:**
```python
import logging

# If your app already has logging configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable guacalib debug logging when needed
guacalib_logger = logging.getLogger('guacalib')
guacalib_logger.setLevel(logging.DEBUG)
```

### Managing Users
```python
# Create user
guacdb.create_user('john.doe', 'secretpass')

# Check if user exists
if guacdb.user_exists('john.doe'):
    print("User exists")

# Delete user
guacdb.delete_existing_user('john.doe')
```

### Managing User Groups
```python
# Create user group
guacdb.create_usergroup('developers')

# Check if user group exists
if guacdb.usergroup_exists('developers'):
    print("User group exists")

# Add user to a user group
guacdb.add_user_to_usergroup('john.doe', 'developers')

# Delete user group
guacdb.delete_existing_usergroup('developers')
```

### Managing Connections
```python
# Create VNC connection
conn_id = guacdb.create_connection(
    'vnc',
    'dev-server',
    '192.168.1.100',
    5901,
    'vncpass'
)

# Grant connection to group
guacdb.grant_connection_permission(
    'developers',
    'USER_GROUP',
    conn_id
)

# Check if connection exists
if guacdb.connection_exists('dev-server'):
    print("Connection exists")

# Delete connection
guacdb.delete_existing_connection('dev-server')
```

### Managing Connection Groups

Connection groups allow organizing connections into hierarchical groups. Here are the key methods:

```python
# Create a top-level connection group
guacdb.create_connection_group('production')

# Create a nested connection group
guacdb.create_connection_group('vnc_servers', parent_group_name='production')

# List all connection groups with their hierarchy
groups = guacdb.list_connection_groups()
for group_name, data in groups.items():
    print(f"{group_name}:")
    print(f"  Parent: {data['parent']}")
    print(f"  Connections: {data['connections']}")

# Check if a connection group exists
if guacdb.connection_group_exists('production'):
    print("Group exists")

# Modify a connection group's parent
guacdb.modify_connection_group_parent('vnc_servers', 'infrastructure')

# Remove a connection group's parent
guacdb.modify_connection_group_parent('vnc_servers', '')

# Delete a connection group
guacdb.delete_connection_group('vnc_servers')
```

### Advanced Library Features

The GuacamoleDB class provides additional methods for complex operations:

#### Permission Management
```python
# Connection permissions
guacdb.grant_connection_permission_to_user('john.doe', 'dev-server')
guacdb.revoke_connection_permission_from_user('john.doe', 'dev-server')

# Connection group permissions (advanced)
guacdb.grant_connection_group_permission_to_user('john.doe', 'production')
guacdb.grant_connection_group_permission_to_user_by_id('john.doe', 42)
guacdb.revoke_connection_group_permission_from_user('john.doe', 'production')
guacdb.revoke_connection_group_permission_from_user_by_id('john.doe', 42)
```

#### Entity Resolution and Validation
```python
# Resolve entities by name or ID with validation
conn_id = guacdb.resolve_connection_id(connection_name='dev-server')
conn_id = guacdb.resolve_connection_id(connection_id=42)

group_id = guacdb.resolve_conngroup_id(group_name='production')
group_id = guacdb.resolve_conngroup_id(group_id=15)

usergroup_id = guacdb.resolve_usergroup_id(group_name='developers')
usergroup_id = guacdb.resolve_usergroup_id(group_id=8)
```

#### Advanced Query Methods
```python
# Get specific entities by ID
connection = guacdb.get_connection_by_id(42)
conngroup = guacdb.get_connection_group_by_id(15)

# Get names by ID
name = guacdb.get_connection_name_by_id(42)
name = guacdb.get_connection_group_name_by_id(15)
name = guacdb.get_usergroup_name_by_id(8)

# Check existence by ID
exists = guacdb.usergroup_exists_by_id(8)
exists = guacdb.connection_group_exists('production')
exists = guacdb.connection_exists('dev-server')
```

#### Debug and Utility Methods
```python
# Debug permission issues
guacdb.debug_connection_permissions('dev-server')

# Validate positive IDs
guacdb.validate_positive_id(42, "connection")
```

### Listing Data
```python
# List users with their groups
users = guacdb.list_users_with_usergroups()

# List groups with their users and connections
groups = guacdb.list_usergroups_with_users_and_connections()

# List all connections
connections = guacdb.list_connections_with_conngroups_and_parents()

# List connection groups with hierarchy
groups = guacdb.list_connection_groups()

# List groups with users
groups_users = guacdb.list_groups_with_users()
```

## Command line usage

### Managing Users

#### Create a new user
```bash
# Basic user creation
guacaman user new \
    --name john.doe \
    --password secretpass

# Create with group memberships (comma-separated)
guacaman user new \
    --name john.doe \
    --password secretpass \
    --usergroup developers,managers,qa  # Add to multiple groups

# Note: Will fail if user already exists
```

#### Modify a user

Modifies user's settings or changes password. Allowed parameters are:

| Parameter            | Type     | Default | Description                                      |
|----------------------|----------|---------|--------------------------------------------------|
| access_window_end    | time     | NULL    | End of allowed access time window (HH:MM:SS)     |
| access_window_start  | time     | NULL    | Start of allowed access time window (HH:MM:SS)   |
| disabled             | tinyint  | 0       | Whether the user is disabled (0=enabled, 1=disabled) |
| email_address        | string   | NULL    | User's email address                             |
| expired              | tinyint  | 0       | Whether the user account is expired (0=active, 1=expired) |
| full_name            | string   | NULL    | User's full name                                 |
| organization         | string   | NULL    | User's organization                              |
| organizational_role  | string   | NULL    | User's role within the organization              |
| timezone             | string   | NULL    | User's timezone (e.g., "America/New_York")       |
| valid_from           | date     | NULL    | Date when account becomes valid (YYYY-MM-DD)     |
| valid_until          | date     | NULL    | Date when account expires (YYYY-MM-DD)           |

```bash
guacaman user modify --name john.doe --set disabled=1
guacaman user modify --name john.doe --password newsecret
```

#### List all users
Shows all users and their group memberships:
```bash
guacaman user list
```

#### Delete a user
Removes a user:
```bash
guacaman user del --name john.doe
```

#### Check if a user exists
Check user existence (returns 0 if exists, 1 if not):
```bash
guacaman user exists --name john.doe
```

### Managing User Groups

#### Create a new user group
```bash
guacaman usergroup new --name developers
```

#### List all user groups
Shows all groups and their members:
```bash
guacaman usergroup list
```

#### Delete a user group
Supports both name and ID-based deletion:
```bash
# Delete by name
guacaman usergroup del --name developers

# Delete by ID
guacaman usergroup del --id 42
```

#### Check if a user group exists
Supports both name and ID-based existence checking:
```bash
# Check by name
guacaman usergroup exists --name developers

# Check by ID
guacaman usergroup exists --id 42
```

#### Modify a user group
Add or remove users from a group with comprehensive ID support:
```bash
# Add user to group by name
guacaman usergroup modify --name developers --adduser john.doe

# Remove user from group by name
guacaman usergroup modify --name developers --rmuser john.doe

# Use ID-based group selectors
guacaman usergroup modify --id 42 --adduser john.doe
guacaman usergroup modify --id 42 --rmuser john.doe
```

### Managing Connections

#### Create a new connection
```bash
# Create a VNC connection
guacaman conn new \
    --type vnc \
    --name dev-server \
    --hostname 192.168.1.100 \
    --port 5901 \
    --password vncpass \
    --usergroup developers,qa  # Comma-separated list of groups

# Create other types of connections
guacaman conn new --type rdp ...
guacaman conn new --type ssh ...  # Basic support available
```

#### List all connections
```bash
guacaman conn list

# List specific connection by ID
guacaman conn list --id 42
```

#### Modify a connection
```bash
# Change basic connection parameters
guacaman conn modify --name dev-server \
    --set hostname=192.168.1.200 \
    --set port=5902 \
    --set max_connections=5 \
    --set max_connections_per_user=2

# Change protocol-specific parameters
guacaman conn modify --name dev-server \
    --set color-depth=32 \
    --set enable-sftp=true \
    --set enable-audio=true

# Grant permission to user
guacaman conn modify --name dev-server --permit john.doe

# Revoke permission from user
guacaman conn modify --name dev-server --deny john.doe

# Set parent connection group
guacaman conn modify --name dev-server --parent "vnc_servers"

# Remove parent connection group
guacaman conn modify --name dev-server --parent ""

# Invalid parameter handling example (will fail)
guacaman conn modify --name dev-server --set invalid_param=value
```

**Available Connection Parameters:**

The `--set` option supports 50+ parameters organized by category:

**Connection Table Parameters:**
- `protocol` - Connection protocol (vnc, rdp, ssh)
- `max_connections` - Maximum concurrent connections
- `max_connections_per_user` - Max connections per user
- `proxy_hostname` - Guacamole proxy hostname
- `proxy_port` - Guacamole proxy port
- `connection_weight` - Load balancing weight
- `failover_only` - Use for failover only

**Protocol-Specific Parameters:**
- **VNC:** `hostname`, `port`, `password`, `color-depth`, `clipboard-encoding`
- **RDP:** `hostname`, `port`, `username`, `password`, `domain`, `color-depth`
- **SSH:** `hostname`, `port`, `username`, `password`, `private-key`, `passphrase`

**Advanced Features:**
- **SFTP:** `enable-sftp`, `sftp-hostname`, `sftp-port`, `sftp-username`, `sftp-password`
- **Audio:** `enable-audio`, `audio-servername`
- **Session Recording:** `recording-path`, `recording-name`
- **Network:** `autoretry`, `server-alive-interval`
- **Security:** `host-key`, `disable-copy`, `disable-paste`

#### Check if a connection exists
Supports both name and ID-based existence checking:
```bash
# Check by name
guacaman conn exists --name dev-server

# Check by ID
guacaman conn exists --id 42
```

#### Delete a connection
Supports both name and ID-based deletion:
```bash
# Delete by name
guacaman conn del --name dev-server

# Delete by ID
guacaman conn del --id 42
```

### Managing Connection Groups

Connection groups allow you to organize connections into hierarchical groups and manage user permissions for entire groups of connections. Features include cycle detection, atomic operations, and comprehensive permission management.

#### Create a new connection group
```bash
# Create a top-level group
guacaman conngroup new --name production

# Create a nested group under production
guacaman conngroup new --name vnc_servers --parent production
```

#### List all connection groups
Shows all groups and their hierarchy with database IDs:
```bash
guacaman conngroup list

# List specific connection group by ID
guacaman conngroup list --id 15
```

#### Delete a connection group
Supports both name and ID-based deletion with automatic cleanup of child references:
```bash
# Delete by name
guacaman conngroup del --name vnc_servers

# Delete by ID
guacaman conngroup del --id 42
```

#### Check if a connection group exists
Supports both name and ID-based existence checking:
```bash
# Check by name
guacaman conngroup exists --name vnc_servers

# Check by ID
guacaman conngroup exists --id 42
```

#### Modify a connection group
Advanced modification with cycle detection, atomic operations, and comprehensive ID support:

**Parent Group Management:**
```bash
# Move group to new parent (with cycle detection)
guacaman conngroup modify --name vnc_servers --parent "infrastructure"

# Remove parent (make top-level)
guacaman conngroup modify --name vnc_servers --parent ""

# Use ID-based selectors
guacaman conngroup modify --id 42 --parent "infrastructure"
```

**Connection Management within Groups:**
```bash
# Add connection to group by name
guacaman conngroup modify --name vnc_servers --addconn-by-name dev-server

# Add connection to group by ID
guacaman conngroup modify --name vnc_servers --addconn-by-id 42

# Remove connection from group by name
guacaman conngroup modify --name vnc_servers --rmconn-by-name dev-server

# Remove connection from group by ID
guacaman conngroup modify --name vnc_servers --rmconn-by-id 42

# Use ID-based group selectors
guacaman conngroup modify --id 15 --addconn-by-name dev-server
```

**Advanced User Permission Management:**
The system supports atomic permission operations with comprehensive validation:

```bash
# Grant permission to user for connection group using name selector
guacaman conngroup modify --name vnc_servers --permit john.doe

# Grant permission to user for connection group using ID selector
guacaman conngroup modify --id 42 --permit jane.doe

# Revoke permission from user for connection group using name selector
guacaman conngroup modify --name vnc_servers --deny john.doe

# Revoke permission from user for connection group using ID selector
guacaman conngroup modify --id 42 --deny jane.doe

# Multiple users in single operation (repeat flags)
guacaman conngroup modify --name vnc_servers --permit john.doe --permit jane.doe
```

**Combined Operations:**
```bash
# Combine parent modification with permission operations
guacaman conngroup modify --name vnc_servers --parent "infrastructure" --permit john.doe

# Add connection and grant permission in one command
guacaman conngroup modify --name vnc_servers --addconn-by-name dev-server --permit jane.doe

# Complex operation with ID-based selectors
guacaman conngroup modify --id 42 --parent "infrastructure" --addconn-by-id 15 --permit john.doe
```

### Version Information

Check the installed version:
```bash
guacaman version
```

### Debug Mode

Enable debug output to see SQL queries and internal state:
```bash
guacaman --debug conn list
guacaman --debug user new --name test --password test
```

### Check existence

Check if a user, group, connection, or connection group exists (returns 0 if exists, 1 if not):

```bash
# Check user
guacaman user exists --name john.doe

# Check user group (supports both name and ID)
guacaman usergroup exists --name developers
guacaman usergroup exists --id 42

# Check connection (supports both name and ID)
guacaman conn exists --name dev-server
guacaman conn exists --id 42

# Check connection group (supports both name and ID)
guacaman conngroup exists --name production
guacaman conngroup exists --id 15
```

These commands are silent and only return an exit code, making them suitable for scripting.

### Dump all data

Dumps all groups, users and connections in YAML format:
```bash
guacaman dump
```

## Output Format

All list commands (`user list`, `usergroup list`, `conn list`, `conngroup list`, `dump`) output data in YAML-like format. The output includes additional fields that may be useful for scripting and integration.

**Connection List Output:**
```yaml
connections:
  dev-server:
    id: 42
    type: vnc
    hostname: 192.168.1.100
    port: "5901"
    parent: vnc_servers
    groups:
      - developers
    permissions:
      - john.doe
```

**Connection Group List Output:**
```yaml
conngroups:
  vnc_servers:
    id: 15
    parent: production
    connections:
      - dev-server
      - test-server
```

**User List Output:**
```yaml
users:
  john.doe:
    usergroups:
      - developers
      - qa
```

Example parsing with `yq`:
```bash
# Get all connection names
guacaman conn list | yq '.connections | keys[]'

# Get connections in a specific group
guacaman conngroup list | yq '.conngroups.vnc_servers.connections[]'

# Get user groups
guacaman user list | yq '.users[].usergroups[]'
```

## Configuration File Format

The $HOME/`.guacaman.ini` file should contain MySQL connection details:

```ini
[mysql]
host = localhost
user = guacamole_user
password = your_password
database = guacamole_db
```

### SSH Tunnel Configuration (Optional)

For remote MySQL access through an SSH gateway, add an `[ssh_tunnel]` section:

```ini
[ssh_tunnel]
enabled = true
host = ssh-gateway.example.com
port = 22
user = ssh_username
private_key = /home/user/.ssh/id_rsa
# password = ssh_password  # alternative to private_key
# private_key_passphrase = passphrase  # if key is encrypted
```

**Note:** Either `password` or `private_key` is required for SSH authentication.

**Environment Variables** (have priority over config file):
- `GUACALIB_SSH_TUNNEL_ENABLED` - set to "true" to enable
- `GUACALIB_SSH_TUNNEL_HOST` - SSH gateway hostname
- `GUACALIB_SSH_TUNNEL_PORT` - SSH port (default: 22)
- `GUACALIB_SSH_TUNNEL_USER` - SSH username
- `GUACALIB_SSH_TUNNEL_PASSWORD` - SSH password (if not using key)
- `GUACALIB_SSH_TUNNEL_PRIVATE_KEY` - path to SSH private key
- `GUACALIB_SSH_TUNNEL_PRIVATE_KEY_PASSPHRASE` - key passphrase (if encrypted)

## Error Handling

The tool provides comprehensive error handling for:
- Database connection issues
- Missing users or groups
- Duplicate entries
- Permission problems
- Invalid configurations

**Validation Rules:**
- Exactly one of `--name` or `--id` must be provided for most operations
- IDs must be positive integers greater than 0
- Names cannot be empty strings
- Configuration files must have secure permissions (0600)
- Mutual exclusion validation for conflicting options
- Cycle detection for connection group parent relationships
- Type validation for connection parameters (colors, booleans, integers)

**Transaction Handling:**
- Connection group modifications use explicit transactions
- Automatic rollback on errors
- Proper error messages with context
- Atomic permission operations to prevent partial state corruption
- Comprehensive input validation before database operations

**Advanced Features:**
- Connection group cycle detection prevents infinite hierarchies
- Centralized entity resolution with consistent error messages
- Debug mode for troubleshooting (`--debug` flag)
- Parameter validation based on protocol-specific requirements

All errors are reported with clear messages to help diagnose issues. Use `--debug` flag to see detailed SQL queries and internal state.

## Security Considerations

- Database credentials are stored in a separate configuration file
- Configuration file must have strict permissions (0600/-rw-------)
  - Script will exit with error code 2 if permissions are too open
- Passwords are properly hashed before storage  
- The tool handles database connections securely
- All SQL queries use parameterized statements to prevent SQL injection

## Limitations

- Requires MySQL client access to the Guacamole database
- SSH connections have basic support with limited parameter validation
- Connection creation only supports basic parameters (use `modify` for advanced parameters)

## TODO

Current limitations and planned improvements:

- [x] Separate connection management from user creation ✓
  - Implemented in `conn` command:
    ```bash
    # Create VNC connection
    guacaman conn new --type vnc --name dev-server --hostname 192.168.1.100 --port 5901 --password somepass
    
    # List connections
    guacaman conn list
    
    # Delete connection
    guacaman conn del --name dev-server
    ```

- [ ] GuacamoleDB initialization without configuration file, via variables

- [ ] Support for other connection types
  - [X] RDP (Remote Desktop Protocol)
  - [X] SSH (basic support available)

- [x] User permissions management ✓
  - Grant/revoke permissions for individual connections
  - Grant/revoke permissions for connection groups
  - Support for both name-based and ID-based operations
  - Atomic permission operations with rollback
  - Advanced validation and cycle detection
  - [ ] More granular permissions control
  - [ ] Permission templates

- [x] Connection parameters management ✓
  - Full parameter modification support via `--set` option
  - Support for all Guacamole connection parameters
  - Connection group hierarchy management
  - [ ] Custom parameters for different connection types (protocol-specific validation)

- [x] Implement dumping RDP connections ✓
  - All connection types (VNC, RDP) are included in dump command
  - Connection parameters are properly exported in YAML format

PRs implementing any of these features are welcome!

## AI guidelines

For all AI agents: use rules in AGENTS.md

## Version

This is version 0.26

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Copyright Roman V. Isaev <rm@isaeff.net> 2024-2026, though 95% of the code is written with the help of various LLMs and coding agents.

This software is distributed under the terms of the GNU General Public license, version 3.

## Support

For bugs, questions, and discussions please use the [GitHub Issues](https://github.com/burbilog/guacalib/issues).
