# Guacamole management library and CLI utility

A command-line tool and Python library for managing Apache Guacamole users, groups, and VNC connections. Command line tool provides a simple way to manage Guacamole's MySQL database directly, allowing for easy automation and scripting of user management tasks.

## Features

### CLI utility

- Version information
- Create and delete users
- Create and delete groups
- Manage user group memberships
- Create and manage VNC connections
- List existing users and their group memberships
- List existing groups and their members
- List existing VNC connections with their parameters
- Dump all data (users, groups, connections) in YAML format
- Comprehensive error handling and validation
- Secure database operations with parameterized queries

### Library

Do all the above in Python

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

# Add user to group
guacdb.add_user_to_group('john.doe', 'developers')

# Check if user exists
if guacdb.user_exists('john.doe'):
    print("User exists")

# Delete user
guacdb.delete_existing_user('john.doe')
```

### Managing Groups
```python
# Create group
guacdb.create_group('developers')

# Check if group exists
if guacdb.group_exists('developers'):
    print("Group exists")

# Delete group
guacdb.delete_existing_group('developers')
```

### Managing Connections
```python
# Create VNC connection
conn_id = guacdb.create_vnc_connection(
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

### Listing Data
```python
# List users with their groups
users = guacdb.list_users_with_groups()

# List groups with their users and connections
groups = guacdb.list_groups_with_users_and_connections()

# List all VNC connections
connections = guacdb.list_connections_with_groups()
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
    --group developers,managers,qa  # Add to multiple groups

# Note: Will fail if user already exists
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

### Managing Groups

#### Create a new group
```bash
guacaman group new --name developers
```

#### List all groups
Shows all groups and their members:
```bash
guacaman group list
```

#### Delete a group
```bash
guacaman group del --name developers
```

### Managing VNC Connections

#### Create a new VNC connection
```bash
guacaman vconn new \
    --name dev-server \
    --hostname 192.168.1.100 \
    --port 5901 \
    --vnc-password vncpass \
    --group developers,qa  # Comma-separated list of groups
```

#### List all VNC connections
```bash
guacaman vconn list
```

#### Delete a VNC connection
```bash
guacaman vconn del --name dev-server
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

# Check group
guacaman group exists --name developers

# Check connection
guacaman vconn exists --name dev-server
```

These commands are silent and only return an exit code, making them suitable for scripting.

### Dump all data

Dumps all groups, users and connections in YAML format:
```bash
guacaman dump
```

Example output:
```yaml
groups:
  group1:
    users:
      - user1
    connections:
      - conn1
users:
  user1:
    groups:
      - group1
vnc-connections:
  conn1:
    hostname: 192.168.1.100
    port: 5901
    groups:
      - group1
```

## Output Format

All list commands (`user list`, `group list`, `vconn list`, `dump`) output data in proper, parseable YAML format. This makes it easy to process the output with tools like `yq` or integrate with other systems.

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

The tool includes comprehensive error handling for:
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

- Currently supports only VNC connections
- Must be run on a machine with MySQL client access to the Guacamole database

## TODO

Current limitations and planned improvements:

- [x] Separate connection management from user creation ✓
  - Implemented in `vconn` command:
    ```bash
    # Create connection
    guacaman vconn new --name dev-server --hostname 192.168.1.100 --port 5901 --vnc-password somepass
    
    # List connections
    guacaman vconn list
    
    # Delete connection
    guacaman vconn del --name dev-server
    ```

- [ ] Support for other connection types
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

This is version 0.6

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Copyright Roman V. Isaev <rm@isaeff.net> 2024

This software is distributed under the terms of the GNU General Public license, version 0.6.

## Support

For bugs, questions, and discussions please use the [GitHub Issues](https://github.com/burbilog/guacalib/issues).
