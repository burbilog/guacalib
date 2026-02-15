#!/usr/bin/env python3
"""Connection repository for Guacamole database operations."""

import mysql.connector

from .base import BaseGuacamoleRepository
from .connection_parameters import CONNECTION_PARAMETERS
from ..exceptions import (
    DatabaseError,
    EntityNotFoundError,
    ValidationError,
    PermissionError,
)


class ConnectionRepository(BaseGuacamoleRepository):
    """Repository for connection-related database operations."""

    CONNECTION_PARAMETERS = CONNECTION_PARAMETERS

    def get_connection_name_by_id(self, connection_id):
        """Get connection name by ID.

        Args:
            connection_id: Connection ID

        Returns:
            str: Connection name or None if not found
        """
        try:
            self.cursor.execute(
                """
                SELECT connection_name
                FROM guacamole_connection
                WHERE connection_id = %s
            """,
                (connection_id,),
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except mysql.connector.Error as e:
            raise DatabaseError(f"Error getting connection name by ID: {e}") from e

    def resolve_connection_id(self, connection_name=None, connection_id=None):
        """Validate inputs and resolve to connection_id.

        Args:
            connection_name: Connection name (optional)
            connection_id: Connection ID (optional)

        Returns:
            int: Resolved connection ID

        Raises:
            ValidationError: If invalid inputs
            EntityNotFoundError: If connection not found
            DatabaseError: If database operation fails
        """
        id_query = (
            "SELECT connection_id FROM guacamole_connection WHERE connection_id = %s"
        )
        name_query = (
            "SELECT connection_id FROM guacamole_connection WHERE connection_name = %s"
        )

        return self._resolve_entity_id(
            entity_name=connection_name,
            entity_id=connection_id,
            entity_type="Connection",
            id_query=id_query,
            name_query=name_query,
        )

    def connection_exists(self, connection_name=None, connection_id=None):
        """Check if a connection with the given name or ID exists.

        Args:
            connection_name: Connection name (optional)
            connection_id: Connection ID (optional)

        Returns:
            bool: True if connection exists
        """
        id_query = (
            "SELECT connection_id FROM guacamole_connection WHERE connection_id = %s"
        )
        name_query = (
            "SELECT connection_id FROM guacamole_connection WHERE connection_name = %s"
        )

        return self._entity_exists(
            entity_name=connection_name,
            entity_id=connection_id,
            entity_type="Connection",
            id_query=id_query,
            name_query=name_query,
        )

    def create_connection(
        self,
        connection_type,
        connection_name,
        hostname,
        port,
        vnc_password,
        parent_group_id=None,
    ):
        """Create a new connection.

        Args:
            connection_type: Protocol type (e.g., 'vnc')
            connection_name: Name for the connection
            hostname: Hostname or IP address
            port: Port number
            vnc_password: VNC password
            parent_group_id: Parent group ID (optional)

        Returns:
            int: Connection ID

        Raises:
            ValidationError: If missing required parameters or connection exists
            DatabaseError: If database operation fails
        """
        if not all([connection_name, hostname, port]):
            raise ValidationError("Missing required connection parameters")

        if self.connection_exists(connection_name):
            raise ValidationError(f"Connection '{connection_name}' already exists")

        try:
            # Create connection
            self.cursor.execute(
                """
                INSERT INTO guacamole_connection
                (connection_name, protocol, parent_id)
                VALUES (%s, %s, %s)
            """,
                (connection_name, connection_type, parent_group_id),
            )

            # Get connection_id
            self.cursor.execute(
                """
                SELECT connection_id FROM guacamole_connection
                WHERE connection_name = %s
            """,
                (connection_name,),
            )
            connection_id = self.cursor.fetchone()[0]

            # Create connection parameters
            params = [
                ("hostname", hostname),
                ("port", port),
                ("password", vnc_password),
            ]

            for param_name, param_value in params:
                self.cursor.execute(
                    """
                    INSERT INTO guacamole_connection_parameter
                    (connection_id, parameter_name, parameter_value)
                    VALUES (%s, %s, %s)
                """,
                    (connection_id, param_name, param_value),
                )

            return connection_id

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error creating VNC connection: {e}") from e

    def delete_existing_connection(self, connection_name=None, connection_id=None):
        """Delete a connection and all its associated data.

        Args:
            connection_name: Connection name (optional)
            connection_id: Connection ID (optional)
        """
        try:
            resolved_connection_id = self.resolve_connection_id(
                connection_name, connection_id
            )

            # Get connection name for logging if we only have ID
            if connection_name is None:
                connection_name = self.get_connection_name_by_id(resolved_connection_id)

            self.debug_print(
                f"Attempting to delete connection: {connection_name} (ID: {resolved_connection_id})"
            )

            # Delete connection history
            self.debug_print("Deleting connection history...")
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection_history
                WHERE connection_id = %s
            """,
                (resolved_connection_id,),
            )

            # Delete connection parameters
            self.debug_print("Deleting connection parameters...")
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection_parameter
                WHERE connection_id = %s
            """,
                (resolved_connection_id,),
            )

            # Delete connection permissions
            self.debug_print("Deleting connection permissions...")
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection_permission
                WHERE connection_id = %s
            """,
                (resolved_connection_id,),
            )

            # Finally delete the connection
            self.debug_print("Deleting connection...")
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection
                WHERE connection_id = %s
            """,
                (resolved_connection_id,),
            )

            # Commit the transaction
            self.debug_print("Committing transaction...")
            self.conn.commit()
            self.debug_print(f"Successfully deleted connection '{connection_name}'")

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error deleting existing connection: {e}") from e

    def modify_connection(
        self,
        connection_name=None,
        connection_id=None,
        param_name=None,
        param_value=None,
    ):
        """Modify a connection parameter.

        Args:
            connection_name: Connection name (optional)
            connection_id: Connection ID (optional)
            param_name: Parameter name to modify
            param_value: New parameter value

        Returns:
            bool: True if successful
        """
        try:
            # Validate parameter name against whitelist (prevents SQL injection)
            self._validate_param_name(param_name, self.CONNECTION_PARAMETERS)

            resolved_connection_id = self.resolve_connection_id(
                connection_name, connection_id
            )

            param_info = self.CONNECTION_PARAMETERS[param_name]
            param_table = param_info["table"]

            # Update the parameter based on which table it belongs to
            if param_table == "connection":
                # Validate parameter value based on type
                if param_info["type"] == "int":
                    try:
                        param_value = int(param_value)
                    except ValueError:
                        raise ValidationError(
                            f"Parameter {param_name} must be an integer",
                            field=param_name,
                            value=str(param_value),
                        )

                # Update in guacamole_connection table - param_name validated against whitelist
                query = f"""
                    UPDATE guacamole_connection
                    SET {param_name} = %s
                    WHERE connection_id = %s
                """
                self.cursor.execute(query, (param_value, resolved_connection_id))

            elif param_table == "parameter":
                # Special handling for read-only parameter
                if param_name == "read-only":
                    if param_value.lower() not in ("true", "false"):
                        raise ValidationError(
                            "Parameter read-only must be 'true' or 'false'",
                            field=param_name,
                            value=str(param_value),
                        )

                    if param_value.lower() == "true":
                        self.cursor.execute(
                            """
                            SELECT parameter_value FROM guacamole_connection_parameter
                            WHERE connection_id = %s AND parameter_name = %s
                        """,
                            (resolved_connection_id, param_name),
                        )

                        if self.cursor.fetchone():
                            self.cursor.execute(
                                """
                                UPDATE guacamole_connection_parameter
                                SET parameter_value = 'true'
                                WHERE connection_id = %s AND parameter_name = %s
                            """,
                                (resolved_connection_id, param_name),
                            )
                        else:
                            self.cursor.execute(
                                """
                                INSERT INTO guacamole_connection_parameter
                                (connection_id, parameter_name, parameter_value)
                                VALUES (%s, %s, 'true')
                            """,
                                (resolved_connection_id, param_name),
                            )
                    else:
                        self.cursor.execute(
                            """
                            DELETE FROM guacamole_connection_parameter
                            WHERE connection_id = %s AND parameter_name = %s
                        """,
                            (resolved_connection_id, param_name),
                        )
                else:
                    # Special handling for color-depth
                    if param_name == "color-depth":
                        if param_value not in ("8", "16", "24", "32"):
                            raise ValidationError(
                                "color-depth must be one of: 8, 16, 24, 32",
                                field=param_name,
                                value=str(param_value),
                            )

                    # Regular parameter handling
                    self.cursor.execute(
                        """
                        SELECT parameter_value FROM guacamole_connection_parameter
                        WHERE connection_id = %s AND parameter_name = %s
                    """,
                        (resolved_connection_id, param_name),
                    )

                    if self.cursor.fetchone():
                        self.cursor.execute(
                            """
                            UPDATE guacamole_connection_parameter
                            SET parameter_value = %s
                            WHERE connection_id = %s AND parameter_name = %s
                        """,
                            (param_value, resolved_connection_id, param_name),
                        )
                    else:
                        self.cursor.execute(
                            """
                            INSERT INTO guacamole_connection_parameter
                            (connection_id, parameter_name, parameter_value)
                            VALUES (%s, %s, %s)
                        """,
                            (resolved_connection_id, param_name, param_value),
                        )

            if self.cursor.rowcount == 0:
                raise ValidationError(
                    f"Failed to update connection parameter: {param_name}",
                    field=param_name,
                )

            return True

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error modifying connection parameter: {e}") from e

    def modify_connection_parent_group(
        self, connection_name=None, connection_id=None, group_name=None
    ):
        """Set parent connection group for a connection.

        Args:
            connection_name: Connection name (optional)
            connection_id: Connection ID (optional)
            group_name: Parent group name (optional, None for root)

        Returns:
            bool: True if successful
        """
        try:
            from .connection_group import ConnectionGroupRepository

            resolved_connection_id = self.resolve_connection_id(
                connection_name, connection_id
            )

            # Get group ID
            group_id = None
            if group_name:
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
                group_id = result[0]

            # Get current parent
            self.cursor.execute(
                """
                SELECT parent_id
                FROM guacamole_connection
                WHERE connection_id = %s
            """,
                (resolved_connection_id,),
            )
            result = self.cursor.fetchone()
            if not result:
                raise EntityNotFoundError("connection", str(resolved_connection_id))
            current_parent_id = result[0]

            # Get connection name for error messages if we only have ID
            if connection_name is None:
                connection_name = self.get_connection_name_by_id(resolved_connection_id)

            # Check if we're trying to set to same group
            if group_id == current_parent_id:
                if group_id is None:
                    raise ValidationError(
                        f"Connection '{connection_name}' already has no parent group"
                    )
                else:
                    raise ValidationError(
                        f"Connection '{connection_name}' is already in group '{group_name}'"
                    )

            # Update parent ID
            self.cursor.execute(
                """
                UPDATE guacamole_connection
                SET parent_id = %s
                WHERE connection_id = %s
            """,
                (group_id, resolved_connection_id),
            )

            if self.cursor.rowcount == 0:
                raise ValidationError(
                    f"Failed to update parent group for connection '{connection_name}'"
                )

            return True

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error modifying connection parent group: {e}") from e

    def get_connection_user_permissions(self, connection_name):
        """Get list of users with direct permissions to a connection.

        Args:
            connection_name: Connection name

        Returns:
            list: List of usernames
        """
        try:
            self.cursor.execute(
                """
                SELECT e.name
                FROM guacamole_connection c
                JOIN guacamole_connection_permission cp ON c.connection_id = cp.connection_id
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE c.connection_name = %s AND e.type = 'USER'
            """,
                (connection_name,),
            )
            return [row[0] for row in self.cursor.fetchall()]
        except mysql.connector.Error as e:
            raise DatabaseError(
                f"Error getting connection user permissions: {e}"
            ) from e

    def grant_connection_permission(
        self, entity_name, entity_type, connection_id, group_path=None
    ):
        """Grant connection permission to an entity.

        Args:
            entity_name: Entity name (user or group)
            entity_type: Entity type ('USER' or 'USER_GROUP')
            connection_id: Connection ID
            group_path: Group path for parent assignment (optional)
        """
        try:
            if group_path:
                self.debug_print(f"Processing group path: {group_path}")
                # Need to resolve group path
                from .connection_group import ConnectionGroupRepository

                # Simple resolution for single-level group
                self.cursor.execute(
                    """
                    SELECT connection_group_id
                    FROM guacamole_connection_group
                    WHERE connection_group_name = %s
                    LIMIT 1
                """,
                    (group_path.split("/")[-1],),
                )
                result = self.cursor.fetchone()
                if result:
                    parent_group_id = result[0]
                    self.debug_print(
                        f"Assigning connection {connection_id} to parent group {parent_group_id}"
                    )
                    self.cursor.execute(
                        """
                        UPDATE guacamole_connection
                        SET parent_id = %s
                        WHERE connection_id = %s
                    """,
                        (parent_group_id, connection_id),
                    )

            self.debug_print(f"Granting permission to {entity_type}:{entity_name}")
            self.cursor.execute(
                """
                INSERT INTO guacamole_connection_permission (entity_id, connection_id, permission)
                SELECT entity.entity_id, %s, 'READ'
                FROM guacamole_entity entity
                WHERE entity.name = %s AND entity.type = %s
            """,
                (connection_id, entity_name, entity_type),
            )

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error granting connection permission: {e}") from e

    def grant_connection_permission_to_user(self, username, connection_name):
        """Grant connection permission to a specific user.

        Args:
            username: Username
            connection_name: Connection name

        Returns:
            bool: True if successful
        """
        try:
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
                raise EntityNotFoundError("connection", connection_name)
            connection_id = result[0]

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
            """,
                (username,),
            )
            result = self.cursor.fetchone()
            if not result:
                raise EntityNotFoundError("user", username)
            entity_id = result[0]

            # Check if permission already exists
            self.cursor.execute(
                """
                SELECT 1 FROM guacamole_connection_permission
                WHERE entity_id = %s AND connection_id = %s
            """,
                (entity_id, connection_id),
            )
            if self.cursor.fetchone():
                raise PermissionError(
                    f"User '{username}' already has permission for connection '{connection_name}'",
                    username=username,
                    resource_type="connection",
                    resource_name=connection_name,
                )

            # Grant permission
            self.cursor.execute(
                """
                INSERT INTO guacamole_connection_permission
                (entity_id, connection_id, permission)
                VALUES (%s, %s, 'READ')
            """,
                (entity_id, connection_id),
            )

            return True

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error granting connection permission: {e}") from e

    def revoke_connection_permission_from_user(self, username, connection_name):
        """Revoke connection permission from a specific user.

        Args:
            username: Username
            connection_name: Connection name

        Returns:
            bool: True if successful
        """
        try:
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
                raise EntityNotFoundError("connection", connection_name)
            connection_id = result[0]

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
            """,
                (username,),
            )
            result = self.cursor.fetchone()
            if not result:
                raise EntityNotFoundError("user", username)
            entity_id = result[0]

            # Check if permission exists
            self.cursor.execute(
                """
                SELECT 1 FROM guacamole_connection_permission
                WHERE entity_id = %s AND connection_id = %s
            """,
                (entity_id, connection_id),
            )
            if not self.cursor.fetchone():
                raise PermissionError(
                    f"User '{username}' has no permission for connection '{connection_name}'",
                    username=username,
                    resource_type="connection",
                    resource_name=connection_name,
                )

            # Revoke permission
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection_permission
                WHERE entity_id = %s AND connection_id = %s
            """,
                (entity_id, connection_id),
            )

            return True

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error revoking connection permission: {e}") from e

    def list_connections_with_conngroups_and_parents(self):
        """List all connections with their groups, parent group, and user permissions.

        Returns:
            list: List of connection info tuples
        """
        try:
            self.cursor.execute(
                """
                SELECT
                    c.connection_id,
                    c.connection_name,
                    c.protocol,
                    MAX(CASE WHEN p1.parameter_name = 'hostname' THEN p1.parameter_value END) AS hostname,
                    MAX(CASE WHEN p2.parameter_name = 'port' THEN p2.parameter_value END) AS port,
                    GROUP_CONCAT(DISTINCT CASE WHEN e.type = 'USER_GROUP' THEN e.name END) AS groups,
                    cg.connection_group_name AS parent
                FROM guacamole_connection c
                LEFT JOIN guacamole_connection_parameter p1
                    ON c.connection_id = p1.connection_id AND p1.parameter_name = 'hostname'
                LEFT JOIN guacamole_connection_parameter p2
                    ON c.connection_id = p2.connection_id AND p2.parameter_name = 'port'
                LEFT JOIN guacamole_connection_permission cp
                    ON c.connection_id = cp.connection_id
                LEFT JOIN guacamole_entity e
                    ON cp.entity_id = e.entity_id AND e.type = 'USER_GROUP'
                LEFT JOIN guacamole_connection_group cg
                    ON c.parent_id = cg.connection_group_id
                GROUP BY c.connection_id
                ORDER BY c.connection_name
            """
            )

            connections_info = self.cursor.fetchall()

            result = []
            for conn_info in connections_info:
                conn_id, name, protocol, host, port, groups, parent = conn_info

                # Get user permissions for this connection
                self.cursor.execute(
                    """
                    SELECT e.name
                    FROM guacamole_connection_permission cp
                    JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                    WHERE cp.connection_id = %s AND e.type = 'USER'
                """,
                    (conn_id,),
                )

                user_permissions = [row[0] for row in self.cursor.fetchall()]

                result.append(
                    (
                        conn_id,
                        name,
                        protocol,
                        host,
                        port,
                        groups,
                        parent,
                        user_permissions,
                    )
                )

            return result

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error listing connections: {e}") from e

    def get_connection_by_id(self, connection_id):
        """Get a specific connection by its ID.

        Args:
            connection_id: Connection ID

        Returns:
            tuple: Connection info tuple or None if not found
        """
        try:
            self.cursor.execute(
                """
                SELECT
                    c.connection_id,
                    c.connection_name,
                    c.protocol,
                    MAX(CASE WHEN p1.parameter_name = 'hostname' THEN p1.parameter_value END) AS hostname,
                    MAX(CASE WHEN p2.parameter_name = 'port' THEN p2.parameter_value END) AS port,
                    GROUP_CONCAT(DISTINCT CASE WHEN e.type = 'USER_GROUP' THEN e.name END) AS groups,
                    cg.connection_group_name AS parent
                FROM guacamole_connection c
                LEFT JOIN guacamole_connection_parameter p1
                    ON c.connection_id = p1.connection_id AND p1.parameter_name = 'hostname'
                LEFT JOIN guacamole_connection_parameter p2
                    ON c.connection_id = p2.connection_id AND p2.parameter_name = 'port'
                LEFT JOIN guacamole_connection_permission cp
                    ON c.connection_id = cp.connection_id
                LEFT JOIN guacamole_entity e
                    ON cp.entity_id = e.entity_id AND e.type = 'USER_GROUP'
                LEFT JOIN guacamole_connection_group cg
                    ON c.parent_id = cg.connection_group_id
                WHERE c.connection_id = %s
                GROUP BY c.connection_id
            """,
                (connection_id,),
            )

            connection_info = self.cursor.fetchone()
            if not connection_info:
                return None

            conn_id, name, protocol, host, port, groups, parent = connection_info

            # Get user permissions for this connection
            self.cursor.execute(
                """
                SELECT e.name
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s AND e.type = 'USER'
            """,
                (conn_id,),
            )

            user_permissions = [row[0] for row in self.cursor.fetchall()]

            return (
                conn_id,
                name,
                protocol,
                host,
                port,
                groups,
                parent,
                user_permissions,
            )

        except mysql.connector.Error as e:
            raise DatabaseError(f"Error getting connection by ID: {e}") from e
