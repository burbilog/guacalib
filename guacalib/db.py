#!/usr/bin/env python3
"""
GuacamoleDB - Facade for backward compatibility.

This class provides backward-compatible API by delegating to specialized repositories.
For new code, consider using the repository classes directly.
"""

import mysql.connector

from .repositories.user import UserRepository
from .repositories.usergroup import UserGroupRepository
from .repositories.connection import ConnectionRepository
from .repositories.connection_group import ConnectionGroupRepository
from .repositories.connection_parameters import CONNECTION_PARAMETERS
from .repositories.user_parameters import USER_PARAMETERS

# SSH tunnel support
try:
    from sshtunnel import SSHTunnelForwarder

    SSH_TUNNEL_AVAILABLE = True
except ImportError:
    SSH_TUNNEL_AVAILABLE = False
    SSHTunnelForwarder = None


class GuacamoleDB:
    """Facade for Guacamole database operations.

    This class provides backward compatibility by delegating to specialized repositories.
    All methods are delegated to the appropriate repository.

    Attributes:
        users: UserRepository for user operations
        usergroups: UserGroupRepository for user group operations
        connections: ConnectionRepository for connection operations
        connection_groups: ConnectionGroupRepository for connection group operations
    """

    # Class attributes for parameter access
    CONNECTION_PARAMETERS = CONNECTION_PARAMETERS
    USER_PARAMETERS = USER_PARAMETERS

    def __init__(self, config_file="db_config.ini", debug=False):
        """Initialize GuacamoleDB with database configuration.

        Args:
            config_file: Path to the configuration file
            debug: Enable debug output
        """
        from .repositories.base import BaseGuacamoleRepository

        self.debug = debug
        self._config_file = config_file
        self.ssh_tunnel = None

        # Read configurations
        self.db_config = BaseGuacamoleRepository.read_config(config_file)
        self.ssh_tunnel_config = BaseGuacamoleRepository.read_ssh_tunnel_config(
            config_file
        )

        # Setup SSH tunnel if configured
        db_connect_config = self.db_config.copy()
        if self.ssh_tunnel_config and self.ssh_tunnel_config.get("enabled"):
            db_connect_config = self._setup_ssh_tunnel(db_connect_config)

        # Create single shared connection
        self.conn = mysql.connector.connect(
            **db_connect_config, charset="utf8mb4", collation="utf8mb4_general_ci"
        )
        self.cursor = self.conn.cursor()

        # Initialize repositories with shared connection
        self.users = UserRepository(
            config_file, debug, self.conn, self.cursor, self.ssh_tunnel
        )
        self.usergroups = UserGroupRepository(
            config_file, debug, self.conn, self.cursor, self.ssh_tunnel
        )
        self.connections = ConnectionRepository(
            config_file, debug, self.conn, self.cursor, self.ssh_tunnel
        )
        self.connection_groups = ConnectionGroupRepository(
            config_file, debug, self.conn, self.cursor, self.ssh_tunnel
        )

    def _setup_ssh_tunnel(self, db_config):
        """Setup SSH tunnel and return modified db_config.

        Args:
            db_config: Original database configuration

        Returns:
            Modified db_config with tunnel settings
        """
        if not SSH_TUNNEL_AVAILABLE:
            print("Error: sshtunnel package is required for SSH tunnel support")
            print("Install it with: pip install sshtunnel")
            import sys

            sys.exit(1)

        db_config = db_config.copy()

        # Build SSH tunnel configuration
        tunnel_config = {
            "ssh_address_or_host": (
                self.ssh_tunnel_config["host"],
                self.ssh_tunnel_config["port"],
            ),
            "ssh_username": self.ssh_tunnel_config["user"],
            "remote_bind_address": (db_config["host"], 3306),
        }

        # Add authentication method
        if self.ssh_tunnel_config.get("private_key"):
            tunnel_config["ssh_pkey"] = self.ssh_tunnel_config["private_key"]
            if self.ssh_tunnel_config.get("private_key_passphrase"):
                tunnel_config["ssh_pkey_password"] = self.ssh_tunnel_config[
                    "private_key_passphrase"
                ]
        elif self.ssh_tunnel_config.get("password"):
            tunnel_config["ssh_password"] = self.ssh_tunnel_config["password"]

        try:
            self.debug_print(f"Creating SSH tunnel to {self.ssh_tunnel_config['host']}")
            self.ssh_tunnel = SSHTunnelForwarder(**tunnel_config)
            self.ssh_tunnel.start()

            # Update MySQL config to use tunnel
            db_config["host"] = "127.0.0.1"
            db_config["port"] = self.ssh_tunnel.local_bind_port

            self.debug_print(
                f"SSH tunnel established on port {self.ssh_tunnel.local_bind_port}"
            )
        except Exception as e:
            print(f"Error creating SSH tunnel: {e}")
            import sys

            sys.exit(1)

        return db_config

    def debug_print(self, *args, **kwargs):
        """Print debug messages if debug mode is enabled."""
        if self.debug:
            print("[DEBUG]", *args, **kwargs)

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit context manager with proper cleanup."""
        # Cleanup database connection
        if self.cursor:
            self.cursor.close()
        if self.conn:
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
                self.conn.close()

        # Close SSH tunnel if it was created
        if self.ssh_tunnel:
            try:
                self.ssh_tunnel.stop()
                self.debug_print("SSH tunnel closed")
            except Exception:
                pass

    # ==================== User methods ====================

    def list_users(self):
        """List all users."""
        return self.users.list_users()

    def user_exists(self, username):
        """Check if a user exists."""
        return self.users.user_exists(username)

    def create_user(self, username, password):
        """Create a new user."""
        return self.users.create_user(username, password)

    def delete_existing_user(self, username):
        """Delete a user."""
        return self.users.delete_existing_user(username)

    def change_user_password(self, username, new_password):
        """Change a user's password."""
        return self.users.change_user_password(username, new_password)

    def modify_user(self, username, param_name, param_value):
        """Modify a user parameter."""
        return self.users.modify_user(username, param_name, param_value)

    def list_users_with_usergroups(self):
        """List all users with their group memberships."""
        return self.users.list_users_with_usergroups()

    # ==================== User group methods ====================

    def list_usergroups(self):
        """List all user groups."""
        return self.usergroups.list_usergroups()

    def usergroup_exists(self, group_name):
        """Check if a user group exists."""
        return self.usergroups.usergroup_exists(group_name)

    def usergroup_exists_by_id(self, group_id):
        """Check if a user group exists by ID."""
        return self.usergroups.usergroup_exists_by_id(group_id)

    def get_usergroup_id(self, group_name):
        """Get user group ID by name."""
        return self.usergroups.get_usergroup_id(group_name)

    def get_usergroup_name_by_id(self, group_id):
        """Get user group name by ID."""
        return self.usergroups.get_usergroup_name_by_id(group_id)

    def resolve_usergroup_id(self, group_name=None, group_id=None):
        """Resolve user group ID from name or ID."""
        return self.usergroups.resolve_usergroup_id(group_name, group_id)

    def create_usergroup(self, group_name):
        """Create a new user group."""
        return self.usergroups.create_usergroup(group_name)

    def delete_existing_usergroup(self, group_name):
        """Delete a user group by name."""
        return self.usergroups.delete_existing_usergroup(group_name)

    def delete_existing_usergroup_by_id(self, group_id):
        """Delete a user group by ID."""
        return self.usergroups.delete_existing_usergroup_by_id(group_id)

    def add_user_to_usergroup(self, username, group_name):
        """Add a user to a user group."""
        return self.usergroups.add_user_to_usergroup(username, group_name)

    def remove_user_from_usergroup(self, username, group_name):
        """Remove a user from a user group."""
        return self.usergroups.remove_user_from_usergroup(username, group_name)

    def list_groups_with_users(self):
        """List all groups with their users."""
        return self.usergroups.list_groups_with_users()

    def list_usergroups_with_users_and_connections(self):
        """List all groups with their users and connections."""
        return self.usergroups.list_usergroups_with_users_and_connections()

    # ==================== Connection methods ====================

    def get_connection_name_by_id(self, connection_id):
        """Get connection name by ID."""
        return self.connections.get_connection_name_by_id(connection_id)

    def resolve_connection_id(self, connection_name=None, connection_id=None):
        """Resolve connection ID from name or ID."""
        return self.connections.resolve_connection_id(connection_name, connection_id)

    def connection_exists(self, connection_name=None, connection_id=None):
        """Check if a connection exists."""
        return self.connections.connection_exists(connection_name, connection_id)

    def create_connection(
        self,
        connection_type,
        connection_name,
        hostname,
        port,
        vnc_password,
        parent_group_id=None,
    ):
        """Create a new connection."""
        return self.connections.create_connection(
            connection_type,
            connection_name,
            hostname,
            port,
            vnc_password,
            parent_group_id,
        )

    def delete_existing_connection(self, connection_name=None, connection_id=None):
        """Delete a connection."""
        return self.connections.delete_existing_connection(
            connection_name, connection_id
        )

    def modify_connection(
        self,
        connection_name=None,
        connection_id=None,
        param_name=None,
        param_value=None,
    ):
        """Modify a connection parameter."""
        return self.connections.modify_connection(
            connection_name, connection_id, param_name, param_value
        )

    def modify_connection_parent_group(
        self, connection_name=None, connection_id=None, group_name=None
    ):
        """Set parent connection group for a connection."""
        return self.connections.modify_connection_parent_group(
            connection_name, connection_id, group_name
        )

    def get_connection_user_permissions(self, connection_name):
        """Get list of users with direct permissions to a connection."""
        return self.connections.get_connection_user_permissions(connection_name)

    def grant_connection_permission(
        self, entity_name, entity_type, connection_id, group_path=None
    ):
        """Grant connection permission to an entity."""
        return self.connections.grant_connection_permission(
            entity_name, entity_type, connection_id, group_path
        )

    def grant_connection_permission_to_user(self, username, connection_name):
        """Grant connection permission to a specific user."""
        return self.connections.grant_connection_permission_to_user(
            username, connection_name
        )

    def revoke_connection_permission_from_user(self, username, connection_name):
        """Revoke connection permission from a specific user."""
        return self.connections.revoke_connection_permission_from_user(
            username, connection_name
        )

    def list_connections_with_conngroups_and_parents(self):
        """List all connections with their groups, parent group, and user permissions."""
        return self.connections.list_connections_with_conngroups_and_parents()

    def get_connection_by_id(self, connection_id):
        """Get a specific connection by its ID."""
        return self.connections.get_connection_by_id(connection_id)

    # ==================== Connection group methods ====================

    def get_connection_group_id_by_name(self, group_name):
        """Get connection group ID by name."""
        return self.connection_groups.get_connection_group_id_by_name(group_name)

    def get_connection_group_id(self, group_path):
        """Resolve nested connection group path to group ID."""
        return self.connection_groups.get_connection_group_id(group_path)

    def get_connection_group_name_by_id(self, group_id):
        """Get connection group name by ID."""
        return self.connection_groups.get_connection_group_name_by_id(group_id)

    def resolve_conngroup_id(self, group_name=None, group_id=None):
        """Resolve connection group ID from name or ID."""
        return self.connection_groups.resolve_conngroup_id(group_name, group_id)

    def connection_group_exists(self, group_name=None, group_id=None):
        """Check if a connection group exists."""
        return self.connection_groups.connection_group_exists(group_name, group_id)

    def _check_connection_group_cycle(self, group_id, parent_id):
        """Check if setting parent_id would create a cycle."""
        return self.connection_groups._check_connection_group_cycle(group_id, parent_id)

    def create_connection_group(self, group_name, parent_group_name=None):
        """Create a new connection group."""
        return self.connection_groups.create_connection_group(
            group_name, parent_group_name
        )

    def delete_connection_group(self, group_name=None, group_id=None):
        """Delete a connection group."""
        return self.connection_groups.delete_connection_group(group_name, group_id)

    def modify_connection_group_parent(
        self, group_name=None, group_id=None, new_parent_name=None
    ):
        """Set parent connection group for a connection group."""
        return self.connection_groups.modify_connection_group_parent(
            group_name, group_id, new_parent_name
        )

    def list_connection_groups(self):
        """List all connection groups."""
        return self.connection_groups.list_connection_groups()

    def get_connection_group_by_id(self, group_id):
        """Get a specific connection group by its ID."""
        return self.connection_groups.get_connection_group_by_id(group_id)

    def debug_connection_permissions(self, connection_name):
        """Debug function to check permissions for a connection."""
        return self.connection_groups.debug_connection_permissions(connection_name)

    def grant_connection_group_permission_to_user(self, username, conngroup_name):
        """Grant connection group permission to a specific user."""
        return self.connection_groups.grant_connection_group_permission_to_user(
            username, conngroup_name
        )

    def revoke_connection_group_permission_from_user(self, username, conngroup_name):
        """Revoke connection group permission from a specific user."""
        return self.connection_groups.revoke_connection_group_permission_from_user(
            username, conngroup_name
        )

    def _atomic_permission_operation(self, operation_func, *args, **kwargs):
        """Execute a database operation with proper error handling."""
        return self.connection_groups._atomic_permission_operation(
            operation_func, *args, **kwargs
        )

    def grant_connection_group_permission_to_user_by_id(self, username, conngroup_id):
        """Grant connection group permission to a specific user by ID."""
        return self.connection_groups.grant_connection_group_permission_to_user_by_id(
            username, conngroup_id
        )

    def revoke_connection_group_permission_from_user_by_id(
        self, username, conngroup_id
    ):
        """Revoke connection group permission from a specific user by ID."""
        return (
            self.connection_groups.revoke_connection_group_permission_from_user_by_id(
                username, conngroup_id
            )
        )

    # ==================== Static utility methods ====================

    @staticmethod
    def read_config(config_file):
        """Read database configuration from file."""
        from .repositories.base import BaseGuacamoleRepository

        return BaseGuacamoleRepository.read_config(config_file)

    @staticmethod
    def validate_positive_id(id_value, entity_type="entity"):
        """Validate that ID is a positive integer."""
        from .repositories.base import BaseGuacamoleRepository

        return BaseGuacamoleRepository.validate_positive_id(id_value, entity_type)

    @staticmethod
    def read_ssh_tunnel_config(config_file):
        """Read SSH tunnel configuration from file or environment variables."""
        from .repositories.base import BaseGuacamoleRepository

        return BaseGuacamoleRepository.read_ssh_tunnel_config(config_file)
