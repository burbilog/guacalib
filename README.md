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

### Listing Data
```python
# List users with their groups
users = guacdb.list_users_with_usergroups()

# List groups with their users and connections
groups = guacdb.list_usergroups_with_users_and_connections()

# List all connections
connections = guacdb.list_connections_with_conngroups_and_parents()
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
```bash
guacaman usergroup del --name developers
```

#### Modify a user group
Add or remove users from a group:
```bash
# Add user to group
guacaman usergroup modify --name developers --adduser john.doe

# Remove user from group
guacaman usergroup modify --name developers --rmuser john.doe
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
    --group developers,qa  # Comma-separated list of groups

# Create other types of connections
guacaman conn new --type rdp ...
guacaman conn new --type ssh ...
```

#### List all connections
```bash
guacaman conn list
```

#### Modify a connection
```bash
# Change connection parameters
guacaman conn modify --name dev-server \
    --set hostname=192.168.1.200 \
    --set port=5902 \
    --set max_connections=5

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

#### Delete a connection
```bash
guacaman conn del --name dev-server
```

### Managing Connection Groups

Connection groups allow you to organize connections into hierarchical groups. Here's how to manage them:

#### Create a new connection group
```bash
# Create a top-level group
guacaman conngroup new --name production

# Create a nested group under production
guacaman conngroup new --name vnc_servers --parent production
```

#### List all connection groups
Shows all groups and their hierarchy:
```bash
guacaman conngroup list
```

#### Delete a connection group
```bash
guacaman conngroup del --name vnc_servers
```

#### Modify a connection group
Change parent group or hierarchy:
```bash
# Move group to new parent
guacaman conngroup modify --name vnc_servers --parent "infrastructure"

# Remove parent (make top-level)
guacaman conngroup modify --name vnc_servers --parent ""
```

#### Check if a connection group exists
```bash
guacaman conngroup exists --name vnc_servers
```

### Version Information

Check the installed version:
```bash
guacaman version
```

### Check existence

Check if a user, group or connection exists (returns 0 if exists, 1 if not):

```bash
# Check user
guacaman user exists --name john.doe

# Check user group
guacaman usergroup exists --name developers

# Check connection
guacaman conn exists --name dev-server
```

These commands are silent and only return an exit code, making them suitable for scripting.

### Dump all data

Dumps all groups, users and connections in YAML format:
```bash
guacaman dump
```

## Output Format

All list commands (`user list`, `usergroup list`, `conn list`, `conngroup list`, `dump`) output data in proper, parseable YAML format. This makes it easy to process the output with tools like `yq` or integrate with other systems.

Example:
```bash
# Parse with yq
guacaman user list | yq '.users[].groups'
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

## Error Handling

The tool provides comprehensive error handling for:
- Database connection issues
- Missing users or groups
- Duplicate entries
- Permission problems
- Invalid configurations

All errors are reported with clear messages to help diagnose issues.

## Security Considerations

- Database credentials are stored in a separate configuration file
- Configuration file must have strict permissions (0600/-rw-------)
  - Script will exit with error code 2 if permissions are too open
- Passwords are properly hashed before storage  
- The tool handles database connections securely
- All SQL queries use parameterized statements to prevent SQL injection

## Limitations

- Requires MySQL client access to the Guacamole database

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

- [X] Support for other connection types
  - RDP (Remote Desktop Protocol)
  - SSH

- [ ] User permissions management
  - More granular permissions control
  - Permission templates

- [ ] Connection parameters management
  - Custom parameters for different connection types
  - Connection groups

- [ ] Implement dumping RDP connections
  - Add RDP connection support to dump command
  - Include RDP-specific parameters in output

PRs implementing any of these features are welcome!

## Version

This is version 0.13

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Copyright Roman V. Isaev <rm@isaeff.net> 2024, though 95% of the code is written with Aider/DeepSeek-V3/Sonnet-3.5/etc

This software is distributed under the terms of the GNU General Public license, version 0.13.

## Support

For bugs, questions, and discussions please use the [GitHub Issues](https://github.com/burbilog/guacalib/issues).
