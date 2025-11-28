"""
Users Repository Module

This module contains SQL repository functions for user management operations.
It provides stateless functions that accept a database cursor and parameters,
returning data without any GuacamoleDB class dependencies.

Functions:
    user_exists: Check if a user exists in the database
    create_user: Create a new user with password hashing
    delete_user: Delete a user and all associated data
    modify_user_parameter: Modify a specific user parameter
    change_user_password: Change a user's password with new salt
    list_users: List all users in the database

All functions are designed to be stateless and accept a cursor as the first parameter.
"""

import hashlib
import os
import binascii
import secrets
import mysql.connector
from typing import List, Union
from .db_user_parameters import USER_PARAMETERS


def user_exists(cursor, username: str) -> bool:
    """Check if a user exists in the Guacamole database.

    Queries the guacamole_entity table to determine if a user with the
    specified username exists.

    Args:
        cursor: Database cursor for executing queries
        username: The username to check for existence.

    Returns:
        True if the user exists, False otherwise.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> with GuacamoleDB() as db:
        ...     if user_exists(db.cursor, 'admin'):
        ...         print("Admin user exists")
    """
    cursor.execute(
        """
        SELECT COUNT(*) FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )
    return cursor.fetchone()[0] > 0


def list_users(cursor) -> List[str]:
    """Retrieve all users from the Guacamole database.

    Queries the guacamole_entity table to find all entities of type 'USER'
    and returns them as an alphabetically sorted list.

    Args:
        cursor: Database cursor for executing queries

    Returns:
        List of usernames sorted alphabetically.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> with GuacamoleDB() as db:
        ...     users = list_users(db.cursor)
        ...     print(f"Found users: {', '.join(users)}")
    """
    cursor.execute(
        """
        SELECT name
        FROM guacamole_entity
        WHERE type = 'USER'
        ORDER BY name
    """
    )
    return [row[0] for row in cursor.fetchall()]


def create_user(cursor, username: str, password: str) -> None:
    """Create a new user in the Guacamole database.

    Creates a new user with secure password hashing using Guacamole's
    authentication method. Generates a random salt and hashes the password
    using SHA256.

    Args:
        cursor: Database cursor for executing queries
        username: The username for the new user.
        password: The password for the new user.

    Raises:
        mysql.connector.Error: If database operations fail.

    Note:
        Uses Guacamole's password hashing method: SHA256(password + hex(salt)).
        The salt is a random 32-byte value for security. This method creates
        both the entity record and the user record with password credentials.

    Example:
        >>> with GuacamoleDB() as db:
        ...     create_user(db.cursor, 'newuser', 'securepassword')
    """
    # Generate random 32-byte salt
    salt = os.urandom(32)

    # Convert salt to uppercase hex string as Guacamole expects
    salt_hex = binascii.hexlify(salt).upper()

    # Create password hash using Guacamole's method: SHA256(password + hex(salt))
    digest = hashlib.sha256(password.encode("utf-8") + salt_hex).digest()

    # Get binary representations
    password_hash = digest  # SHA256 hash of (password + hex(salt))
    password_salt = salt  # Original raw bytes salt

    # Create entity
    cursor.execute(
        """
        INSERT INTO guacamole_entity (name, type)
        VALUES (%s, 'USER')
    """,
        (username,),
    )

    # Create user with proper binary data
    cursor.execute(
        """
        INSERT INTO guacamole_user
            (entity_id, password_hash, password_salt, password_date)
        SELECT
            entity_id,
            %s,
            %s,
            NOW()
        FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (password_hash, password_salt, username),
    )


