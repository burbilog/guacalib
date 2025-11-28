"""
Cross-domain reporting repository for Guacamole database operations.

This module contains functions for cross-domain reporting and complex
queries that span multiple tables or domains. These functions have
been extracted from the GuacamoleDB facade to improve maintainability
and follow the repository pattern.

All functions in this module accept a database cursor as the first
parameter and are stateless - they don't depend on GuacamoleDB instance
variables, making them easy to test and reuse.
"""

from typing import Dict, List, Optional
import logging
import mysql.connector


logger = logging.getLogger(__name__)


def debug_connection_permissions(cursor, connection_name: str) -> None:
    """Debug function to check and display permissions for a connection.

    Outputs detailed debugging information about all permissions associated
    with a specific connection, including both user and user group permissions.
    This function is intended for troubleshooting connection access issues.

    Args:
        cursor: Database cursor for executing queries.
        connection_name: The name of the connection to debug.

    Returns:
        None (outputs debug information to logger).

    Raises:
        mysql.connector.Error: If database query fails.
        ValueError: If connection is not found.

    Example:
        >>> cursor = db.cursor()
        >>> debug_connection_permissions(cursor, "my-server")
        # Outputs debug information via logger
    """
    try:
        logger.debug(f"Checking permissions for connection '{connection_name}'")

        # Get connection ID
        cursor.execute(
            """
            SELECT connection_id FROM guacamole_connection
            WHERE connection_name = %s
        """,
            (connection_name,),
        )
        result = cursor.fetchone()
        if not result:
            logger.debug(f"Connection '{connection_name}' not found")
            raise ValueError(f"Connection '{connection_name}' not found")
        connection_id = result[0]
        logger.debug(f"Connection ID: {connection_id}")

        # Check all permissions
        cursor.execute(
            """
            SELECT cp.entity_id, e.name, e.type, cp.permission
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s
        """,
            (connection_id,),
        )

        permissions = cursor.fetchall()
        if not permissions:
            logger.debug(
                f"No permissions found for connection '{connection_name}'"
            )
        else:
            logger.debug(f"Found {len(permissions)} permissions:")
            for perm in permissions:
                entity_id, name, entity_type, permission = perm
                logger.debug(
                    f"  Entity ID: {entity_id}, Name: {name}, Type: {entity_type}, Permission: {permission}"
                )

        # Specifically check user permissions
        cursor.execute(
            """
            SELECT e.name
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s AND e.type = 'USER'
        """,
            (connection_id,),
        )

        user_permissions = cursor.fetchall()
        if not user_permissions:
            logger.debug(
                f"No user permissions found for connection '{connection_name}'"
            )
        else:
            logger.debug(f"Found {len(user_permissions)} user permissions:")
            for perm in user_permissions:
                logger.debug(f"  User: {perm[0]}")

        logger.debug("End of debug info")

    except mysql.connector.Error as e:
        logger.debug(f"Error debugging permissions: {e}")
        raise


def list_groups_with_users(cursor) -> Dict[str, List[str]]:
    """List all user groups with their associated users.

    Retrieves a mapping of user group names to the list of usernames
    that belong to each group. This provides a simplified view of
    user group membership.

    Args:
        cursor: Database cursor for executing queries.

    Returns:
        Dictionary mapping group names to lists of usernames.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> groups = list_groups_with_users(cursor)
        >>> print(groups)
        {'admin-group': ['admin', 'manager'], 'users': ['john', 'jane']}
    """
    try:
        cursor.execute(
            """
            SELECT
                ug.name as group_name,
                u.username
            FROM guacamole_user_group ug
            LEFT JOIN guacamole_user_group_member ugm ON ug.user_group_id = ugm.user_group_id
            LEFT JOIN guacamole_user u ON ugm.user_id = u.user_id
            ORDER BY ug.name, u.username
        """
        )

        results = cursor.fetchall()
        groups_dict = {}

        for group_name, username in results:
            if group_name not in groups_dict:
                groups_dict[group_name] = []
            if username:  # Only add non-null usernames
                groups_dict[group_name].append(username)

        return groups_dict

    except mysql.connector.Error as e:
        raise ValueError(f"Error listing groups with users: {e}")