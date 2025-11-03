"""
Permissions Repository Module

This module contains SQL repository functions for permission management operations.
It provides stateless functions that accept a database cursor and parameters,
returning data without any GuacamoleDB class dependencies.

Functions:
    get_connection_user_permissions: Get users with direct permissions to a connection
    add_user_to_usergroup: Add a user to a user group with permissions
    remove_user_from_usergroup: Remove a user from a user group
    grant_connection_permission: Grant connection permission to an entity
    grant_connection_permission_to_user: Grant connection permission to a user
    revoke_connection_permission_from_user: Revoke connection permission from a user
    debug_connection_permissions: Debug permissions for a connection
    grant_connection_group_permission_to_user: Grant connection group permission to user
    revoke_connection_group_permission_from_user: Revoke connection group permission from user
    grant_connection_group_permission_to_user_by_id: Grant connection group permission by ID
    revoke_connection_group_permission_from_user_by_id: Revoke connection group permission by ID

All functions are designed to be stateless and accept a cursor as the first parameter.
"""

import mysql.connector
from typing import List


def get_connection_user_permissions(cursor, connection_name: str) -> List[str]:
    """Get list of users with direct permissions to a connection.

    Args:
        cursor: Database cursor for executing queries
        connection_name: The connection name to get permissions for.

    Returns:
        List of usernames with direct permissions to the connection.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> users = get_connection_user_permissions(cursor, 'my-server')
        >>> print(f"Users with access: {users}")
    """
    cursor.execute(
        """
        SELECT e.name
        FROM guacamole_connection c
        JOIN guacamole_connection_permission cp ON c.connection_id = cp.connection_id
        JOIN guacamole_entity e ON cp.entity_id = e.entity_id
        WHERE c.connection_name = %s AND e.type = 'USER'
    """,
        (connection_name,),
    )
    return [row[0] for row in cursor.fetchall()]