def delete_user(cursor, username: str) -> None:
    """Delete a user and all associated data from the Guacamole database.

    Removes a user completely from the system, including their entity record,
    user account, group memberships, and all permissions. This operation
    cascades through all related tables to maintain database integrity.

    Args:
        cursor: Database cursor for executing queries
        username: The username to delete.

    Raises:
        ValueError: If the user doesn't exist.
        mysql.connector.Error: If database operations fail.

    Note:
        This is a destructive operation that cannot be undone. The user and
        all their associated permissions and memberships are permanently
        removed. Deletions are performed in the correct order to respect
        foreign key constraints.

    Example:
        >>> with GuacamoleDB() as db:
        ...     delete_user(db.cursor, 'olduser')
    """
    if not user_exists(cursor, username):
        raise ValueError(f"User '{username}' not found")

    # Delete user group permissions first
    cursor.execute(
        """
        DELETE FROM guacamole_user_group_permission
        WHERE entity_id IN (
            SELECT entity_id FROM guacamole_entity
            WHERE name = %s AND type = 'USER'
        )
    """,
        (username,),
    )

    # Delete user group memberships
    cursor.execute(
        """
        DELETE FROM guacamole_user_group_member
        WHERE member_entity_id IN (
            SELECT entity_id FROM guacamole_entity
            WHERE name = %s AND type = 'USER'
        )
    """,
        (username,),
    )

    # Delete user permissions
    cursor.execute(
        """
        DELETE FROM guacamole_connection_permission
        WHERE entity_id IN (
            SELECT entity_id FROM guacamole_entity
            WHERE name = %s AND type = 'USER'
        )
    """,
        (username,),
    )

    # Delete user
    cursor.execute(
        """
        DELETE FROM guacamole_user
        WHERE entity_id IN (
            SELECT entity_id FROM guacamole_entity
            WHERE name = %s AND type = 'USER'
        )
    """,
        (username,),
    )

    # Delete entity
    cursor.execute(
        """
        DELETE FROM guacamole_entity
        WHERE name = %s AND type = 'USER'
    """,
        (username,),
    )


def modify_user_parameter(
    cursor, username: str, param_name: str, param_value: Union[str, int]
) -> bool:
    """Modify a user parameter in the Guacamole database.

    Updates user account parameters such as disabled status, expiration dates,
    time windows, timezone, and contact information.

    Args:
        cursor: Database cursor for executing queries
        username: The username to modify.
        param_name: The parameter name to modify.
        param_value: The new value for the parameter.

    Returns:
        True if the parameter was successfully updated.

    Raises:
        ValueError: If parameter name is invalid, user doesn't exist,
                   or parameter update fails.
        mysql.connector.Error: If database operations fail.

    Note:
        Valid parameters are defined in USER_PARAMETERS. Boolean values
        should be passed as '0' (false) or '1' (true) for tinyint fields.

    Example:
        >>> with GuacamoleDB() as db:
        ...     modify_user_parameter(db.cursor, 'user1', 'disabled', '1')
        ...     modify_user_parameter(db.cursor, 'user1', 'full_name', 'John Doe')
    """
    # Validate parameter name
    if param_name not in USER_PARAMETERS:
        raise ValueError(
            f"Invalid parameter: {param_name}. Run 'guacaman user modify' without arguments to see allowed parameters."
        )

    # Validate parameter value based on type
    param_type = USER_PARAMETERS[param_name]["type"]
    if param_type == "tinyint":
        if param_value not in ("0", "1"):
            raise ValueError(f"Parameter {param_name} must be 0 or 1")
        param_value = int(param_value)

    # Get user entity_id
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

    # Update the parameter
    query = f"""
        UPDATE guacamole_user
        SET {param_name} = %s
        WHERE entity_id = %s
    """
    cursor.execute(query, (param_value, entity_id))

    if cursor.rowcount == 0:
        raise ValueError(f"Failed to update user parameter: {param_name}")

    return True


def change_user_password(cursor, username: str, new_password: str) -> bool:
    """Change the password for an existing user.

    Updates a user's password with secure hashing using a new random salt.
    Uses the same hashing method as create_user() for consistency.

    Args:
        cursor: Database cursor for executing queries
        username: The username whose password should be changed.
        new_password: The new password to set.

    Returns:
        True if password was successfully changed.

    Raises:
        ValueError: If user is not found or password update fails.
        mysql.connector.Error: If database operations fail.

    Note:
        Generates a new random salt for security. The password date is
        updated to track when the password was last changed.

    Example:
        >>> with GuacamoleDB() as db:
        ...     change_user_password(db.cursor, 'user1', 'newsecurepassword')
    """
    # Generate random 32-byte salt
    salt = os.urandom(32)

    # Convert salt to uppercase hex string as Guacamole expects
    salt_hex = binascii.hexlify(salt).upper()

    # Create password hash using Guacamole's method: SHA256(password + hex(salt))
    digest = hashlib.sha256(new_password.encode("utf-8") + salt_hex).digest()

    # Get user entity_id
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

    # Update the password
    cursor.execute(
        """
        UPDATE guacamole_user
        SET password_hash = %s,
            password_salt = %s,
            password_date = NOW()
        WHERE entity_id = %s
    """,
        (digest, salt, entity_id),
    )

    if cursor.rowcount == 0:
        raise ValueError(f"Failed to update password for user '{username}'")

    return True
