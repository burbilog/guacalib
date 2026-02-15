#!/usr/bin/env python3
"""User group repository for Guacamole database operations."""

import mysql.connector

from .base import BaseGuacamoleRepository


class UserGroupRepository(BaseGuacamoleRepository):
    """Repository for user group-related database operations."""

    def list_usergroups(self):
        """List all user groups.

        Returns:
            list: List of group names
        """
        try:
            self.cursor.execute(
                """
                SELECT name
                FROM guacamole_entity
                WHERE type = 'USER_GROUP'
                ORDER BY name
            """
            )
            return [row[0] for row in self.cursor.fetchall()]
        except mysql.connector.Error as e:
            print(f"Error listing usergroups: {e}")
            raise

    def usergroup_exists(self, group_name):
        """Check if a group with the given name exists.

        Args:
            group_name: Group name to check

        Returns:
            bool: True if group exists
        """
        try:
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM guacamole_entity
                WHERE name = %s AND type = 'USER_GROUP'
            """,
                (group_name,),
            )
            return self.cursor.fetchone()[0] > 0
        except mysql.connector.Error as e:
            print(f"Error checking usergroup existence: {e}")
            raise

    def usergroup_exists_by_id(self, group_id):
        """Check if a usergroup exists by ID.

        Args:
            group_id: Group ID to check

        Returns:
            bool: True if group exists
        """
        try:
            self.cursor.execute(
                """
                SELECT user_group_id FROM guacamole_user_group
                WHERE user_group_id = %s
            """,
                (group_id,),
            )
            return self.cursor.fetchone() is not None
        except mysql.connector.Error as e:
            raise ValueError(f"Database error while checking usergroup existence: {e}")

    def get_usergroup_id(self, group_name):
        """Get user group ID by name.

        Args:
            group_name: Group name

        Returns:
            int: Group ID

        Raises:
            Exception: If group not found
        """
        try:
            self.cursor.execute(
                """
                SELECT user_group_id
                FROM guacamole_user_group g
                JOIN guacamole_entity e ON g.entity_id = e.entity_id
                WHERE e.name = %s AND e.type = 'USER_GROUP'
            """,
                (group_name,),
            )
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                raise Exception(f"Usergroup '{group_name}' not found")
        except mysql.connector.Error as e:
            print(f"Error getting usergroup ID: {e}")
            raise

    def get_usergroup_name_by_id(self, group_id):
        """Get usergroup name by ID.

        Args:
            group_id: Group ID

        Returns:
            str: Group name

        Raises:
            ValueError: If group not found
        """
        try:
            self.cursor.execute(
                """
                SELECT e.name FROM guacamole_entity e
                JOIN guacamole_user_group g ON e.entity_id = g.entity_id
                WHERE g.user_group_id = %s
            """,
                (group_id,),
            )
            result = self.cursor.fetchone()
            if not result:
                raise ValueError(f"Usergroup with ID {group_id} not found")
            return result[0]
        except mysql.connector.Error as e:
            raise ValueError(f"Database error while getting usergroup name: {e}")

    def resolve_usergroup_id(self, group_name=None, group_id=None):
        """Validate inputs and resolve to user_group_id.

        Args:
            group_name: Group name (optional)
            group_id: Group ID (optional)

        Returns:
            int: Resolved group ID

        Raises:
            ValueError: If invalid inputs or group not found
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
                self.cursor.execute(
                    """
                    SELECT user_group_id FROM guacamole_user_group
                    WHERE user_group_id = %s
                """,
                    (group_id,),
                )
                result = self.cursor.fetchone()
                if not result:
                    raise ValueError(f"Usergroup with ID {group_id} not found")
                return group_id
            except mysql.connector.Error as e:
                raise ValueError(f"Database error while resolving usergroup ID: {e}")

        # If name provided, resolve to ID
        if group_name is not None:
            try:
                self.cursor.execute(
                    """
                    SELECT user_group_id FROM guacamole_user_group g
                    JOIN guacamole_entity e ON g.entity_id = e.entity_id
                    WHERE e.name = %s
                """,
                    (group_name,),
                )
                result = self.cursor.fetchone()
                if not result:
                    raise ValueError(f"Usergroup '{group_name}' not found")
                return result[0]
            except mysql.connector.Error as e:
                raise ValueError(f"Database error while resolving usergroup name: {e}")

    def create_usergroup(self, group_name):
        """Create a new user group.

        Args:
            group_name: Name for the new group
        """
        try:
            # Create entity
            self.cursor.execute(
                """
                INSERT INTO guacamole_entity (name, type)
                VALUES (%s, 'USER_GROUP')
            """,
                (group_name,),
            )

            # Create group
            self.cursor.execute(
                """
                INSERT INTO guacamole_user_group (entity_id, disabled)
                SELECT entity_id, FALSE
                FROM guacamole_entity
                WHERE name = %s AND type = 'USER_GROUP'
            """,
                (group_name,),
            )

        except mysql.connector.Error as e:
            print(f"Error creating usergroup: {e}")
            raise

    def delete_existing_usergroup(self, group_name):
        """Delete a user group by name and all associated data.

        Args:
            group_name: Group name to delete
        """
        try:
            self.debug_print(f"Deleting usergroup: {group_name}")
            # Delete group memberships
            self.cursor.execute(
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
            self.cursor.execute(
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
            self.cursor.execute(
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
            self.cursor.execute(
                """
                DELETE FROM guacamole_entity
                WHERE name = %s AND type = 'USER_GROUP'
            """,
                (group_name,),
            )

        except mysql.connector.Error as e:
            print(f"Error deleting existing usergroup: {e}")
            raise

    def delete_existing_usergroup_by_id(self, group_id):
        """Delete a usergroup by ID and all its associated data.

        Args:
            group_id: Group ID to delete
        """
        try:
            # Validate and resolve the group ID
            resolved_group_id = self.resolve_usergroup_id(group_id=group_id)
            group_name = self.get_usergroup_name_by_id(resolved_group_id)

            self.debug_print(
                f"Attempting to delete usergroup: {group_name} (ID: {resolved_group_id})"
            )

            # Delete group memberships
            self.cursor.execute(
                """
                DELETE FROM guacamole_user_group_member
                WHERE user_group_id = %s
            """,
                (resolved_group_id,),
            )

            # Delete group permissions
            self.cursor.execute(
                """
                DELETE FROM guacamole_connection_permission
                WHERE entity_id IN (
                    SELECT entity_id FROM guacamole_user_group
                    WHERE user_group_id = %s
                )
            """,
                (resolved_group_id,),
            )

            # Delete user group
            self.cursor.execute(
                """
                DELETE FROM guacamole_user_group
                WHERE user_group_id = %s
            """,
                (resolved_group_id,),
            )

            # Delete entity
            self.cursor.execute(
                """
                DELETE FROM guacamole_entity
                WHERE entity_id IN (
                    SELECT entity_id FROM guacamole_user_group
                    WHERE user_group_id = %s
                )
            """,
                (resolved_group_id,),
            )

        except mysql.connector.Error as e:
            print(f"Error deleting existing usergroup: {e}")
            raise
        except ValueError as e:
            print(f"Error: {e}")
            raise

    def add_user_to_usergroup(self, username, group_name):
        """Add a user to a user group.

        Args:
            username: Username to add
            group_name: Group name to add user to
        """
        try:
            # Get the group ID
            group_id = self.get_usergroup_id(group_name)

            # Get the user's entity ID
            self.cursor.execute(
                """
                SELECT entity_id
                FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
            """,
                (username,),
            )
            user_entity_id = self.cursor.fetchone()[0]

            # Add user to group
            self.cursor.execute(
                """
                INSERT INTO guacamole_user_group_member
                (user_group_id, member_entity_id)
                VALUES (%s, %s)
            """,
                (group_id, user_entity_id),
            )

            # Grant group permissions to user
            self.cursor.execute(
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

            self.debug_print(
                f"Successfully added user '{username}' to usergroup '{group_name}'"
            )

        except mysql.connector.Error as e:
            print(f"Error adding user to usergroup: {e}")
            raise

    def remove_user_from_usergroup(self, username, group_name):
        """Remove a user from a user group.

        Args:
            username: Username to remove
            group_name: Group name to remove user from
        """
        try:
            # Get the group ID
            group_id = self.get_usergroup_id(group_name)

            # Get the user's entity ID
            self.cursor.execute(
                """
                SELECT entity_id
                FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
            """,
                (username,),
            )
            user_entity_id = self.cursor.fetchone()[0]

            # Check if user is actually in the group
            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM guacamole_user_group_member
                WHERE user_group_id = %s AND member_entity_id = %s
            """,
                (group_id, user_entity_id),
            )
            if self.cursor.fetchone()[0] == 0:
                raise ValueError(f"User '{username}' is not in group '{group_name}'")

            # Remove user from group
            self.cursor.execute(
                """
                DELETE FROM guacamole_user_group_member
                WHERE user_group_id = %s AND member_entity_id = %s
            """,
                (group_id, user_entity_id),
            )

            # Revoke group permissions from user
            self.cursor.execute(
                """
                DELETE FROM guacamole_user_group_permission
                WHERE entity_id = %s AND affected_user_group_id = %s
            """,
                (user_entity_id, group_id),
            )

            self.debug_print(
                f"Successfully removed user '{username}' from usergroup '{group_name}'"
            )

        except mysql.connector.Error as e:
            print(f"Error removing user from group: {e}")
            raise

    def list_groups_with_users(self):
        """List all groups with their users.

        Returns:
            dict: Dictionary mapping group names to list of usernames
        """
        query = """
            SELECT
                e.name as groupname,
                GROUP_CONCAT(DISTINCT ue.name) as usernames
            FROM guacamole_entity e
            LEFT JOIN guacamole_user_group ug ON e.entity_id = ug.entity_id
            LEFT JOIN guacamole_user_group_member ugm ON ug.user_group_id = ugm.user_group_id
            LEFT JOIN guacamole_entity ue ON ugm.member_entity_id = ue.entity_id AND ue.type = 'USER'
            WHERE e.type = 'USER_GROUP'
            GROUP BY e.name
            ORDER BY e.name
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()

        groups_users = {}
        for row in results:
            groupname = row[0]
            usernames = row[1].split(",") if row[1] else []
            groups_users[groupname] = usernames

        return groups_users

    def list_usergroups_with_users_and_connections(self):
        """List all groups with their users and connections.

        Returns:
            dict: Dictionary with group info including id, users, and connections
        """
        try:
            # Get users per group with IDs
            self.cursor.execute(
                """
                SELECT
                    e.name as groupname,
                    ug.user_group_id,
                    GROUP_CONCAT(DISTINCT ue.name) as users
                FROM guacamole_entity e
                LEFT JOIN guacamole_user_group ug ON e.entity_id = ug.entity_id
                LEFT JOIN guacamole_user_group_member ugm ON ug.user_group_id = ugm.user_group_id
                LEFT JOIN guacamole_entity ue ON ugm.member_entity_id = ue.entity_id AND ue.type = 'USER'
                WHERE e.type = 'USER_GROUP'
                GROUP BY e.name, ug.user_group_id
            """
            )
            groups_users = {
                (row[0], row[1]): row[2].split(",") if row[2] else []
                for row in self.cursor.fetchall()
            }

            # Get connections per group with IDs
            self.cursor.execute(
                """
                SELECT
                    e.name as groupname,
                    ug.user_group_id,
                    GROUP_CONCAT(DISTINCT c.connection_name) as connections
                FROM guacamole_entity e
                LEFT JOIN guacamole_user_group ug ON e.entity_id = ug.entity_id
                LEFT JOIN guacamole_connection_permission cp ON e.entity_id = cp.entity_id
                LEFT JOIN guacamole_connection c ON cp.connection_id = c.connection_id
                WHERE e.type = 'USER_GROUP'
                GROUP BY e.name, ug.user_group_id
            """
            )
            groups_connections = {
                (row[0], row[1]): row[2].split(",") if row[2] else []
                for row in self.cursor.fetchall()
            }

            # Combine results
            result = {}
            for group_key in set(groups_users.keys()).union(groups_connections.keys()):
                group_name, group_id = group_key
                result[group_name] = {
                    "id": group_id,
                    "users": groups_users.get(group_key, []),
                    "connections": groups_connections.get(group_key, []),
                }
            return result
        except mysql.connector.Error as e:
            print(f"Error listing groups with users and connections: {e}")
            raise
