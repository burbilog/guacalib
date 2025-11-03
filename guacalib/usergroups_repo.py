"""
User Groups Repository Module

This module contains SQL repository functions for user group management operations.
It provides stateless functions that accept a database cursor and parameters,
returning data without any GuacamoleDB class dependencies.

Functions:
    usergroup_exists: Check if a user group exists in the database
    create_usergroup: Create a new user group with default settings
    delete_usergroup: Delete a user group and all associated data
    list_usergroups: List all user groups in the database

All functions are designed to be stateless and accept a cursor as the first parameter.
"""

from typing import List
import mysql.connector


def usergroup_exists(cursor, group_name: str) -> bool:
    """Check if a user group exists in the Guacamole database.

    Queries the guacamole_entity table to determine if a user group with the
    specified name exists.

    Args:
        cursor: Database cursor for executing queries
        group_name: The user group name to check for existence.

    Returns:
        True if the user group exists, False otherwise.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> with GuacamoleDB() as db:
        ...     if usergroup_exists(db.cursor, 'admins'):
        ...         print("Admin group exists")
    """
    cursor.execute(
        """
        SELECT COUNT(*) FROM guacamole_entity
        WHERE name = %s AND type = 'USER_GROUP'
    """,
        (group_name,),
    )
    return cursor.fetchone()[0] > 0


def list_usergroups(cursor) -> List[str]:
    """Retrieve all user groups from the Guacamole database.

    Queries the guacamole_entity table to find all entities of type 'USER_GROUP'
    and returns them as an alphabetically sorted list.

    Args:
        cursor: Database cursor for executing queries

    Returns:
        List of user group names sorted alphabetically.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> with GuacamoleDB() as db:
        ...     groups = list_usergroups(db.cursor)
        ...     print(f"Found groups: {', '.join(groups)}")
    """
    cursor.execute(
        """
        SELECT name
        FROM guacamole_entity
        WHERE type = 'USER_GROUP'
        ORDER BY name
    """
    )
    return [row[0] for row in cursor.fetchall()]


def create_usergroup(cursor, group_name: str) -> None:
    """Create a new user group in the Guacamole database.

    Creates both the entity record and the user group record for a new
    user group with disabled status set to FALSE (enabled).

    Args:
        cursor: Database cursor for executing queries
        group_name: The name for the new user group.

    Raises:
        mysql.connector.Error: If database operations fail.

    Example:
        >>> with GuacamoleDB() as db:
        ...     create_usergroup(db.cursor, 'developers')
    """
    # Create entity
    cursor.execute(
        """
        INSERT INTO guacamole_entity (name, type)
        VALUES (%s, 'USER_GROUP')
    """,
        (group_name,),
    )

    # Create group
    cursor.execute(
        """
        INSERT INTO guacamole_user_group (entity_id, disabled)
        SELECT entity_id, FALSE
        FROM guacamole_entity
        WHERE name = %s AND type = 'USER_GROUP'
    """,
        (group_name,),
    )


def delete_usergroup(cursor, group_name: str) -> None:
    """Delete a user group and all associated data from the Guacamole database.

    Removes a user group completely from the system, including their entity record,
    group account, group memberships, and all permissions. This operation
    cascades through all related tables to maintain database integrity.

    Args:
        cursor: Database cursor for executing queries
        group_name: The user group name to delete.

    Raises:
        ValueError: If the user group doesn't exist.
        mysql.connector.Error: If database operations fail.

    Note:
        This is a destructive operation that cannot be undone. The user group and
        all their associated permissions and memberships are permanently
        removed. Deletions are performed in the correct order to respect
        foreign key constraints.

    Example:
        >>> with GuacamoleDB() as db:
        ...     delete_usergroup(db.cursor, 'oldgroup')
    """
    if not usergroup_exists(cursor, group_name):
        raise ValueError(f"User group '{group_name}' not found")

    # Delete group memberships
    cursor.execute(
        """
        DELETE FROM guacamole_user_group_member
        WHERE user_group_id IN (
            SELECT user_group_id FROM guacamole_user_group
            WHERE entity_id IN (
                SELECT entity_id FROM guacamole_entity
                WHERE name = %s AND type = 'USER_GROUP'
            )
        )
    """,
        (group_name,),
    )

    # Delete group permissions
    cursor.execute(
        """
        DELETE FROM guacamole_connection_permission
        WHERE entity_id IN (
            SELECT entity_id FROM guacamole_entity
            WHERE name = %s AND type = 'USER_GROUP'
        )
    """,
        (group_name,),
    )

    # Delete user group
    cursor.execute(
        """
        DELETE FROM guacamole_user_group
        WHERE entity_id IN (
            SELECT entity_id FROM guacamole_entity
            WHERE name = %s AND type = 'USER_GROUP'
        )
    """,
        (group_name,),
    )

    # Delete entity
    cursor.execute(
        """
        DELETE FROM guacamole_entity
        WHERE name = %s AND type = 'USER_GROUP'
    """,
        (group_name,),
    )