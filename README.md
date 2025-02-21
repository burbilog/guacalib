# Guacamole CLI Manager

A command-line tool for managing Apache Guacamole users, groups, and VNC connections. This tool provides a simple way to manage Guacamole's MySQL database directly, allowing for easy automation and scripting of user management tasks.

## Features

- Create and delete users
- Create and delete groups
- Manage user group memberships
- Automatically create VNC connections for users
- List existing users and their group memberships
- List existing groups and their members

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
./gcmanager.py user new \
    --username john.doe \
    --password secretpass
```

To create a user and add them to a group:
```bash
./gcmanager.py user new \
    --username john.doe \
    --password secretpass \
    --group developers
```

#### Create a new VNC connection
```bash
./gcmanager.py conn new \
    --name dev-server \
    --hostname 192.168.1.100 \
    --port 5901 \
    --vnc-password vncpass \
    --group developers
```

#### Grant access to a user
```bash
./gcmanager.py conn grant \
    --connection dev-server \
    --user john.doe
```

#### List all users
Shows all users and their group memberships:
```bash
./gcmanager.py user list
```

#### Delete a user
Removes a user and their associated VNC connection:
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

- [ ] Separate connection management from user creation
  - Currently each user gets a single hardcoded VNC connection
  - Future `conn` command will allow flexible connection management:
    ```bash
    # Planned syntax
    gcmanager.py conn new --type vnc --name dev-server --host 192.168.1.100 --port 5901
    gcmanager.py conn grant --name dev-server --user john.doe
    gcmanager.py conn list
    gcmanager.py conn del --name dev-server
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

PRs implementing any of these features are welcome!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Copyright Roman V. Isaev <rm@isaeff.net> 2024

This software is distributed under the terms of the GNU General Public license, version 3.0.

## Support

For bugs, questions, and discussions please use the [GitHub Issues](https://github.com/burbilog/gcmanager/issues).
