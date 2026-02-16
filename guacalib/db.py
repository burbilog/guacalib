#!/usr/bin/env python3
"""
GuacamoleDB - Facade for backward compatibility.

This class provides backward-compatible API by delegating to specialized repositories.
For new code, consider using the repository classes directly.
"""

from typing import Any, Dict, List, Optional

import mysql.connector

from .repositories.base import BaseGuacamoleRepository
from .repositories.user import UserRepository
from .repositories.usergroup import UserGroupRepository
from .repositories.connection import ConnectionRepository
from .repositories.connection_group import ConnectionGroupRepository
from .repositories.connection_parameters import CONNECTION_PARAMETERS
from .repositories.user_parameters import USER_PARAMETERS

from .ssh_tunnel import create_ssh_tunnel, close_ssh_tunnel


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

    def __init__(self, config_file: str = "~/.guacaman.ini", debug: bool = False) -> None:
        """Initialize GuacamoleDB with database configuration.

        Args:
            config_file: Path to the configuration file
            debug: Enable debug output
        """
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

    def _setup_ssh_tunnel(self, db_config: Dict[str, str]) -> Dict[str, Any]:
        """Setup SSH tunnel and return modified db_config.

        Args:
            db_config: Original database configuration

        Returns:
            Modified db_config with tunnel settings
        """
        self.ssh_tunnel, db_config = create_ssh_tunnel(
            self.ssh_tunnel_config, db_config, self.debug_print
        )
        return db_config

    def debug_print(self, *args: Any, **kwargs: Any) -> None:
        """Print debug messages if debug mode is enabled."""
        if self.debug:
            print("[DEBUG]", *args, **kwargs)

    def __enter__(self) -> "GuacamoleDB":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        """Exit context manager with proper cleanup."""
        # Determine if we should commit or rollback
        # Commit on: no exception, or SystemExit with code 0
        # Rollback on: any other exception, or SystemExit with non-zero code
        should_commit = False
        if exc_type is None:
            should_commit = True
        elif exc_type is SystemExit:
            # sys.exit(0) should commit, sys.exit(1) should rollback
            should_commit = exc_value is not None and exc_value.code == 0

        # Cleanup database connection
        if self.cursor:
            self.cursor.close()
        if self.conn:
            try:
                if should_commit:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
                self.conn.close()

        # Close SSH tunnel if it was created
        close_ssh_tunnel(self.ssh_tunnel, self.debug_print)

    # ==================== User methods ====================

    def list_users(self) -> List[str]:
        """List all users."""
        return self.users.list_users()

    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        return self.users.user_exists(username)

    def create_user(self, username: str, password: str) -> bool:
        """Create a new user."""
        return self.users.create_user(username, password)

    def delete_existing_user(self, username: str) -> bool:
        """Delete a user."""
        return self.users.delete_existing_user(username)

    def change_user_password(self, username: str, new_password: str) -> bool:
        """Change a user's password."""
        return self.users.change_user_password(username, new_password)

    def modify_user(self, username: str, param_name: str, param_value: str) -> bool:
        """Modify a user parameter."""
        return self.users.modify_user(username, param_name, param_value)

    def list_users_with_usergroups(self) -> Dict[str, Dict[str, List[str]]]:
        """List all users with their group memberships."""
        return self.users.list_users_with_usergroups()

    # ==================== User group methods ====================

    def list_usergroups(self) -> List[str]:
        """List all user groups."""
        return self.usergroups.list_usergroups()

    def usergroup_exists(self, group_name: str) -> bool:
        """Check if a user group exists."""
        return self.usergroups.usergroup_exists(group_name)

    def usergroup_exists_by_id(self, group_id: int) -> bool:
        """Check if a user group exists by ID."""
        return self.usergroups.usergroup_exists_by_id(group_id)

    def get_usergroup_id(self, group_name: str) -> int:
        """Get user group ID by name."""
        return self.usergroups.get_usergroup_id(group_name)

    def get_usergroup_name_by_id(self, group_id: int) -> Optional[str]:
        """Get user group name by ID."""
        return self.usergroups.get_usergroup_name_by_id(group_id)

    def resolve_usergroup_id(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> int:
        """Resolve user group ID from name or ID."""
        return self.usergroups.resolve_usergroup_id(group_name, group_id)

    def create_usergroup(self, group_name: str) -> bool:
        """Create a new user group."""
        return self.usergroups.create_usergroup(group_name)

    def delete_existing_usergroup(self, group_name: str) -> bool:
        """Delete a user group by name."""
        return self.usergroups.delete_existing_usergroup(group_name)

    def delete_existing_usergroup_by_id(self, group_id: int) -> bool:
        """Delete a user group by ID."""
        return self.usergroups.delete_existing_usergroup_by_id(group_id)

    def add_user_to_usergroup(self, username: str, group_name: str) -> bool:
        """Add a user to a user group."""
        return self.usergroups.add_user_to_usergroup(username, group_name)

    def remove_user_from_usergroup(self, username: str, group_name: str) -> bool:
        """Remove a user from a user group."""
        return self.usergroups.remove_user_from_usergroup(username, group_name)

    def list_groups_with_users(self) -> Dict[str, Dict[str, Any]]:
        """List all groups with their users."""
        return self.usergroups.list_groups_with_users()

    def list_usergroups_with_users_and_connections(self) -> Dict[str, Dict[str, Any]]:
        """List all groups with their users and connections."""
        return self.usergroups.list_usergroups_with_users_and_connections()

    # ==================== Connection methods ====================

    def get_connection_name_by_id(self, connection_id: int) -> Optional[str]:
        """Get connection name by ID."""
        return self.connections.get_connection_name_by_id(connection_id)

    def resolve_connection_id(
        self, connection_name: Optional[str] = None, connection_id: Optional[int] = None
    ) -> int:
        """Resolve connection ID from name or ID."""
        return self.connections.resolve_connection_id(connection_name, connection_id)

    def connection_exists(
        self, connection_name: Optional[str] = None, connection_id: Optional[int] = None
    ) -> bool:
        """Check if a connection exists."""
        return self.connections.connection_exists(connection_name, connection_id)

    def create_connection(
        self,
        connection_type: str,
        connection_name: str,
        hostname: str,
        port: int,
        vnc_password: str,
        parent_group_id: Optional[int] = None,
    ) -> int:
        """Create a new connection."""
        return self.connections.create_connection(
            connection_type,
            connection_name,
            hostname,
            port,
            vnc_password,
            parent_group_id,
        )

    def delete_existing_connection(
        self, connection_name: Optional[str] = None, connection_id: Optional[int] = None
    ) -> bool:
        """Delete a connection."""
        return self.connections.delete_existing_connection(
            connection_name, connection_id
        )

    def modify_connection(
        self,
        connection_name: Optional[str] = None,
        connection_id: Optional[int] = None,
        param_name: Optional[str] = None,
        param_value: Optional[str] = None,
    ) -> bool:
        """Modify a connection parameter."""
        return self.connections.modify_connection(
            connection_name, connection_id, param_name, param_value
        )

    def modify_connection_parent_group(
        self,
        connection_name: Optional[str] = None,
        connection_id: Optional[int] = None,
        group_name: Optional[str] = None,
    ) -> bool:
        """Set parent connection group for a connection."""
        return self.connections.modify_connection_parent_group(
            connection_name, connection_id, group_name
        )

    def get_connection_user_permissions(self, connection_name: str) -> List[str]:
        """Get list of users with direct permissions to a connection."""
        return self.connections.get_connection_user_permissions(connection_name)

    def grant_connection_permission(
        self,
        entity_name: str,
        entity_type: str,
        connection_id: int,
        group_path: Optional[str] = None,
    ) -> bool:
        """Grant connection permission to an entity."""
        return self.connections.grant_connection_permission(
            entity_name, entity_type, connection_id, group_path
        )

    def grant_connection_permission_to_user(self, username: str, connection_name: str) -> bool:
        """Grant connection permission to a specific user."""
        return self.connections.grant_connection_permission_to_user(
            username, connection_name
        )

    def revoke_connection_permission_from_user(self, username: str, connection_name: str) -> bool:
        """Revoke connection permission from a specific user."""
        return self.connections.revoke_connection_permission_from_user(
            username, connection_name
        )

    def list_connections_with_conngroups_and_parents(self) -> Dict[str, Dict[str, Any]]:
        """List all connections with their groups, parent group, and user permissions."""
        return self.connections.list_connections_with_conngroups_and_parents()

    def get_connection_by_id(self, connection_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific connection by its ID."""
        return self.connections.get_connection_by_id(connection_id)

    # ==================== Connection group methods ====================

    def get_connection_group_id_by_name(self, group_name: str) -> Optional[int]:
        """Get connection group ID by name."""
        return self.connection_groups.get_connection_group_id_by_name(group_name)

    def get_connection_group_id(self, group_path: str) -> int:
        """Resolve nested connection group path to group ID."""
        return self.connection_groups.get_connection_group_id(group_path)

    def get_connection_group_name_by_id(self, group_id: int) -> Optional[str]:
        """Get connection group name by ID."""
        return self.connection_groups.get_connection_group_name_by_id(group_id)

    def resolve_conngroup_id(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> int:
        """Resolve connection group ID from name or ID."""
        return self.connection_groups.resolve_conngroup_id(group_name, group_id)

    def connection_group_exists(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> bool:
        """Check if a connection group exists."""
        return self.connection_groups.connection_group_exists(group_name, group_id)

    def _check_connection_group_cycle(self, group_id: int, parent_id: Optional[int]) -> bool:
        """Check if setting parent_id would create a cycle."""
        return self.connection_groups._check_connection_group_cycle(group_id, parent_id)

    def create_connection_group(
        self, group_name: str, parent_group_name: Optional[str] = None
    ) -> bool:
        """Create a new connection group."""
        return self.connection_groups.create_connection_group(
            group_name, parent_group_name
        )

    def delete_connection_group(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> bool:
        """Delete a connection group."""
        return self.connection_groups.delete_connection_group(group_name, group_id)

    def modify_connection_group_parent(
        self,
        group_name: Optional[str] = None,
        group_id: Optional[int] = None,
        new_parent_name: Optional[str] = None,
    ) -> bool:
        """Set parent connection group for a connection group."""
        return self.connection_groups.modify_connection_group_parent(
            group_name, group_id, new_parent_name
        )

    def list_connection_groups(self) -> Dict[str, Dict[str, Any]]:
        """List all connection groups."""
        return self.connection_groups.list_connection_groups()

    def get_connection_group_by_id(self, group_id: int) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get a specific connection group by its ID."""
        return self.connection_groups.get_connection_group_by_id(group_id)

    def debug_connection_permissions(self, connection_name: str) -> None:
        """Debug function to check permissions for a connection."""
        return self.connection_groups.debug_connection_permissions(connection_name)

    def grant_connection_group_permission_to_user(
        self, username: str, conngroup_name: str
    ) -> bool:
        """Grant connection group permission to a specific user."""
        return self.connection_groups.grant_connection_group_permission_to_user(
            username, conngroup_name
        )

    def revoke_connection_group_permission_from_user(
        self, username: str, conngroup_name: str
    ) -> bool:
        """Revoke connection group permission from a specific user."""
        return self.connection_groups.revoke_connection_group_permission_from_user(
            username, conngroup_name
        )

    def _atomic_permission_operation(self, operation_func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute a database operation with proper error handling."""
        return self.connection_groups._atomic_permission_operation(
            operation_func, *args, **kwargs
        )

    def grant_connection_group_permission_to_user_by_id(
        self, username: str, conngroup_id: int
    ) -> bool:
        """Grant connection group permission to a specific user by ID."""
        return self.connection_groups.grant_connection_group_permission_to_user_by_id(
            username, conngroup_id
        )

    def revoke_connection_group_permission_from_user_by_id(
        self, username: str, conngroup_id: int
    ) -> bool:
        """Revoke connection group permission from a specific user by ID."""
        return (
            self.connection_groups.revoke_connection_group_permission_from_user_by_id(
                username, conngroup_id
            )
        )

    # ==================== Static utility methods ====================

    @staticmethod
    def read_config(config_file: str) -> Dict[str, str]:
        """Read database configuration from file."""
        return BaseGuacamoleRepository.read_config(config_file)

    @staticmethod
    def validate_positive_id(id_value: Optional[int], entity_type: str = "entity") -> Optional[int]:
        """Validate that ID is a positive integer."""
        return BaseGuacamoleRepository.validate_positive_id(id_value, entity_type)

    @staticmethod
    def read_ssh_tunnel_config(config_file: str) -> Optional[Dict[str, Any]]:
        """Read SSH tunnel configuration from file or environment variables."""
        return BaseGuacamoleRepository.read_ssh_tunnel_config(config_file)
