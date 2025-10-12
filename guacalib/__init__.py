"""Guacamole Database Management Library.

This library provides programmatic access to Apache Guacamole database operations,
enabling automated management of users, user groups, connections, and connection
groups through direct MySQL database access. It serves as both a Python library
and the foundation for the guacaman CLI tool.

The library focuses on security, reliability, and comprehensive functionality
for managing Guacamole deployments programmatically. It supports all major
Guacamole features including user management, permission control, connection
configuration, and hierarchical organization.

Key Features:
- Complete user and user group management
- Connection and connection group operations
- Fine-grained permission control
- Hierarchical organization support
- Transaction-based operations
- Comprehensive error handling and validation
- MySQL database connectivity with connection pooling

Example:
    Basic usage for user management:

    >>> from guacalib import GuacamoleDB
    >>>
    >>> # Initialize database connection
    >>> with GuacamoleDB() as db:
    >>>     # Create a new user
    >>>     db.create_user("testuser", "securepassword")
    >>>
    >>>     # Create a VNC connection
    >>>     conn_id = db.create_connection(
    >>>         "vnc", "desktop", "192.168.1.100", "5901", "vncpassword"
    >>>     )
    >>>
    >>>     # Grant user access to connection
    >>>     db.grant_connection_permission("testuser", "USER", conn_id)

Example:
    Connection group management:

    >>> from guacalib import GuacamoleDB
    >>>
    >>> with GuacamoleDB() as db:
    >>>     # Create a connection group
    >>>     group_id = db.create_connection_group("Desktops", "ORGANIZATIONAL")
    >>>
    >>>     # Add connection to group
    >>>     db.create_connection(
    >>>         "vnc", "desktop-pc", "192.168.1.101", "5901", "password",
    >>>         parent_group_id=group_id
    >>>     )
    >>>
    >>>     # Grant group access to user group
    >>>     db.grant_connection_group_permission_to_user(
    >>>         "IT Staff", "USER_GROUP", group_id
    >>>     )

API Overview:
    The main entry point is the `GuacamoleDB` class, which provides methods for:

    - **User Management**: create_user(), delete_existing_user(), modify_user()
    - **User Groups**: create_usergroup(), add_user_to_usergroup()
    - **Connections**: create_connection(), modify_connection(), delete_existing_connection()
    - **Connection Groups**: create_connection_group(), modify_connection_group_parent()
    - **Permissions**: grant_connection_permission(), revoke_connection_permission()
    - **Data Listing**: list_users(), list_connections_with_conngroups_and_parents()

    The GuacamoleDB class implements the context manager protocol for safe
    database connection handling and supports MySQL connection parameters via
    configuration files or direct parameter passing.

Security:
    - All SQL queries use parameterized statements to prevent injection
    - Database credentials stored in separate configuration files
    - Comprehensive input validation and error handling
    - Transaction support for atomic operations
"""

from .db import GuacamoleDB
from .version import VERSION

__version__ = VERSION
__all__ = ["GuacamoleDB"]
