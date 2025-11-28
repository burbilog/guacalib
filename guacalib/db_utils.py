"""
Shared database utilities for ID resolution and validation.

This module contains utility functions that are used across multiple
domains in the GuacamoleDB class. These functions have been extracted
to reduce code duplication and improve maintainability.

All functions in this module accept a database cursor as the first
parameter and are stateless - they don't depend on GuacamoleDB instance
variables, making them easy to test and reuse.
"""

from typing import Optional, Dict, List
import mysql.connector


def validate_positive_id(id_value: Optional[int], entity_type: str = "entity") -> Optional[int]:
    """Validate that ID is a positive integer.

    Args:
        id_value: The ID value to validate.
        entity_type: The type of entity (used in error messages).

    Returns:
        The validated ID value.

    Raises:
        ValueError: If ID is not a positive integer.
    """
    if id_value is not None and id_value <= 0:
        raise ValueError(
            f"{entity_type} ID must be a positive integer greater than 0"
        )
    return id_value


def get_connection_name_by_id(cursor, connection_id: int) -> Optional[str]:
    """Get connection name by ID.

    Args:
        cursor: Database cursor for executing queries.
        connection_id: The connection ID.

    Returns:
        The connection name, or None if not found.

    Raises:
        mysql.connector.Error: If database query fails.
    """
    cursor.execute(
        """
        SELECT connection_name
        FROM guacamole_connection
        WHERE connection_id = %s
    """,
        (connection_id,),
    )
    result = cursor.fetchone()
    return result[0] if result else None


def get_connection_group_name_by_id(cursor, group_id: int) -> Optional[str]:
    """Get connection group name by ID.

    Args:
        cursor: Database cursor for executing queries.
        group_id: The connection group ID.

    Returns:
        The connection group name, or None if not found.

    Raises:
        mysql.connector.Error: If database query fails.
    """
    cursor.execute(
        """
        SELECT connection_group_name
        FROM guacamole_connection_group
        WHERE connection_group_id = %s
    """,
        (group_id,),
    )
    result = cursor.fetchone()
    return result[0] if result else None


