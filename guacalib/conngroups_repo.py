"""
Connection Groups Repository Module

This module contains SQL repository functions for connection group management operations.
It provides stateless functions that accept a database cursor and parameters,
returning data without any GuacamoleDB class dependencies.

Functions:
    connection_group_exists: Check if a connection group exists in the database
    create_connection_group: Create a new connection group with optional parent
    delete_connection_group: Delete a connection group and update child references
    check_connection_group_cycle: Check for circular references in hierarchy

All functions are designed to be stateless and accept a cursor as the first parameter.
"""

from typing import Optional
import mysql.connector
from . import db_utils


def connection_group_exists(
    cursor, group_name: Optional[str] = None, group_id: Optional[int] = None
) -> bool:
    """Check if a connection group exists in the Guacamole database.

    Args:
        cursor: Database cursor for executing queries
        group_name: The connection group name to check. Optional.
        group_id: The connection group ID to check. Optional.

    Returns:
        True if the connection group exists, False otherwise.

    Raises:
        ValueError: If neither or both parameters are provided.
        mysql.connector.Error: If database query fails.

    Note:
        Exactly one of group_name or group_id must be provided.

    Example:
        >>> cursor = db.cursor()
        >>> if connection_group_exists(cursor, group_name='servers'):
        ...     print("Connection group exists")
    """
    if not group_name and not group_id:
        raise ValueError("Either group_name or group_id must be provided")
    if group_name and group_id:
        raise ValueError("Provide either group_name or group_id, not both")

    try:
        if group_name:
            cursor.execute(
                """
                SELECT COUNT(*) FROM guacamole_connection_group
                WHERE connection_group_name = %s
            """,
                (group_name,),
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) FROM guacamole_connection_group
                WHERE connection_group_id = %s
            """,
                (group_id,),
            )
        return cursor.fetchone()[0] > 0
    except mysql.connector.Error as e:
        raise


def create_connection_group(
    cursor, group_name: str, parent_group_name: Optional[str] = None
) -> bool:
    """Create a new connection group in the Guacamole database.

    Creates a new connection group with the specified name and optionally
    assigns it to a parent group to establish a hierarchical structure.

    Args:
        cursor: Database cursor for executing queries
        group_name: Name for the new connection group.
        parent_group_name: Optional name of the parent connection group.
                          If None, the group will be created at the root level.

    Returns:
        True if the connection group was created successfully.

    Raises:
        ValueError: If group name is invalid, parent group doesn't exist,
                   or would create a cycle in the hierarchy.
        mysql.connector.Error: If database operation fails.

    Example:
        >>> cursor = db.cursor()
        >>> # Create root-level group
        >>> create_connection_group(cursor, "Production Servers")
        >>> # Create child group
        >>> create_connection_group(cursor, "Web Servers", "Production Servers")
    """
    parent_group_id = None
    if parent_group_name:
        # Get parent group ID if specified
        cursor.execute(
            """
            SELECT connection_group_id
            FROM guacamole_connection_group
            WHERE connection_group_name = %s
        """,
            (parent_group_name,),
        )
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Parent connection group '{parent_group_name}' not found")
        parent_group_id = result[0]

        # Check for cycles - since this is a new group, we can't be creating a cycle
        # but we should still validate the parent exists and is valid
        if check_connection_group_cycle(cursor, None, parent_group_id):
            raise ValueError(
                f"Parent connection group '{parent_group_name}' is invalid"
            )

    # Create the new connection group
    cursor.execute(
        """
        INSERT INTO guacamole_connection_group
        (connection_group_name, parent_id)
        VALUES (%s, %s)
    """,
        (group_name, parent_group_id),
    )

    # Verify the group was created
    cursor.execute(
        """
        SELECT connection_group_id
        FROM guacamole_connection_group
        WHERE connection_group_name = %s
    """,
        (group_name,),
    )
    if not cursor.fetchone():
        raise ValueError("Failed to create connection group - no ID returned")

    return True


def delete_connection_group(
    cursor, group_name: Optional[str] = None, group_id: Optional[int] = None
) -> bool:
    """Delete a connection group and update references to it.

    Removes a connection group while maintaining database integrity by updating
    child groups and connections to have NULL parent references instead of
    deleting them entirely.

    Args:
        cursor: Database cursor for executing queries
        group_name: The connection group name to delete. Optional.
        group_id: The connection group ID to delete. Optional.

    Returns:
        True if the connection group was deleted successfully.

    Raises:
        ValueError: If the connection group doesn't exist or neither/both parameters provided.
        mysql.connector.Error: If database operations fail.

    Note:
        This operation updates child groups and connections to have NULL parent
        references rather than deleting them. Exactly one of group_name or group_id
        must be provided.

    Example:
        >>> cursor = db.cursor()
        >>> delete_connection_group(cursor, group_name='old-group')
    """
    if not group_name and not group_id:
        raise ValueError("Either group_name or group_id must be provided")
    if group_name and group_id:
        raise ValueError("Provide either group_name or group_id, not both")

    # Resolve group_id if only name is provided
    if group_name:
        if not connection_group_exists(cursor, group_name=group_name):
            raise ValueError(f"Connection group '{group_name}' not found")
        cursor.execute(
            """
            SELECT connection_group_id FROM guacamole_connection_group
            WHERE connection_group_name = %s
        """,
            (group_name,),
        )
        resolved_group_id = cursor.fetchone()[0]
    else:
        # For ID-based deletion, verify connection group exists
        if not connection_group_exists(cursor, group_id=group_id):
            raise ValueError(f"Connection group with ID {group_id} not found")
        resolved_group_id = group_id

    # Update any child groups to have NULL parent
    cursor.execute(
        """
        UPDATE guacamole_connection_group
        SET parent_id = NULL
        WHERE parent_id = %s
    """,
        (resolved_group_id,),
    )

    # Update any connections to have NULL parent
    cursor.execute(
        """
        UPDATE guacamole_connection
        SET parent_id = NULL
        WHERE parent_id = %s
    """,
        (resolved_group_id,),
    )

    # Delete the group
    cursor.execute(
        """
        DELETE FROM guacamole_connection_group
        WHERE connection_group_id = %s
    """,
        (resolved_group_id,),
    )

    return True


def check_connection_group_cycle(
    cursor, group_id: int, parent_id: Optional[int]
) -> bool:
    """Check if setting a parent connection group would create a cycle.

    Validates whether assigning a parent group to a connection group would
    result in a circular reference in the connection group hierarchy.
    This prevents infinite loops and maintains a proper tree structure.

    Args:
        cursor: Database cursor for executing queries
        group_id: The database ID of the connection group to be modified.
        parent_id: The database ID of the proposed parent group, or None
                  to remove the parent relationship.

    Returns:
        True if setting the parent would create a cycle, False otherwise.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> # Group 1 -> Group 2 -> Group 3 (hierarchy)
        >>> # Attempting to make Group 3 parent of Group 1 would create a cycle
        >>> check_connection_group_cycle(cursor, 1, 3)  # Returns True
        >>> check_connection_group_cycle(cursor, 4, None)  # Returns False
    """
    if parent_id is None:
        return False

    current_parent = parent_id
    while current_parent is not None:
        if current_parent == group_id:
            return True

        # Get next parent
        cursor.execute(
            """
            SELECT parent_id
            FROM guacamole_connection_group
            WHERE connection_group_id = %s
        """,
            (current_parent,),
        )
        result = cursor.fetchone()
        current_parent = result[0] if result else None

    return False


def modify_connection_group_parent(
    cursor,
    group_name: Optional[str] = None,
    group_id: Optional[int] = None,
    new_parent_name: Optional[str] = None,
) -> bool:
    """Set parent connection group for a connection group with cycle detection.

    Args:
        cursor: Database cursor for executing queries.
        group_name: The name of the connection group to modify. Optional.
        group_id: The ID of the connection group to modify. Optional.
        new_parent_name: The name of the new parent group. Optional (None for root level).

    Returns:
        True if successful.

    Raises:
        ValueError: If group doesn't exist, parent group doesn't exist,
                   or setting parent would create a cycle.
        mysql.connector.Error: If database operation fails.

    Note:
        Exactly one of group_name or group_id must be provided.

    Example:
        >>> cursor = db.cursor()
        >>> modify_connection_group_parent(cursor, group_name="Production", new_parent_name="Infrastructure")
        >>> modify_connection_group_parent(cursor, group_id=42, new_parent_name=None)
    """
    # Validate exactly one group identifier provided
    if (group_name is None) == (group_id is None):
        raise ValueError("Exactly one of group_name or group_id must be provided")

    try:
        # Resolve group ID and validate group exists
        if group_id is not None:
            # Validate group ID exists
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
            resolved_group_id = group_id
        else:
            # Resolve group by name
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
            resolved_group_id = result[0]

        # Get group name for error messages if we only have ID
        if group_name is None:
            cursor.execute(
                """
                SELECT connection_group_name FROM guacamole_connection_group
                WHERE connection_group_id = %s
            """,
                (resolved_group_id,),
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(
                    f"Connection group with ID {resolved_group_id} not found"
                )
            group_name = result[0]

        # Handle NULL parent (empty string or None)
        new_parent_id = None
        if new_parent_name:
            # Get new parent ID
            cursor.execute(
                """
                SELECT connection_group_id
                FROM guacamole_connection_group
                WHERE connection_group_name = %s
            """,
                (new_parent_name,),
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(
                    f"Parent connection group '{new_parent_name}' not found"
                )
            new_parent_id = result[0]

            # Check for cycles using cycle detection helper
            if check_connection_group_cycle(cursor, resolved_group_id, new_parent_id):
                raise ValueError(
                    "Setting parent would create a cycle in connection groups"
                )

        # Update the parent
        cursor.execute(
            """
            UPDATE guacamole_connection_group
            SET parent_id = %s
            WHERE connection_group_id = %s
        """,
            (new_parent_id, resolved_group_id),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"Failed to update parent group for '{group_name}'")

        return True

    except mysql.connector.Error as e:
        raise ValueError(f"Database error modifying connection group parent: {e}")
