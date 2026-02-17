#!/usr/bin/env python3
"""Connection group repository for Guacamole database operations."""

from typing import Any, Callable, Dict, Optional

import mysql.connector

from .base import BaseGuacamoleRepository
from ..entities import ENTITY_TYPE_USER
from ..exceptions import (
    DatabaseError,
    EntityNotFoundError,
    ValidationError,
    PermissionError,
)


class ConnectionGroupRepository(BaseGuacamoleRepository):
    """Repository for connection group-related database operations."""

    def get_connection_group_id_by_name(self, group_name: str) -> Optional[int]:
        """Get connection_group_id by name from guacamole_connection_group.

        Args:
            group_name: Group name

        Returns:
            int: Group ID or None if group_name is empty

        Raises:
            EntityNotFoundError: If group not found
            DatabaseError: If database operation fails
        """
        try:
            if not group_name:
                return None

            self.cursor.execute(
                """
                SELECT connection_group_id
                FROM guacamole_connection_group
                WHERE connection_group_name = %s
            """,
                (group_name,),
            )
            result = self.cursor.fetchone()
            if not result:
                raise EntityNotFoundError("connection group", group_name)
            return result[0]
        except mysql.connector.Error as e:
            raise DatabaseError(f"Error getting connection group ID: {e}") from e

    def get_connection_group_id(self, group_path: str) -> int:
        """Resolve nested connection group path to group_id.

        Args:
            group_path: Slash-separated group path

        Returns:
            int: Group ID

        Raises:
            EntityNotFoundError: If group not found in path
            DatabaseError: If database operation fails
        """
        try:
            groups = group_path.split("/")
            parent_group_id = None

            self.debug_print(f"Resolving group path: {group_path}")

            for group_name in groups:
                sql = """
                    SELECT connection_group_id
                    FROM guacamole_connection_group
                    WHERE connection_group_name = %s
                """
                params = [group_name]

                if parent_group_id is not None:
                    sql += " AND parent_id = %s"
                    params.append(parent_group_id)
                else:
                    sql += " AND parent_id IS NULL"

                sql += " ORDER BY connection_group_id LIMIT 1"

                self.debug_print(f"Executing SQL:\n{sql}\nWith params: {params}")

                self.cursor.execute(sql, tuple(params))

                result = self.cursor.fetchone()
                if not result:
                    raise EntityNotFoundError(
                        "connection group",
                        group_name,
                        f"Group '{group_name}' not found in path '{group_path}'",
                    )

                parent_group_id = result[0]
                self.debug_print(f"Found group ID {parent_group_id} for '{group_name}'")

            return parent_group_id

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error resolving group path: {e}") from e

    def get_connection_group_name_by_id(self, group_id: int) -> Optional[str]:
        """Get connection group name by ID.

        Args:
            group_id: Group ID

        Returns:
            str: Group name or None if not found
        """
        try:
            self.cursor.execute(
                """
                SELECT connection_group_name
                FROM guacamole_connection_group
                WHERE connection_group_id = %s
            """,
                (group_id,),
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except mysql.connector.Error as e:
            raise DatabaseError(
                f"Error getting connection group name by ID: {e}"
            ) from e

    def resolve_conngroup_id(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> int:
        """Validate inputs and resolve to connection_group_id.

        Args:
            group_name: Group name (optional)
            group_id: Group ID (optional)

        Returns:
            int: Resolved group ID

        Raises:
            ValidationError: If invalid inputs
            EntityNotFoundError: If group not found
            DatabaseError: If database operation fails
        """
        id_query = "SELECT connection_group_id FROM guacamole_connection_group WHERE connection_group_id = %s"
        name_query = "SELECT connection_group_id FROM guacamole_connection_group WHERE connection_group_name = %s"

        return self._resolve_entity_id(
            entity_name=group_name,
            entity_id=group_id,
            entity_type="Connection group",
            id_query=id_query,
            name_query=name_query,
        )

    def connection_group_exists(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> bool:
        """Check if a connection group with the given name or ID exists.

        Args:
            group_name: Group name (optional)
            group_id: Group ID (optional)

        Returns:
            bool: True if group exists
        """
        id_query = "SELECT connection_group_id FROM guacamole_connection_group WHERE connection_group_id = %s"
        name_query = "SELECT connection_group_id FROM guacamole_connection_group WHERE connection_group_name = %s"

        return self._entity_exists(
            entity_name=group_name,
            entity_id=group_id,
            entity_type="Connection group",
            id_query=id_query,
            name_query=name_query,
        )

    def _check_connection_group_cycle(
        self, group_id: int, parent_id: Optional[int]
    ) -> bool:
        """Check if setting parent_id would create a cycle in connection groups.

        Args:
            group_id: Group ID to check
            parent_id: Proposed parent ID

        Returns:
            bool: True if cycle would be created
        """
        if parent_id is None:
            return False

        current_parent = parent_id
        while current_parent is not None:
            if current_parent == group_id:
                return True

            # Get next parent
            self.cursor.execute(
                """
                SELECT parent_id
                FROM guacamole_connection_group
                WHERE connection_group_id = %s
            """,
                (current_parent,),
            )
            result = self.cursor.fetchone()
            current_parent = result[0] if result else None

        return False

    def create_connection_group(
        self, group_name: str, parent_group_name: Optional[str] = None
    ) -> bool:
        """Create a new connection group.

        Args:
            group_name: Name for the new group
            parent_group_name: Parent group name (optional)

        Returns:
            bool: True if successful
        """
        try:
            parent_group_id = None
            if parent_group_name:
                # Get parent group ID if specified
                self.cursor.execute(
                    """
                    SELECT connection_group_id
                    FROM guacamole_connection_group
                    WHERE connection_group_name = %s
                """,
                    (parent_group_name,),
                )
                result = self.cursor.fetchone()
                if not result:
                    raise EntityNotFoundError(
                        "parent connection group", parent_group_name
                    )
                parent_group_id = result[0]

                # Check for cycles
                if self._check_connection_group_cycle(None, parent_group_id):
                    raise ValidationError(
                        f"Parent connection group '{parent_group_name}' is invalid"
                    )

            # Create the new connection group
            self.cursor.execute(
                """
                INSERT INTO guacamole_connection_group
                (connection_group_name, parent_id)
                VALUES (%s, %s)
            """,
                (group_name, parent_group_id),
            )

            # Verify the group was created
            self.cursor.execute(
                """
                SELECT connection_group_id
                FROM guacamole_connection_group
                WHERE connection_group_name = %s
            """,
                (group_name,),
            )
            if not self.cursor.fetchone():
                raise ValidationError(
                    "Failed to create connection group - no ID returned"
                )

            return True

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error creating connection group: {e}") from e

    def delete_connection_group(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> bool:
        """Delete a connection group and update references to it.

        Args:
            group_name: Group name (optional)
            group_id: Group ID (optional)

        Returns:
            bool: True if successful
        """
        try:
            resolved_group_id = self.resolve_conngroup_id(group_name, group_id)

            # Get group name for logging if we only have ID
            if group_name is None:
                group_name = self.get_connection_group_name_by_id(resolved_group_id)

            self.debug_print(
                f"Attempting to delete connection group: {group_name} (ID: {resolved_group_id})"
            )

            # Update any child groups to have NULL parent
            self.debug_print("Updating child groups to have NULL parent...")
            self.cursor.execute(
                """
                UPDATE guacamole_connection_group
                SET parent_id = NULL
                WHERE parent_id = %s
            """,
                (resolved_group_id,),
            )

            # Update any connections to have NULL parent
            self.debug_print("Updating connections to have NULL parent...")
            self.cursor.execute(
                """
                UPDATE guacamole_connection
                SET parent_id = NULL
                WHERE parent_id = %s
            """,
                (resolved_group_id,),
            )

            # Delete the group
            self.debug_print("Deleting connection group...")
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection_group
                WHERE connection_group_id = %s
            """,
                (resolved_group_id,),
            )

            self.debug_print(f"Successfully deleted connection group '{group_name}'")
            return True

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error deleting connection group: {e}") from e

    def modify_connection_group_parent(
        self,
        group_name: Optional[str] = None,
        group_id: Optional[int] = None,
        new_parent_name: Optional[str] = None,
    ) -> bool:
        """Set parent connection group for a connection group with cycle detection.

        Args:
            group_name: Group name (optional)
            group_id: Group ID (optional)
            new_parent_name: New parent group name (optional, None for root)

        Returns:
            bool: True if successful
        """
        try:
            resolved_group_id = self.resolve_conngroup_id(group_name, group_id)

            # Get group name for error messages if we only have ID
            if group_name is None:
                group_name = self.get_connection_group_name_by_id(resolved_group_id)

            # Handle NULL parent (empty string)
            new_parent_id = None
            if new_parent_name:
                # Get new parent ID
                self.cursor.execute(
                    """
                    SELECT connection_group_id
                    FROM guacamole_connection_group
                    WHERE connection_group_name = %s
                """,
                    (new_parent_name,),
                )
                result = self.cursor.fetchone()
                if not result:
                    raise EntityNotFoundError(
                        "parent connection group", new_parent_name
                    )
                new_parent_id = result[0]

                # Check for cycles
                if self._check_connection_group_cycle(resolved_group_id, new_parent_id):
                    raise ValidationError(
                        "Setting parent would create a cycle in connection groups"
                    )

            # Update the parent
            self.cursor.execute(
                """
                UPDATE guacamole_connection_group
                SET parent_id = %s
                WHERE connection_group_id = %s
            """,
                (new_parent_id, resolved_group_id),
            )

            if self.cursor.rowcount == 0:
                raise ValidationError(
                    f"Failed to update parent group for '{group_name}'"
                )

            return True

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error modifying connection group parent: {e}") from e

    def list_connection_groups(self) -> Dict[str, Dict[str, Any]]:
        """List all connection groups with their connections and parent groups.

        Returns:
            dict: Dictionary mapping group names to group info
        """
        try:
            self.cursor.execute(
                """
                SELECT
                    cg.connection_group_id,
                    cg.connection_group_name,
                    cg.parent_id,
                    p.connection_group_name as parent_name,
                    GROUP_CONCAT(DISTINCT c.connection_name) as connections
                FROM guacamole_connection_group cg
                LEFT JOIN guacamole_connection_group p ON cg.parent_id = p.connection_group_id
                LEFT JOIN guacamole_connection c ON cg.connection_group_id = c.parent_id
                GROUP BY cg.connection_group_id
                ORDER BY cg.connection_group_name
            """
            )

            groups = {}
            for row in self.cursor.fetchall():
                group_id = row[0]
                group_name = row[1]
                parent_id = row[2]
                parent_name = row[3]
                connections = row[4].split(",") if row[4] else []

                groups[group_name] = {
                    "id": group_id,
                    "parent": parent_name if parent_name else "ROOT",
                    "connections": connections,
                }
            return groups
        except mysql.connector.Error as e:
            raise DatabaseError(f"Error listing groups: {e}") from e

    def get_connection_group_by_id(
        self, group_id: int
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get a specific connection group by its ID.

        Args:
            group_id: Group ID

        Returns:
            dict: Dictionary with group info or None if not found
        """
        try:
            self.cursor.execute(
                """
                SELECT
                    cg.connection_group_id,
                    cg.connection_group_name,
                    cg.parent_id,
                    p.connection_group_name as parent_name,
                    GROUP_CONCAT(DISTINCT c.connection_name) as connections
                FROM guacamole_connection_group cg
                LEFT JOIN guacamole_connection_group p ON cg.parent_id = p.connection_group_id
                LEFT JOIN guacamole_connection c ON cg.connection_group_id = c.parent_id
                WHERE cg.connection_group_id = %s
                GROUP BY cg.connection_group_id
            """,
                (group_id,),
            )

            row = self.cursor.fetchone()
            if not row:
                return None

            group_id = row[0]
            group_name = row[1]
            parent_id = row[2]
            parent_name = row[3]
            connections = row[4].split(",") if row[4] else []

            return {
                group_name: {
                    "id": group_id,
                    "parent": parent_name if parent_name else "ROOT",
                    "connections": connections,
                }
            }
        except mysql.connector.Error as e:
            raise DatabaseError(f"Error getting connection group by ID: {e}") from e

    def debug_connection_permissions(self, connection_name: str) -> None:
        """Debug function to check permissions for a connection.

        Args:
            connection_name: Connection name to debug
        """
        try:
            self.debug_print(f"Checking permissions for connection '{connection_name}'")

            # Get connection ID
            self.cursor.execute(
                """
                SELECT connection_id FROM guacamole_connection
                WHERE connection_name = %s
            """,
                (connection_name,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"Connection '{connection_name}' not found")
                return
            connection_id = result[0]
            self.debug_print(f"Connection ID: {connection_id}")

            # Check all permissions
            self.cursor.execute(
                """
                SELECT cp.entity_id, e.name, e.type, cp.permission
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s
            """,
                (connection_id,),
            )

            permissions = self.cursor.fetchall()
            if not permissions:
                self.debug_print(
                    f"No permissions found for connection '{connection_name}'"
                )
            else:
                self.debug_print(f"Found {len(permissions)} permissions:")
                for perm in permissions:
                    entity_id, name, entity_type, permission = perm
                    self.debug_print(
                        f"  Entity ID: {entity_id}, Name: {name}, Type: {entity_type}, Permission: {permission}"
                    )

            # Specifically check user permissions
            self.cursor.execute(
                """
                SELECT e.name
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s AND e.type = %s
            """,
                (connection_id, ENTITY_TYPE_USER),
            )

            user_permissions = self.cursor.fetchall()
            if not user_permissions:
                self.debug_print(
                    f"No user permissions found for connection '{connection_name}'"
                )
            else:
                self.debug_print(f"Found {len(user_permissions)} user permissions:")
                for perm in user_permissions:
                    self.debug_print(f"  User: {perm[0]}")

            self.debug_print("End of debug info")

        except mysql.connector.Error as e:
            self.debug_print(f"Error debugging permissions: {e}")

    def grant_connection_group_permission_to_user(
        self, username: str, conngroup_name: str
    ) -> bool:
        """Grant connection group permission to a specific user.

        Args:
            username: Username
            conngroup_name: Connection group name

        Returns:
            bool: True if successful
        """
        if not username or not isinstance(username, str):
            raise ValidationError("Username must be a non-empty string")
        if not conngroup_name or not isinstance(conngroup_name, str):
            raise ValidationError("Connection group name must be a non-empty string")

        try:
            # Get connection group ID
            self.cursor.execute(
                """
                SELECT connection_group_id, connection_group_name FROM guacamole_connection_group
                WHERE connection_group_name = %s
                LIMIT 1
            """,
                (conngroup_name,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(
                    f"Connection group lookup failed for: {conngroup_name}"
                )
                raise EntityNotFoundError("connection group", conngroup_name)
            connection_group_id, actual_conngroup_name = result

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id, name FROM guacamole_entity
                WHERE name = %s AND type = %s
                LIMIT 1
            """,
                (username, ENTITY_TYPE_USER),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"User lookup failed for: {username}")
                raise EntityNotFoundError("user", username)
            entity_id, actual_username = result

            # Check if permission already exists
            self.cursor.execute(
                """
                SELECT permission FROM guacamole_connection_group_permission
                WHERE entity_id = %s AND connection_group_id = %s
                LIMIT 1
            """,
                (entity_id, connection_group_id),
            )
            existing_permission = self.cursor.fetchone()
            if existing_permission:
                permission_type = existing_permission[0]
                if permission_type == "READ":
                    raise PermissionError(
                        f"User '{actual_username}' already has permission for connection group '{actual_conngroup_name}'",
                        username=actual_username,
                        resource_type="connection_group",
                        resource_name=actual_conngroup_name,
                    )
                else:
                    self.debug_print(
                        f"Updating existing permission '{permission_type}' to 'READ' for user '{actual_username}'"
                    )

            # Grant permission
            if existing_permission and existing_permission[0] != "READ":
                self.cursor.execute(
                    """
                    UPDATE guacamole_connection_group_permission
                    SET permission = 'READ'
                    WHERE entity_id = %s AND connection_group_id = %s
                """,
                    (entity_id, connection_group_id),
                )
                self.debug_print(
                    f"Updated permission to 'READ' for user '{actual_username}' on connection group '{actual_conngroup_name}'"
                )
            else:
                self.cursor.execute(
                    """
                    INSERT INTO guacamole_connection_group_permission
                    (entity_id, connection_group_id, permission)
                    VALUES (%s, %s, 'READ')
                """,
                    (entity_id, connection_group_id),
                )
                self.debug_print(
                    f"Granted 'READ' permission to user '{actual_username}' for connection group '{actual_conngroup_name}'"
                )

            return True
        except mysql.connector.Error as e:
            raise DatabaseError(
                f"Database error granting connection group permission for user '{username}' on group '{conngroup_name}': {e}"
            ) from e

    def revoke_connection_group_permission_from_user(
        self, username: str, conngroup_name: str
    ) -> bool:
        """Revoke connection group permission from a specific user.

        Args:
            username: Username
            conngroup_name: Connection group name

        Returns:
            bool: True if successful
        """
        if not username or not isinstance(username, str):
            raise ValidationError("Username must be a non-empty string")
        if not conngroup_name or not isinstance(conngroup_name, str):
            raise ValidationError("Connection group name must be a non-empty string")

        try:
            # Get connection group ID
            self.cursor.execute(
                """
                SELECT connection_group_id, connection_group_name FROM guacamole_connection_group
                WHERE connection_group_name = %s
                LIMIT 1
            """,
                (conngroup_name,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(
                    f"Connection group lookup failed for: {conngroup_name}"
                )
                raise EntityNotFoundError("connection group", conngroup_name)
            connection_group_id, actual_conngroup_name = result

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id, name FROM guacamole_entity
                WHERE name = %s AND type = %s
                LIMIT 1
            """,
                (username, ENTITY_TYPE_USER),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"User lookup failed for: {username}")
                raise EntityNotFoundError("user", username)
            entity_id, actual_username = result

            # Check if permission exists
            self.cursor.execute(
                """
                SELECT permission FROM guacamole_connection_group_permission
                WHERE entity_id = %s AND connection_group_id = %s
                LIMIT 1
            """,
                (entity_id, connection_group_id),
            )
            existing_permission = self.cursor.fetchone()
            if not existing_permission:
                raise PermissionError(
                    f"User '{actual_username}' has no permission for connection group '{actual_conngroup_name}'",
                    username=actual_username,
                    resource_type="connection_group",
                    resource_name=actual_conngroup_name,
                )

            permission_type = existing_permission[0]
            self.debug_print(
                f"Revoking '{permission_type}' permission from user '{actual_username}' for connection group '{actual_conngroup_name}'"
            )

            # Revoke permission
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection_group_permission
                WHERE entity_id = %s AND connection_group_id = %s
                LIMIT 1
            """,
                (entity_id, connection_group_id),
            )

            if self.cursor.rowcount == 0:
                raise PermissionError(
                    "Failed to revoke permission - no rows affected. Permission may have been removed by another operation."
                )

            self.debug_print(
                f"Successfully revoked '{permission_type}' permission from user '{actual_username}' for connection group '{actual_conngroup_name}'"
            )
            return True
        except mysql.connector.Error as e:
            raise DatabaseError(
                f"Database error revoking connection group permission for user '{username}' on group '{conngroup_name}': {e}"
            ) from e

    def _atomic_permission_operation(
        self, operation_func: Callable, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute a database operation with proper error handling and validation.

        Args:
            operation_func: Function to execute
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function

        Returns:
            Result of operation_func
        """
        try:
            return operation_func(*args, **kwargs)
        except mysql.connector.Error as e:
            raise DatabaseError(
                f"Database error during permission operation: {e}"
            ) from e

    def grant_connection_group_permission_to_user_by_id(
        self, username: str, conngroup_id: int
    ) -> bool:
        """Grant connection group permission to a specific user by connection group ID.

        Args:
            username: Username
            conngroup_id: Connection group ID

        Returns:
            bool: True if successful
        """
        if not username or not isinstance(username, str):
            raise ValidationError("Username must be a non-empty string")
        if (
            conngroup_id is None
            or not isinstance(conngroup_id, int)
            or conngroup_id <= 0
        ):
            raise ValidationError("Connection group ID must be a positive integer")

        try:
            # Get connection group name for error messages
            self.cursor.execute(
                """
                SELECT connection_group_id, connection_group_name FROM guacamole_connection_group
                WHERE connection_group_id = %s
                LIMIT 1
            """,
                (conngroup_id,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(
                    f"Connection group ID lookup failed for: {conngroup_id}"
                )
                raise EntityNotFoundError("connection group", str(conngroup_id))
            actual_conngroup_id, conngroup_name = result

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id, name FROM guacamole_entity
                WHERE name = %s AND type = %s
                LIMIT 1
            """,
                (username, ENTITY_TYPE_USER),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"User lookup failed for: {username}")
                raise EntityNotFoundError("user", username)
            entity_id, actual_username = result

            # Check if permission already exists
            self.cursor.execute(
                """
                SELECT permission FROM guacamole_connection_group_permission
                WHERE entity_id = %s AND connection_group_id = %s
                LIMIT 1
            """,
                (entity_id, actual_conngroup_id),
            )
            existing_permission = self.cursor.fetchone()
            if existing_permission:
                permission_type = existing_permission[0]
                if permission_type == "READ":
                    raise PermissionError(
                        f"User '{actual_username}' already has permission for connection group ID '{actual_conngroup_id}'",
                        username=actual_username,
                        resource_type="connection_group",
                        resource_name=str(actual_conngroup_id),
                    )
                else:
                    self.debug_print(
                        f"Updating existing permission '{permission_type}' to 'READ' for user '{actual_username}'"
                    )

            # Grant permission
            if existing_permission and existing_permission[0] != "READ":
                self.cursor.execute(
                    """
                    UPDATE guacamole_connection_group_permission
                    SET permission = 'READ'
                    WHERE entity_id = %s AND connection_group_id = %s
                """,
                    (entity_id, actual_conngroup_id),
                )
                self.debug_print(
                    f"Updated permission to 'READ' for user '{actual_username}' on connection group ID '{actual_conngroup_id}'"
                )
            else:
                self.cursor.execute(
                    """
                    INSERT INTO guacamole_connection_group_permission
                    (entity_id, connection_group_id, permission)
                    VALUES (%s, %s, 'READ')
                """,
                    (entity_id, actual_conngroup_id),
                )
                self.debug_print(
                    f"Granted 'READ' permission to user '{actual_username}' for connection group ID '{actual_conngroup_id}'"
                )

            return True
        except mysql.connector.Error as e:
            raise DatabaseError(
                f"Database error granting connection group permission for user '{username}' on group ID '{conngroup_id}': {e}"
            ) from e

    def revoke_connection_group_permission_from_user_by_id(
        self, username: str, conngroup_id: int
    ) -> bool:
        """Revoke connection group permission from a specific user by connection group ID.

        Args:
            username: Username
            conngroup_id: Connection group ID

        Returns:
            bool: True if successful
        """
        if not username or not isinstance(username, str):
            raise ValidationError("Username must be a non-empty string")
        if (
            conngroup_id is None
            or not isinstance(conngroup_id, int)
            or conngroup_id <= 0
        ):
            raise ValidationError("Connection group ID must be a positive integer")

        try:
            # Get connection group name for error messages
            self.cursor.execute(
                """
                SELECT connection_group_id, connection_group_name FROM guacamole_connection_group
                WHERE connection_group_id = %s
                LIMIT 1
            """,
                (conngroup_id,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(
                    f"Connection group ID lookup failed for: {conngroup_id}"
                )
                raise EntityNotFoundError("connection group", str(conngroup_id))
            actual_conngroup_id, conngroup_name = result

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id, name FROM guacamole_entity
                WHERE name = %s AND type = %s
                LIMIT 1
            """,
                (username, ENTITY_TYPE_USER),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"User lookup failed for: {username}")
                raise EntityNotFoundError("user", username)
            entity_id, actual_username = result

            # Check if permission exists
            self.cursor.execute(
                """
                SELECT permission FROM guacamole_connection_group_permission
                WHERE entity_id = %s AND connection_group_id = %s
                LIMIT 1
            """,
                (entity_id, actual_conngroup_id),
            )
            existing_permission = self.cursor.fetchone()
            if not existing_permission:
                raise PermissionError(
                    f"User '{actual_username}' has no permission for connection group ID '{actual_conngroup_id}'",
                    username=actual_username,
                    resource_type="connection_group",
                    resource_name=str(actual_conngroup_id),
                )

            permission_type = existing_permission[0]
            self.debug_print(
                f"Revoking '{permission_type}' permission from user '{actual_username}' for connection group ID '{actual_conngroup_id}'"
            )

            # Revoke permission
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection_group_permission
                WHERE entity_id = %s AND connection_group_id = %s
                LIMIT 1
            """,
                (entity_id, actual_conngroup_id),
            )

            if self.cursor.rowcount == 0:
                raise PermissionError(
                    "Failed to revoke permission - no rows affected. Permission may have been removed by another operation."
                )

            self.debug_print(
                f"Successfully revoked '{permission_type}' permission from user '{actual_username}' for connection group ID '{actual_conngroup_id}'"
            )
            return True
        except mysql.connector.Error as e:
            raise DatabaseError(
                f"Database error revoking connection group permission for user '{username}' on group ID '{conngroup_id}': {e}"
            ) from e
