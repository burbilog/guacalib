#!/usr/bin/env python3
"""User repository for Guacamole database operations."""

import mysql.connector
import hashlib
import os
import binascii

from .base import BaseGuacamoleRepository
from .user_parameters import USER_PARAMETERS


class UserRepository(BaseGuacamoleRepository):
    """Repository for user-related database operations."""

    USER_PARAMETERS = USER_PARAMETERS

    def list_users(self):
        """List all users.

        Returns:
            list: List of usernames
        """
        try:
            self.cursor.execute(
                """
                SELECT name
                FROM guacamole_entity
                WHERE type = 'USER'
                ORDER BY name
            """
            )
            return [row[0] for row in self.cursor.fetchall()]
        except mysql.connector.Error as e:
            print(f"Error listing users: {e}")
            raise

    def user_exists(self, username):
        """Check if a user with the given name exists.

        Args:
            username: Username to check

        Returns:
            bool: True if user exists
        """
        try:
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
            """,
                (username,),
            )
            return self.cursor.fetchone()[0] > 0
        except mysql.connector.Error as e:
            print(f"Error checking user existence: {e}")
            raise

    def create_user(self, username, password):
        """Create a new user with hashed password.

        Args:
            username: Username for the new user
            password: Plain text password
        """
        try:
            # Generate random 32-byte salt
            salt = os.urandom(32)

            # Convert salt to uppercase hex string as Guacamole expects
            salt_hex = binascii.hexlify(salt).upper()

            # Create password hash using Guacamole's method: SHA256(password + hex(salt))
            digest = hashlib.sha256(password.encode("utf-8") + salt_hex).digest()

            # Get binary representations
            password_hash = digest
            password_salt = salt

            # Create entity
            self.cursor.execute(
                """
                INSERT INTO guacamole_entity (name, type)
                VALUES (%s, 'USER')
            """,
                (username,),
            )

            # Create user with proper binary data
            self.cursor.execute(
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

        except mysql.connector.Error as e:
            print(f"Error creating user: {e}")
            raise

    def delete_existing_user(self, username):
        """Delete a user and all associated data.

        Args:
            username: Username to delete
        """
        try:
            if not self.user_exists(username):
                raise ValueError(f"User '{username}' doesn't exist")

            self.debug_print(f"Deleting user: {username}")
            # Delete user group permissions first
            self.cursor.execute(
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
            self.cursor.execute(
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
            self.cursor.execute(
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
            self.cursor.execute(
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
            self.cursor.execute(
                """
                DELETE FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
            """,
                (username,),
            )

        except mysql.connector.Error as e:
            print(f"Error deleting existing user: {e}")
            raise

    def change_user_password(self, username, new_password):
        """Change a user's password.

        Args:
            username: Username
            new_password: New plain text password

        Returns:
            bool: True if successful
        """
        try:
            # Generate random 32-byte salt
            salt = os.urandom(32)

            # Convert salt to uppercase hex string as Guacamole expects
            salt_hex = binascii.hexlify(salt).upper()

            # Create password hash using Guacamole's method: SHA256(password + hex(salt))
            digest = hashlib.sha256(new_password.encode("utf-8") + salt_hex).digest()

            # Get user entity_id
            self.cursor.execute(
                """
                SELECT entity_id FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
            """,
                (username,),
            )
            result = self.cursor.fetchone()
            if not result:
                raise ValueError(f"User '{username}' not found")
            entity_id = result[0]

            # Update the password
            self.cursor.execute(
                """
                UPDATE guacamole_user
                SET password_hash = %s,
                    password_salt = %s,
                    password_date = NOW()
                WHERE entity_id = %s
            """,
                (digest, salt, entity_id),
            )

            if self.cursor.rowcount == 0:
                raise ValueError(f"Failed to update password for user '{username}'")

            return True

        except mysql.connector.Error as e:
            print(f"Error changing password: {e}")
            raise

    def modify_user(self, username, param_name, param_value):
        """Modify a user parameter in the guacamole_user table.

        Args:
            username: Username
            param_name: Parameter name to modify
            param_value: New parameter value

        Returns:
            bool: True if successful
        """
        try:
            # Validate parameter name
            if param_name not in self.USER_PARAMETERS:
                raise ValueError(
                    f"Invalid parameter: {param_name}. Run 'guacaman user modify' without arguments to see allowed parameters."
                )

            # Validate parameter value based on type
            param_type = self.USER_PARAMETERS[param_name]["type"]
            if param_type == "tinyint":
                if param_value not in ("0", "1"):
                    raise ValueError(f"Parameter {param_name} must be 0 or 1")
                param_value = int(param_value)

            # Get user entity_id
            self.cursor.execute(
                """
                SELECT entity_id FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
            """,
                (username,),
            )
            result = self.cursor.fetchone()
            if not result:
                raise ValueError(f"User '{username}' not found")
            entity_id = result[0]

            # Update the parameter
            query = f"""
                UPDATE guacamole_user
                SET {param_name} = %s
                WHERE entity_id = %s
            """
            self.cursor.execute(query, (param_value, entity_id))

            if self.cursor.rowcount == 0:
                raise ValueError(f"Failed to update user parameter: {param_name}")

            return True

        except mysql.connector.Error as e:
            print(f"Error modifying user parameter: {e}")
            raise

    def list_users_with_usergroups(self):
        """List all users with their group memberships.

        Returns:
            dict: Dictionary mapping usernames to list of group names
        """
        query = """
            SELECT DISTINCT
                e1.name as username,
                GROUP_CONCAT(e2.name) as groupnames
            FROM guacamole_entity e1
            JOIN guacamole_user u ON e1.entity_id = u.entity_id
            LEFT JOIN guacamole_user_group_member ugm
                ON e1.entity_id = ugm.member_entity_id
            LEFT JOIN guacamole_user_group ug
                ON ugm.user_group_id = ug.user_group_id
            LEFT JOIN guacamole_entity e2
                ON ug.entity_id = e2.entity_id
            WHERE e1.type = 'USER'
            GROUP BY e1.name
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()

        users_groups = {}
        for row in results:
            username = row[0]
            groupnames = row[1].split(",") if row[1] else []
            users_groups[username] = groupnames

        return users_groups