def get_usergroup_name_by_id(cursor, group_id: int) -> str:
    """Get user group name by its database ID.

    Retrieves the name of a user group given its database ID.
    This is useful for converting internal IDs back to human-readable names.

    Args:
        cursor: Database cursor for executing queries.
        group_id: The database ID of the user group.

    Returns:
        The name of the user group.

    Raises:
        ValueError: If user group with the specified ID is not found.
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> name = get_usergroup_name_by_id(cursor, 42)
        >>> print(f"Group name: {name}")
        Group name: admin-group
    """
    cursor.execute(
        """
        SELECT e.name FROM guacamole_entity e
        JOIN guacamole_user_group g ON e.entity_id = g.entity_id
        WHERE g.user_group_id = %s
    """,
        (group_id,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Usergroup with ID {group_id} not found")
    return result[0]


def resolve_connection_id(cursor, connection_name: Optional[str] = None, connection_id: Optional[int] = None) -> int:
    """Validate inputs and resolve to connection_id with centralized validation.

    This is a core utility method that handles the common pattern of accepting
    either a connection name or ID and resolving it to a validated connection ID.
    Provides comprehensive input validation and error handling.

    Args:
        cursor: Database cursor for executing queries.
        connection_name: The connection name to resolve. Optional.
        connection_id: The connection ID to validate. Optional.

    Returns:
        The validated connection ID.

    Raises:
        ValueError: If neither or both parameters are provided, if ID is invalid,
                   if connection doesn't exist, or if database error occurs.

    Note:
        Exactly one of connection_name or connection_id must be provided.
        This method is used by many other methods for consistent ID resolution.

    Example:
        >>> cursor = db.cursor()
        >>> # Resolve by name
        >>> conn_id = resolve_connection_id(cursor, connection_name='my-server')
        >>> # Resolve by ID (validates existence)
        >>> conn_id = resolve_connection_id(cursor, connection_id=123)
    """
    # Validate exactly one parameter provided
    if (connection_name is None) == (connection_id is None):
        raise ValueError(
            "Exactly one of connection_name or connection_id must be provided"
        )

    # If ID provided, validate and return it
    if connection_id is not None:
        if connection_id <= 0:
            raise ValueError(
                "Connection ID must be a positive integer greater than 0"
            )

        # Verify the connection exists
        try:
            cursor.execute(
                """
                SELECT connection_id FROM guacamole_connection
                WHERE connection_id = %s
            """,
                (connection_id,),
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Connection with ID {connection_id} not found")
            return connection_id
        except mysql.connector.Error as e:
            raise ValueError(f"Database error while resolving connection ID: {e}")

    # If name provided, resolve to ID
    if connection_name is not None:
        try:
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
            return result[0]
        except mysql.connector.Error as e:
            raise ValueError(f"Database error while resolving connection name: {e}")


def resolve_conngroup_id(cursor, group_name: Optional[str] = None, group_id: Optional[int] = None) -> int:
    """Validate inputs and resolve to connection_group_id with centralized validation.

    Args:
        cursor: Database cursor for executing queries.
        group_name: The connection group name to resolve. Optional.
        group_id: The connection group ID to validate. Optional.

    Returns:
        The validated connection group ID.

    Raises:
        ValueError: If neither or both parameters are provided, if ID is invalid,
                   if group doesn't exist, or if database error occurs.
    """
    # Validate exactly one parameter provided
    if (group_name is None) == (group_id is None):
        raise ValueError("Exactly one of group_name or group_id must be provided")

    # If ID provided, validate and return it
    if group_id is not None:
        if group_id <= 0:
            raise ValueError(
                "Connection group ID must be a positive integer greater than 0"
            )

        # Verify the connection group exists
        try:
            cursor.execute(
                """
                SELECT connection_group_id FROM guacamole_connection_group
                WHERE connection_group_id = %s
            """,
                (group_id,),
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Connection group with ID {group_id} not found")
            return group_id
        except mysql.connector.Error as e:
            raise ValueError(
                f"Database error while resolving connection group ID: {e}"
            )

    # If name provided, resolve to ID
    if group_name is not None:
        try:
            cursor.execute(
                """
                SELECT connection_group_id FROM guacamole_connection_group
                WHERE connection_group_name = %s
            """,
                (group_name,),
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Connection group '{group_name}' not found")
            return result[0]
        except mysql.connector.Error as e:
            raise ValueError(
                f"Database error while resolving connection group name: {e}"
            )


def resolve_usergroup_id(cursor, group_name: Optional[str] = None, group_id: Optional[int] = None) -> int:
    """Validate inputs and resolve to user_group_id with centralized validation.

    Args:
        cursor: Database cursor for executing queries.
        group_name: The user group name to resolve. Optional.
        group_id: The user group ID to validate. Optional.

    Returns:
        The validated user group ID.

    Raises:
        ValueError: If neither or both parameters are provided, if ID is invalid,
                   if group doesn't exist, or if database error occurs.
    """
    # Validate exactly one parameter provided
    if (group_name is None) == (group_id is None):
        raise ValueError("Exactly one of group_name or group_id must be provided")

    # If ID provided, validate and return it
    if group_id is not None:
        if group_id <= 0:
            raise ValueError(
                "Usergroup ID must be a positive integer greater than 0"
            )

        # Verify the usergroup exists
        try:
            cursor.execute(
                """
                SELECT user_group_id FROM guacamole_user_group
                WHERE user_group_id = %s
            """,
                (group_id,),
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Usergroup with ID {group_id} not found")
            return group_id
        except mysql.connector.Error as e:
            raise ValueError(f"Database error while resolving usergroup ID: {e}")

    # If name provided, resolve to ID
    if group_name is not None:
        try:
            cursor.execute(
                """
                SELECT user_group_id FROM guacamole_user_group g
                JOIN guacamole_entity e ON g.entity_id = e.entity_id
                WHERE e.name = %s
            """,
                (group_name,),
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Usergroup '{group_name}' not found")
            return result[0]
        except mysql.connector.Error as e:
            raise ValueError(f"Database error while resolving usergroup name: {e}")


def resolve_connection_group_path(cursor, group_path: str) -> int:
    """Resolve nested connection group path to connection group ID.

    Resolves a hierarchical path (e.g., "parent/child/grandchild") to the
    database ID of the final group in the path. This method traverses the
    hierarchy to find the exact group at the specified path.

    Args:
        cursor: Database cursor for executing queries.
        group_path: Slash-separated path to the connection group.
                   Examples: "Production", "Production/Web", "Servers/Linux"

    Returns:
        The database ID of the connection group at the specified path.

    Raises:
        ValueError: If the group path cannot be resolved or any group in the
                   path doesn't exist, or if database error occurs.

    Example:
        >>> cursor = db.cursor()
        >>> group_id = resolve_connection_group_path(cursor, "Production/Web Servers")
        >>> print(f"Group ID: {group_id}")
        Group ID: 42
    """
    try:
        groups = group_path.split("/")
        parent_group_id = None

        for group_name in groups:
            # Use connection_group_name directly with parent hierarchy
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

            cursor.execute(sql, tuple(params))

            result = cursor.fetchone()
            if not result:
                raise ValueError(
                    f"Group '{group_name}' not found in path '{group_path}'"
                )

            parent_group_id = result[0]

        return parent_group_id

    except mysql.connector.Error as e:
        raise ValueError(f"Database error resolving group path: {e}")


def get_usergroup_id(cursor, group_name: str) -> int:
    """Get user group ID by name from the database.

    Args:
        cursor: Database cursor for executing queries
        group_name: Name of the user group to look up

    Returns:
        The database ID of the user group

    Raises:
        Exception: If the user group with the specified name is not found
        mysql.connector.Error: If database query fails
    """
    cursor.execute(
        """
        SELECT user_group_id
        FROM guacamole_user_group g
        JOIN guacamole_entity e ON g.entity_id = e.entity_id
        WHERE e.name = %s AND e.type = 'USER_GROUP'
    """,
        (group_name,),
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        raise Exception(f"Usergroup '{group_name}' not found")


def get_connection_group_id_by_name(cursor, group_name: str) -> Optional[int]:
    """Get connection group ID by name from the database.

    Args:
        cursor: Database cursor for executing queries
        group_name: Name of the connection group to look up

    Returns:
        The database ID of the connection group, or None if group_name is empty

    Raises:
        ValueError: If the connection group with the specified name is not found
        mysql.connector.Error: If database query fails
    """
    if not group_name:  # Handle empty group name as explicit NULL
        return None

    cursor.execute(
        """
        SELECT connection_group_id
        FROM guacamole_connection_group
        WHERE connection_group_name = %s
    """,
        (group_name,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Connection group '{group_name}' not found")
    return result[0]


def usergroup_exists_by_id(cursor, group_id: int) -> bool:
    """Check if a user group exists by ID.

    Args:
        cursor: Database cursor for executing queries
        group_id: The user group ID to check

    Returns:
        True if the user group exists, False otherwise

    Raises:
        mysql.connector.Error: If database query fails
    """
    cursor.execute(
        """
        SELECT user_group_id FROM guacamole_user_group
        WHERE user_group_id = %s
    """,
        (group_id,),
    )
    return cursor.fetchone() is not None