def add_user_to_usergroup(cursor, username: str, group_name: str) -> None:
    """Add a user to a user group with proper permissions.

    Creates membership relationship and grants appropriate group permissions
    to the user for accessing the user group resources.

    Args:
        cursor: Database cursor for executing queries
        username: The username to add to the group.
        group_name: The user group name to add the user to.

    Raises:
        ValueError: If user or group doesn't exist.
        mysql.connector.Error: If database operations fail.

    Example:
        >>> cursor = db.cursor()
        >>> add_user_to_usergroup(cursor, 'john.doe', 'developers')
    """
    # Get the group ID
    cursor.execute(
        """
        SELECT user_group_id
        FROM guacamole_user_group ug
        JOIN guacamole_entity e ON ug.entity_id = e.entity_id
        WHERE e.name = %s
    """,
        (group_name,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User group '{group_name}' not found")
    group_id = result[0]

    # Get the user's entity ID
    cursor.execute(
        """
        SELECT entity_id
        FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User '{username}' not found")
    user_entity_id = result[0]

    # Add user to group
    cursor.execute(
        """
        INSERT INTO guacamole_user_group_member
        (user_group_id, member_entity_id)
        VALUES (%s, %s)
    """,
        (group_id, user_entity_id),
    )

    # Grant group permissions to user
    cursor.execute(
        """
        INSERT INTO guacamole_user_group_permission
        (entity_id, affected_user_group_id, permission)
        SELECT %s, %s, 'READ'
        FROM dual
        WHERE NOT EXISTS (
            SELECT 1 FROM guacamole_user_group_permission
            WHERE entity_id = %s
            AND affected_user_group_id = %s
            AND permission = 'READ'
        )
    """,
        (user_entity_id, group_id, user_entity_id, group_id),
    )


def remove_user_from_usergroup(cursor, username: str, group_name: str) -> None:
    """Remove a user from a user group and revoke associated permissions.

    Removes membership relationship and revokes group permissions from the user.

    Args:
        cursor: Database cursor for executing queries
        username: The username to remove from the group.
        group_name: The user group name to remove the user from.

    Raises:
        ValueError: If user or group doesn't exist, or user not in group.
        mysql.connector.Error: If database operations fail.

    Example:
        >>> cursor = db.cursor()
        >>> remove_user_from_usergroup(cursor, 'john.doe', 'developers')
    """
    # Get the group ID
    cursor.execute(
        """
        SELECT user_group_id
        FROM guacamole_user_group ug
        JOIN guacamole_entity e ON ug.entity_id = e.entity_id
        WHERE e.name = %s
    """,
        (group_name,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User group '{group_name}' not found")
    group_id = result[0]

    # Get the user's entity ID
    cursor.execute(
        """
        SELECT entity_id
        FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User '{username}' not found")
    user_entity_id = result[0]

    # Check if user is actually in the group
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM guacamole_user_group_member
        WHERE user_group_id = %s AND member_entity_id = %s
    """,
        (group_id, user_entity_id),
    )
    if cursor.fetchone()[0] == 0:
        raise ValueError(f"User '{username}' is not in group '{group_name}'")

    # Remove user from group
    cursor.execute(
        """
        DELETE FROM guacamole_user_group_member
        WHERE user_group_id = %s AND member_entity_id = %s
    """,
        (group_id, user_entity_id),
    )

    # Revoke group permissions from user
    cursor.execute(
        """
        DELETE FROM guacamole_user_group_permission
        WHERE entity_id = %s AND affected_user_group_id = %s
    """,
        (user_entity_id, group_id),
    )


def grant_connection_permission(cursor, entity_name: str, entity_type: str, connection_id: int, group_path=None) -> None:
    """Grant connection permission to an entity.

    Grants READ permission to an entity (user or user group) for accessing
    a specific connection. Optionally assigns connection to a parent group.

    Args:
        cursor: Database cursor for executing queries
        entity_name: The name of the entity to grant permission to.
        entity_type: The type of entity ('USER' or 'USER_GROUP').
        connection_id: The connection ID to grant permission for.
        group_path: Optional path to assign connection to parent group.

    Raises:
        ValueError: If entity doesn't exist.
        mysql.connector.Error: If database operations fail.

    Example:
        >>> cursor = db.cursor()
        >>> grant_connection_permission(cursor, 'john.doe', 'USER', 42)
    """
    if group_path:
        # Get parent group ID
        cursor.execute(
            """
            SELECT connection_group_id FROM guacamole_connection_group
            WHERE connection_group_name = %s
        """,
            (group_path,),
        )
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Parent connection group '{group_path}' not found")
        parent_group_id = result[0]

        # Assign connection to parent group
        cursor.execute(
            """
            UPDATE guacamole_connection
            SET parent_id = %s
            WHERE connection_id = %s
        """,
            (parent_group_id, connection_id),
        )

    # Grant permission
    cursor.execute(
        """
        INSERT INTO guacamole_connection_permission (entity_id, connection_id, permission)
        SELECT entity.entity_id, %s, 'READ'
        FROM guacamole_entity entity
        WHERE entity.name = %s AND entity.type = %s
    """,
        (connection_id, entity_name, entity_type),
    )


def grant_connection_permission_to_user(cursor, username: str, connection_name: str) -> bool:
    """Grant connection permission to a specific user.

    Args:
        cursor: Database cursor for executing queries
        username: The username to grant permission to.
        connection_name: The connection name to grant access to.

    Returns:
        True if the permission was granted successfully.

    Raises:
        ValueError: If user or connection doesn't exist, or permission already exists.
        mysql.connector.Error: If database operation fails.

    Example:
        >>> cursor = db.cursor()
        >>> success = grant_connection_permission_to_user(cursor, "john.doe", "my-server")
        >>> print(f"Permission granted: {success}")
    """
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
        raise ValueError(f"Connection '{connection_name}' not found")
    connection_id = result[0]

    # Get user entity ID
    cursor.execute(
        """
        SELECT entity_id FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User '{username}' not found")
    entity_id = result[0]

    # Check if permission already exists
    cursor.execute(
        """
        SELECT 1 FROM guacamole_connection_permission
        WHERE entity_id = %s AND connection_id = %s
    """,
        (entity_id, connection_id),
    )
    if cursor.fetchone():
        raise ValueError(
            f"User '{username}' already has permission for connection '{connection_name}'"
        )

    # Grant permission
    cursor.execute(
        """
        INSERT INTO guacamole_connection_permission
        (entity_id, connection_id, permission)
        VALUES (%s, %s, 'READ')
    """,
        (entity_id, connection_id),
    )

    return True


def revoke_connection_permission_from_user(cursor, username: str, connection_name: str) -> bool:
    """Revoke connection permission from a specific user.

    Args:
        cursor: Database cursor for executing queries
        username: The username to revoke permission from.
        connection_name: The connection name to revoke access to.

    Returns:
        True if the permission was revoked successfully.

    Raises:
        ValueError: If user or connection doesn't exist, or permission doesn't exist.
        mysql.connector.Error: If database operation fails.

    Example:
        >>> cursor = db.cursor()
        >>> success = revoke_connection_permission_from_user(cursor, "john.doe", "my-server")
        >>> print(f"Permission revoked: {success}")
    """
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
        raise ValueError(f"Connection '{connection_name}' not found")
    connection_id = result[0]

    # Get user entity ID
    cursor.execute(
        """
        SELECT entity_id FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User '{username}' not found")
    entity_id = result[0]

    # Check if permission exists
    cursor.execute(
        """
        SELECT 1 FROM guacamole_connection_permission
        WHERE entity_id = %s AND connection_id = %s
    """,
        (entity_id, connection_id),
    )
    if not cursor.fetchone():
        raise ValueError(
            f"User '{username}' does not have permission for connection '{connection_name}'"
        )

    # Revoke permission
    cursor.execute(
        """
        DELETE FROM guacamole_connection_permission
        WHERE entity_id = %s AND connection_id = %s
    """,
        (entity_id, connection_id),
    )

    return True


def grant_connection_group_permission_to_user(cursor, username: str, conngroup_name: str) -> bool:
    """Grant connection group permission to a specific user.

    Grants READ permission to a user for accessing a connection group.
    This allows the user to see and use all connections within that group.

    Args:
        cursor: Database cursor for executing queries
        username: Name of the user to grant permission to.
        conngroup_name: Name of the connection group to grant access to.

    Returns:
        True if the permission was granted successfully.

    Raises:
        ValueError: If username or connection group name is invalid, or if
                   the user or connection group doesn't exist.
        mysql.connector.Error: If database operation fails.

    Example:
        >>> cursor = db.cursor()
        >>> success = grant_connection_group_permission_to_user(
        ...     cursor, "john.doe", "Production Servers"
        ... )
        >>> print(f"Permission granted: {success}")
    """
    # Get connection group ID
    cursor.execute(
        """
        SELECT connection_group_id, connection_group_name FROM guacamole_connection_group
        WHERE connection_group_name = %s
        LIMIT 1
    """,
        (conngroup_name,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Connection group '{conngroup_name}' not found")
    connection_group_id, actual_conngroup_name = result

    # Get user entity ID
    cursor.execute(
        """
        SELECT entity_id FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User '{username}' not found")
    entity_id = result[0]

    # Check if permission already exists
    cursor.execute(
        """
        SELECT 1 FROM guacamole_connection_group_permission
        WHERE entity_id = %s AND connection_group_id = %s
    """,
        (entity_id, connection_group_id),
    )
    if cursor.fetchone():
        raise ValueError(
            f"User '{username}' already has permission for connection group '{conngroup_name}'"
        )

    # Grant permission
    cursor.execute(
        """
        INSERT INTO guacamole_connection_group_permission
        (entity_id, connection_group_id, permission)
        VALUES (%s, %s, 'READ')
    """,
        (entity_id, connection_group_id),
    )

    return True


def revoke_connection_group_permission_from_user(cursor, username: str, conngroup_name: str) -> bool:
    """Revoke connection group permission from a specific user.

    Args:
        cursor: Database cursor for executing queries
        username: Name of the user to revoke permission from.
        conngroup_name: Name of the connection group to revoke access to.

    Returns:
        True if the permission was revoked successfully.

    Raises:
        ValueError: If username or connection group name is invalid, or if
                   the user, connection group, or permission doesn't exist.
        mysql.connector.Error: If database operation fails.

    Example:
        >>> cursor = db.cursor()
        >>> success = revoke_connection_group_permission_from_user(
        ...     cursor, "john.doe", "Production Servers"
        ... )
        >>> print(f"Permission revoked: {success}")
    """
    # Get connection group ID
    cursor.execute(
        """
        SELECT connection_group_id FROM guacamole_connection_group
        WHERE connection_group_name = %s
        LIMIT 1
    """,
        (conngroup_name,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Connection group '{conngroup_name}' not found")
    connection_group_id = result[0]

    # Get user entity ID
    cursor.execute(
        """
        SELECT entity_id FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User '{username}' not found")
    entity_id = result[0]

    # Check if permission exists
    cursor.execute(
        """
        SELECT 1 FROM guacamole_connection_group_permission
        WHERE entity_id = %s AND connection_group_id = %s
    """,
        (entity_id, connection_group_id),
    )
    if not cursor.fetchone():
        raise ValueError(
            f"Permission for user '{username}' on connection group '{conngroup_name}' does not exist"
        )

    # Revoke permission
    cursor.execute(
        """
        DELETE FROM guacamole_connection_group_permission
        WHERE entity_id = %s AND connection_group_id = %s
    """,
        (entity_id, connection_group_id),
    )

    return True


def grant_connection_group_permission_to_user_by_id(cursor, username: str, conngroup_id: int) -> bool:
    """Grant connection group permission to a user using connection group ID.

    Grants READ permission to a user for accessing a connection group specified by ID.
    This allows the user to see and use all connections within that group.

    Args:
        cursor: Database cursor for executing queries
        username: Name of the user to grant permission to.
        conngroup_id: Database ID of the connection group to grant access to.

    Returns:
        True if the permission was granted successfully.

    Raises:
        ValueError: If username is invalid, or if the user or connection
                   group doesn't exist, or permission already exists.
        mysql.connector.Error: If database operation fails.

    Example:
        >>> cursor = db.cursor()
        >>> success = grant_connection_group_permission_to_user_by_id(
        ...     cursor, "john.doe", 42
        ... )
        >>> print(f"Permission granted: {success}")
    """
    # Validate connection group ID
    cursor.execute(
        """
        SELECT connection_group_id, connection_group_name FROM guacamole_connection_group
        WHERE connection_group_id = %s
        LIMIT 1
    """,
        (conngroup_id,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Connection group with ID {conngroup_id} not found")
    actual_conngroup_id, actual_conngroup_name = result

    # Get user entity ID
    cursor.execute(
        """
        SELECT entity_id FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User '{username}' not found")
    entity_id = result[0]

    # Check if permission already exists
    cursor.execute(
        """
        SELECT 1 FROM guacamole_connection_group_permission
        WHERE entity_id = %s AND connection_group_id = %s
    """,
        (entity_id, actual_conngroup_id),
    )
    if cursor.fetchone():
        raise ValueError(
            f"User '{username}' already has permission for connection group '{actual_conngroup_name}' (ID: {conngroup_id})"
        )

    # Grant permission
    cursor.execute(
        """
        INSERT INTO guacamole_connection_group_permission
        (entity_id, connection_group_id, permission)
        VALUES (%s, %s, 'READ')
    """,
        (entity_id, actual_conngroup_id),
    )

    return True


def revoke_connection_group_permission_from_user_by_id(cursor, username: str, conngroup_id: int) -> bool:
    """Revoke connection group permission from a user using connection group ID.

    Args:
        cursor: Database cursor for executing queries
        username: Name of the user to revoke permission from.
        conngroup_id: Database ID of the connection group to revoke access to.

    Returns:
        True if the permission was revoked successfully.

    Raises:
        ValueError: If username is invalid, or if the user, connection
                   group, or permission doesn't exist.
        mysql.connector.Error: If database operation fails.

    Example:
        >>> cursor = db.cursor()
        >>> success = revoke_connection_group_permission_from_user_by_id(
        ...     cursor, "john.doe", 42
        ... )
        >>> print(f"Permission revoked: {success}")
    """
    # Validate connection group ID
    cursor.execute(
        """
        SELECT connection_group_id, connection_group_name FROM guacamole_connection_group
        WHERE connection_group_id = %s
        LIMIT 1
    """,
        (conngroup_id,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Connection group with ID {conngroup_id} not found")
    actual_conngroup_id, actual_conngroup_name = result

    # Get user entity ID
    cursor.execute(
        """
        SELECT entity_id FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"User '{username}' not found")
    entity_id = result[0]

    # Check if permission exists
    cursor.execute(
        """
        SELECT 1 FROM guacamole_connection_group_permission
        WHERE entity_id = %s AND connection_group_id = %s
    """,
        (entity_id, actual_conngroup_id),
    )
    if not cursor.fetchone():
        raise ValueError(
            f"Permission for user '{username}' on connection group '{actual_conngroup_name}' (ID: {conngroup_id}) does not exist"
        )

    # Revoke permission
    cursor.execute(
        """
        DELETE FROM guacamole_connection_group_permission
        WHERE entity_id = %s AND connection_group_id = %s
    """,
        (entity_id, actual_conngroup_id),
    )

    return True