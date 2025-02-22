# Guacamole CLI Manager

A command-line tool for managing Apache Guacamole users, groups, and VNC connections. This tool provides a simple way to manage Guacamole's MySQL database directly, allowing for easy automation and scripting of user management tasks.

## Features

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

## Installation

1. Clone the repository:
```bash
git clone https://github.com/burbilog/gcmanager.git
cd gcmanager
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a database configuration file `db_config.ini`:
```ini
[mysql]
host = localhost
user = guacamole_user
password = your_password
database = guacamole_db
```

## Usage

### Managing Users

#### Create a new user
```bash
# Basic user creation
./gcmanager.py user new \
    --username john.doe \
    --password secretpass

# Create with group memberships (comma-separated)
./gcmanager.py user new \
    --username john.doe \
    --password secretpass \
    --group developers,managers,qa  # Add to multiple groups

# Note: Will fail if user already exists
```

#### List all users
Shows all users and their group memberships:
```bash
./gcmanager.py user list
```

#### Delete a user
Removes a user:
```bash
./gcmanager.py user del --username john.doe
```

### Managing Groups

#### Create a new group
```bash
./gcmanager.py group new --name developers
```

#### List all groups
Shows all groups and their members:
```bash
./gcmanager.py group list
```

#### Delete a group
```bash
./gcmanager.py group del --name developers
```

### Managing VNC Connections

#### Create a new VNC connection
```bash
./gcmanager.py vconn new \
    --name dev-server \
    --hostname 192.168.1.100 \
    --port 5901 \
    --vnc-password vncpass \
    --group developers,qa  # Comma-separated list of groups
```

#### List all VNC connections
```bash
./gcmanager.py vconn list
```

#### Delete a VNC connection
```bash
./gcmanager.py vconn del --name dev-server
```

### Check existence

Check if a user, group or connection exists (returns 0 if exists, 1 if not):

```bash
# Check user
./gcmanager.py user exists --username john.doe

# Check group
./gcmanager.py group exists --name developers

# Check connection
./gcmanager.py vconn exists --name dev-server
```

These commands are silent and only return an exit code, making them suitable for scripting.

### Dump all data

Dumps all groups, users and connections in YAML format:
```bash
./gcmanager.py dump
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
connections:
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
./gcmanager.py user list | yq '.users[].groups'
```

## Configuration File Format

The `db_config.ini` file should contain MySQL connection details:

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
    gcmanager.py vconn new --name dev-server --hostname 192.168.1.100 --port 5901 --vnc-password somepass
    
    # List connections
    gcmanager.py vconn list
    
    # Delete connection
    gcmanager.py vconn del --name dev-server
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Copyright Roman V. Isaev <rm@isaeff.net> 2024

This software is distributed under the terms of the GNU General Public license, version 3.0.

## Support

For bugs, questions, and discussions please use the [GitHub Issues](https://github.com/burbilog/gcmanager/issues).
