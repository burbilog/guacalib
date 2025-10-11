#!/usr/bin/env python3

import mysql.connector
import configparser
import sys
import hashlib
import os
import binascii
from typing import Optional, Union, Dict, List, Tuple, Any, Type, Callable

from mysql.connector.connection import MySQLConnection

from .db_connection_parameters import CONNECTION_PARAMETERS
from .db_user_parameters import USER_PARAMETERS

# Custom type definitions
ConnectionConfig = Dict[str, str]
ConnectionParameters = Dict[str, Union[str, int, bool]]
UserParameters = Dict[str, Dict[str, Union[str, str, str]]]
UserInfo = Tuple[str, List[str]]
ConnectionInfo = Tuple[int, str, str, str, str, str, str, List[str]]
GroupInfo = Dict[str, Dict[str, Union[int, List[str]]]]
PermissionInfo = Tuple[str, str, str]  # (entity_name, entity_type, permission)


class GuacamoleDB:
    CONNECTION_PARAMETERS = CONNECTION_PARAMETERS
    USER_PARAMETERS = USER_PARAMETERS

    def __init__(self, config_file: str = "db_config.ini", debug: bool = False) -> None:
        self.debug = debug
        self.db_config = self.read_config(config_file)
        self.conn = self.connect_db()
        self.cursor = self.conn.cursor()

    def debug_print(self, *args: Any, **kwargs: Any) -> None:
        """Print debug messages if debug mode is enabled"""
        if self.debug:
            print("[DEBUG]", *args, **kwargs)

    def __enter__(self) -> "GuacamoleDB":
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[Any]) -> None:
        if self.cursor:
            self.cursor.close()
        if self.conn:
            try:
                # Always commit unless there was an exception
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
                self.conn.close()

    @staticmethod
    def read_config(config_file: str) -> ConnectionConfig:
        config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            print(f"Error: Config file not found: {config_file}")
            print(
                "Please create a config file at ~/.guacaman.ini with the following format:"
            )
            print("[mysql]")
            print("host = your_mysql_host")
            print("user = your_mysql_user")
            print("password = your_mysql_password")
            print("database = your_mysql_database")
            sys.exit(1)

        try:
            config.read(config_file)
            if "mysql" not in config:
                print(f"Error: Missing [mysql] section in config file: {config_file}")
                sys.exit(1)

            required_keys = ["host", "user", "password", "database"]
            missing_keys = [key for key in required_keys if key not in config["mysql"]]
            if missing_keys:
                print(
                    f"Error: Missing required keys in [mysql] section: {', '.join(missing_keys)}"
                )
                print(f"Config file: {config_file}")
                sys.exit(1)

            return {
                "host": config["mysql"]["host"],
                "user": config["mysql"]["user"],
                "password": config["mysql"]["password"],
                "database": config["mysql"]["database"],
            }
        except Exception as e:
            print(f"Error reading config file {config_file}: {str(e)}")
            sys.exit(1)

    def connect_db(self) -> MySQLConnection:
        try:
            return mysql.connector.connect(
                **self.db_config, charset="utf8mb4", collation="utf8mb4_general_ci"
            )
        except mysql.connector.Error as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)

    def list_users(self) -> List[str]:
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

    def list_usergroups(self) -> List[str]:
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

    def usergroup_exists(self, group_name: str) -> bool:
        """Check if a group with the given name exists"""
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

    def get_usergroup_id(self, group_name: str) -> int:
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

    def user_exists(self, username: str) -> bool:
        """Check if a user with the given name exists"""
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

    # Define allowed user parameters as a class attribute
    USER_PARAMETERS = {
        "disabled": {
            "type": "tinyint",
            "description": "Whether the user is disabled (0=enabled, 1=disabled)",
            "default": "0",
        },
        "expired": {
            "type": "tinyint",
            "description": "Whether the user account is expired (0=active, 1=expired)",
            "default": "0",
        },
        "access_window_start": {
            "type": "time",
            "description": "Start of allowed access time window (HH:MM:SS)",
            "default": "NULL",
        },
        "access_window_end": {
            "type": "time",
            "description": "End of allowed access time window (HH:MM:SS)",
            "default": "NULL",
        },
        "valid_from": {
            "type": "date",
            "description": "Date when account becomes valid (YYYY-MM-DD)",
            "default": "NULL",
        },
        "valid_until": {
            "type": "date",
            "description": "Date when account expires (YYYY-MM-DD)",
            "default": "NULL",
        },
        "timezone": {
            "type": "string",
            "description": 'User\'s timezone (e.g., "America/New_York")',
            "default": "NULL",
        },
        "full_name": {
            "type": "string",
            "description": "User's full name",
            "default": "NULL",
        },
        "email_address": {
            "type": "string",
            "description": "User's email address",
            "default": "NULL",
        },
        "organization": {
            "type": "string",
            "description": "User's organization",
            "default": "NULL",
        },
        "organizational_role": {
            "type": "string",
            "description": "User's role within the organization",
            "default": "NULL",
        },
    }

    def get_connection_group_id_by_name(self, group_name: str) -> Optional[int]:
        """Get connection_group_id by name from guacamole_connection_group"""
        try:
            if not group_name:  # Handle empty group name as explicit NULL
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
                raise ValueError(f"Connection group '{group_name}' not found")
            return result[0]
        except mysql.connector.Error as e:
            print(f"Error getting connection group ID: {e}")
            raise

    def modify_connection_parent_group(
        self, connection_name: Optional[str] = None, connection_id: Optional[int] = None, group_name: Optional[str] = None
    ) -> bool:
        """Set parent connection group for a connection"""
        try:
            # Use resolver to get connection_id and validate inputs
            resolved_connection_id = self.resolve_connection_id(
                connection_name, connection_id
            )

            group_id = (
                self.get_connection_group_id_by_name(group_name) if group_name else None
            )

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
                raise ValueError(
                    f"Connection with ID {resolved_connection_id} not found"
                )
            current_parent_id = result[0]

            # Get connection name for error messages if we only have ID
            if connection_name is None:
                connection_name = self.get_connection_name_by_id(resolved_connection_id)

            # Check if we're trying to set to same group
            if group_id == current_parent_id:
                if group_id is None:
                    raise ValueError(
                        f"Connection '{connection_name}' already has no parent group"
                    )
                else:
                    raise ValueError(
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
                raise ValueError(
                    f"Failed to update parent group for connection '{connection_name}'"
                )

            return True

        except mysql.connector.Error as e:
            print(f"Error modifying connection parent group: {e}")
            raise

    def get_connection_user_permissions(self, connection_name: str) -> List[str]:
        """Get list of users with direct permissions to a connection"""
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
            print(f"Error getting connection user permissions: {e}")
            raise

    def modify_connection(
        self,
        connection_name: Optional[str] = None,
        connection_id: Optional[int] = None,
        param_name: Optional[str] = None,
        param_value: Optional[Union[str, int]] = None,
    ) -> bool:
        """Modify a connection parameter in either guacamole_connection or guacamole_connection_parameter table"""
        try:
            # Validate parameter name
            if param_name not in self.CONNECTION_PARAMETERS:
                raise ValueError(
                    f"Invalid parameter: {param_name}. Run 'guacaman conn modify' without arguments to see allowed parameters."
                )

            # Use resolver to get connection_id and validate inputs
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
                        raise ValueError(f"Parameter {param_name} must be an integer")

                # Update in guacamole_connection table
                query = f"""
                    UPDATE guacamole_connection 
                    SET {param_name} = %s
                    WHERE connection_id = %s
                """
                self.cursor.execute(query, (param_value, resolved_connection_id))

            elif param_table == "parameter":
                # Special handling for read-only parameter
                if param_name == "read-only":
                    # Validate boolean value
                    if param_value.lower() not in ("true", "false"):
                        raise ValueError(
                            "Parameter read-only must be 'true' or 'false'"
                        )

                    # For read-only, we either add with 'true' or remove the parameter
                    if param_value.lower() == "true":
                        # Check if parameter already exists
                        self.cursor.execute(
                            """
                            SELECT parameter_value FROM guacamole_connection_parameter
                            WHERE connection_id = %s AND parameter_name = %s
                        """,
                            (resolved_connection_id, param_name),
                        )

                        if self.cursor.fetchone():
                            # Update existing parameter
                            self.cursor.execute(
                                """
                                UPDATE guacamole_connection_parameter
                                SET parameter_value = 'true'
                                WHERE connection_id = %s AND parameter_name = %s
                            """,
                                (resolved_connection_id, param_name),
                            )
                        else:
                            # Insert new parameter
                            self.cursor.execute(
                                """
                                INSERT INTO guacamole_connection_parameter
                                (connection_id, parameter_name, parameter_value)
                                VALUES (%s, %s, 'true')
                            """,
                                (resolved_connection_id, param_name),
                            )
                    else:  # param_value.lower() == 'false'
                        # Remove the parameter if it exists
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
                            raise ValueError(
                                "color-depth must be one of: 8, 16, 24, 32"
                            )

                    # Regular parameter handling
                    # Check if parameter already exists
                    self.cursor.execute(
                        """
                        SELECT parameter_value FROM guacamole_connection_parameter
                        WHERE connection_id = %s AND parameter_name = %s
                    """,
                        (resolved_connection_id, param_name),
                    )

                    if self.cursor.fetchone():
                        # Update existing parameter
                        self.cursor.execute(
                            """
                            UPDATE guacamole_connection_parameter
                            SET parameter_value = %s
                            WHERE connection_id = %s AND parameter_name = %s
                        """,
                            (param_value, resolved_connection_id, param_name),
                        )
                    else:
                        # Insert new parameter
                        self.cursor.execute(
                            """
                            INSERT INTO guacamole_connection_parameter
                            (connection_id, parameter_name, parameter_value)
                            VALUES (%s, %s, %s)
                        """,
                            (resolved_connection_id, param_name, param_value),
                        )

            if self.cursor.rowcount == 0:
                raise ValueError(f"Failed to update connection parameter: {param_name}")

            return True

        except mysql.connector.Error as e:
            print(f"Error modifying connection parameter: {e}")
            raise

    def change_user_password(self, username: str, new_password: str) -> bool:
        """Change a user's password"""
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

    def modify_user(self, username: str, param_name: str, param_value: Union[str, int]) -> bool:
        """Modify a user parameter in the guacamole_user table"""
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

    def delete_existing_user(self, username: str) -> None:
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

    def delete_existing_usergroup(self, group_name: str) -> None:
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

    def delete_existing_usergroup_by_id(self, group_id: int) -> None:
        """Delete a usergroup by ID and all its associated data"""
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

    def delete_existing_connection(self, connection_name: Optional[str] = None, connection_id: Optional[int] = None) -> None:
        """Delete a connection and all its associated data"""
        try:
            # Use resolver to get connection_id and validate inputs
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
            print(f"Error deleting existing connection: {e}")
            raise

    def delete_connection_group(self, group_name: Optional[str] = None, group_id: Optional[int] = None) -> bool:
        """Delete a connection group and update references to it"""
        try:
            # Use resolver to get group_id and validate inputs
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

            # Commit the transaction
            self.debug_print("Committing transaction...")
            self.conn.commit()
            self.debug_print(f"Successfully deleted connection group '{group_name}'")
            return True

        except mysql.connector.Error as e:
            print(f"Error deleting connection group: {e}")
            raise

        except mysql.connector.Error as e:
            print(f"Error deleting existing connection: {e}")
            raise

    def create_user(self, username: str, password: str) -> None:
        try:
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

    def create_usergroup(self, group_name: str) -> None:
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

    def add_user_to_usergroup(self, username: str, group_name: str) -> None:
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

    def remove_user_from_usergroup(self, username: str, group_name: str) -> None:
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

    def get_connection_group_id(self, group_path: str) -> int:
        """Resolve nested connection group path to group_id"""
        try:
            groups = group_path.split("/")
            parent_group_id = None

            self.debug_print(f"Resolving group path: {group_path}")

            for group_name in groups:
                # CORRECTED SQL - use connection_group_name directly
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
                    raise ValueError(
                        f"Group '{group_name}' not found in path '{group_path}'"
                    )

                parent_group_id = result[0]
                self.debug_print(f"Found group ID {parent_group_id} for '{group_name}'")

            return parent_group_id

        except mysql.connector.Error as e:
            print(f"Error resolving group path: {e}")
            raise

    def connection_exists(self, connection_name: Optional[str] = None, connection_id: Optional[int] = None) -> bool:
        """Check if a connection with the given name or ID exists"""
        try:
            # Use resolver to validate inputs and get connection_id
            resolved_connection_id = self.resolve_connection_id(
                connection_name, connection_id
            )
            # If resolver succeeds, connection exists
            return True
        except ValueError:
            # If resolver fails with "not found", connection doesn't exist
            return False
        except mysql.connector.Error as e:
            print(f"Error checking connection existence: {e}")
            raise

    def connection_group_exists(self, group_name: Optional[str] = None, group_id: Optional[int] = None) -> bool:
        """Check if a connection group with the given name or ID exists"""
        try:
            # Use resolver to validate inputs and get group_id
            resolved_group_id = self.resolve_conngroup_id(group_name, group_id)
            # If resolver succeeds, connection group exists
            return True
        except ValueError:
            # If resolver fails with "not found", connection group doesn't exist
            return False
        except mysql.connector.Error as e:
            print(f"Error checking connection group existence: {e}")
            raise

    def create_connection(
        self,
        connection_type: str,
        connection_name: str,
        hostname: str,
        port: Union[str, int],
        vnc_password: str,
        parent_group_id: Optional[int] = None,
    ) -> int:
        if not all([connection_name, hostname, port]):
            raise ValueError("Missing required connection parameters")

        if self.connection_exists(connection_name):
            raise ValueError(f"Connection '{connection_name}' already exists")

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
            print(f"Error creating VNC connection: {e}")
            raise

    def grant_connection_permission(
        self, entity_name, entity_type, connection_id, group_path=None
    ):
        try:
            if group_path:
                self.debug_print(f"Processing group path: {group_path}")
                parent_group_id = self.get_connection_group_id(group_path)

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
            print(f"Error granting connection permission: {e}")
            raise

    def list_users_with_usergroups(self) -> Dict[str, List[str]]:
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

    def list_connections_with_conngroups_and_parents(self) -> List[ConnectionInfo]:
        """List all connections with their groups, parent group, and user permissions"""
        try:
            # Get basic connection info with groups
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

            # Create a mapping of connection names to connection IDs
            connection_map = {
                name: conn_id for conn_id, name, _, _, _, _, _ in connections_info
            }

            # Now prepare the result array
            result = []
            for conn_info in connections_info:
                conn_id, name, protocol, host, port, groups, parent = conn_info

                # Get user permissions for this connection - THIS IS THE KEY CHANGE
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

                # Append user permissions to the connection info (include connection_id)
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
            print(f"Error listing connections: {e}")
            raise

    def get_connection_by_id(self, connection_id: int) -> Optional[ConnectionInfo]:
        """Get a specific connection by its ID"""
        try:
            # Get basic connection info with groups
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
            print(f"Error getting connection by ID: {e}")
            raise

    def list_usergroups_with_users_and_connections(self):
        """List all groups with their users and connections"""
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

    def _check_connection_group_cycle(self, group_id, parent_id):
        """Check if setting parent_id would create a cycle in connection groups"""
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

    def create_connection_group(self, group_name: str, parent_group_name: Optional[str] = None) -> bool:
        """Create a new connection group"""
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
                    raise ValueError(
                        f"Parent connection group '{parent_group_name}' not found"
                    )
                parent_group_id = result[0]

                # Check for cycles - since this is a new group, we can't be creating a cycle
                # but we should still validate the parent exists and is valid
                if self._check_connection_group_cycle(None, parent_group_id):
                    raise ValueError(
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
                raise ValueError("Failed to create connection group - no ID returned")

            return True

        except mysql.connector.Error as e:
            print(f"Error creating connection group: {e}")
            raise

    def grant_connection_permission_to_user(self, username: str, connection_name: str) -> bool:
        """Grant connection permission to a specific user"""
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
                raise ValueError(f"Connection '{connection_name}' not found")
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
                raise ValueError(f"User '{username}' not found")
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
                raise ValueError(
                    f"User '{username}' already has permission for connection '{connection_name}'"
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
            print(f"Error granting connection permission: {e}")
            raise

    def revoke_connection_permission_from_user(self, username: str, connection_name: str) -> bool:
        """Revoke connection permission from a specific user"""
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
                raise ValueError(f"Connection '{connection_name}' not found")
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
                raise ValueError(f"User '{username}' not found")
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
                raise ValueError(
                    f"User '{username}' has no permission for connection '{connection_name}'"
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
            print(f"Error revoking connection permission: {e}")
            raise

    def modify_connection_group_parent(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None, new_parent_name: Optional[str] = None
    ) -> bool:
        """Set parent connection group for a connection group with cycle detection"""
        try:
            # Use resolver to get group_id and validate inputs
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
                    raise ValueError(
                        f"Parent connection group '{new_parent_name}' not found"
                    )
                new_parent_id = result[0]

                # Check for cycles using helper method
                if self._check_connection_group_cycle(resolved_group_id, new_parent_id):
                    raise ValueError(
                        f"Setting parent would create a cycle in connection groups"
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
                raise ValueError(f"Failed to update parent group for '{group_name}'")

            return True

        except mysql.connector.Error as e:
            print(f"Error modifying connection group parent: {e}")
            raise

    def list_connection_groups(self) -> Dict[str, Dict[str, Union[int, List[str]]]]:
        """List all connection groups with their connections and parent groups"""
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
            print(f"Error listing groups: {e}")
            raise

    def get_connection_group_by_id(self, group_id: int) -> Optional[Dict[str, Dict[str, Union[int, List[str]]]]]:
        """Get a specific connection group by its ID"""
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
            print(f"Error getting connection group by ID: {e}")
            raise

    def get_connection_name_by_id(self, connection_id: int) -> Optional[str]:
        """Get connection name by ID"""
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
            print(f"Error getting connection name by ID: {e}")
            raise

    def get_connection_group_name_by_id(self, group_id: int) -> Optional[str]:
        """Get connection group name by ID"""
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
            print(f"Error getting connection group name by ID: {e}")
            raise

    def validate_positive_id(self, id_value: Optional[int], entity_type: str = "entity") -> Optional[int]:
        """Validate that ID is a positive integer"""
        if id_value is not None and id_value <= 0:
            raise ValueError(
                f"{entity_type} ID must be a positive integer greater than 0"
            )
        return id_value

    def resolve_connection_id(self, connection_name: Optional[str] = None, connection_id: Optional[int] = None) -> int:
        """Validate inputs and resolve to connection_id with centralized validation"""
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
                self.cursor.execute(
                    """
                    SELECT connection_id FROM guacamole_connection
                    WHERE connection_id = %s
                """,
                    (connection_id,),
                )
                result = self.cursor.fetchone()
                if not result:
                    raise ValueError(f"Connection with ID {connection_id} not found")
                return connection_id
            except mysql.connector.Error as e:
                raise ValueError(f"Database error while resolving connection ID: {e}")

        # If name provided, resolve to ID
        if connection_name is not None:
            try:
                self.cursor.execute(
                    """
                    SELECT connection_id FROM guacamole_connection
                    WHERE connection_name = %s
                """,
                    (connection_name,),
                )
                result = self.cursor.fetchone()
                if not result:
                    raise ValueError(f"Connection '{connection_name}' doesn't exist")
                return result[0]
            except mysql.connector.Error as e:
                raise ValueError(f"Database error while resolving connection name: {e}")

    def resolve_conngroup_id(self, group_name: Optional[str] = None, group_id: Optional[int] = None) -> int:
        """Validate inputs and resolve to connection_group_id with centralized validation"""
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
                self.cursor.execute(
                    """
                    SELECT connection_group_id FROM guacamole_connection_group
                    WHERE connection_group_id = %s
                """,
                    (group_id,),
                )
                result = self.cursor.fetchone()
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
                self.cursor.execute(
                    """
                    SELECT connection_group_id FROM guacamole_connection_group
                    WHERE connection_group_name = %s
                """,
                    (group_name,),
                )
                result = self.cursor.fetchone()
                if not result:
                    raise ValueError(f"Connection group '{group_name}' not found")
                return result[0]
            except mysql.connector.Error as e:
                raise ValueError(
                    f"Database error while resolving connection group name: {e}"
                )

    def resolve_usergroup_id(self, group_name: Optional[str] = None, group_id: Optional[int] = None) -> int:
        """Validate inputs and resolve to user_group_id with centralized validation"""
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

    def usergroup_exists_by_id(self, group_id: int) -> bool:
        """Check if a usergroup exists by ID"""
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

    def get_usergroup_name_by_id(self, group_id: int) -> str:
        """Get usergroup name by ID"""
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

    def list_groups_with_users(self):
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

    def debug_connection_permissions(self, connection_name):
        """Debug function to check permissions for a connection"""
        try:
            print(f"\n[DEBUG] Checking permissions for connection '{connection_name}'")

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
                print(f"[DEBUG] Connection '{connection_name}' not found")
                return
            connection_id = result[0]
            print(f"[DEBUG] Connection ID: {connection_id}")

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
                print(
                    f"[DEBUG] No permissions found for connection '{connection_name}'"
                )
            else:
                print(f"[DEBUG] Found {len(permissions)} permissions:")
                for perm in permissions:
                    entity_id, name, entity_type, permission = perm
                    print(
                        f"[DEBUG]   Entity ID: {entity_id}, Name: {name}, Type: {entity_type}, Permission: {permission}"
                    )

            # Specifically check user permissions
            self.cursor.execute(
                """
                SELECT e.name
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s AND e.type = 'USER'
            """,
                (connection_id,),
            )

            user_permissions = self.cursor.fetchall()
            if not user_permissions:
                print(
                    f"[DEBUG] No user permissions found for connection '{connection_name}'"
                )
            else:
                print(f"[DEBUG] Found {len(user_permissions)} user permissions:")
                for perm in user_permissions:
                    print(f"[DEBUG]   User: {perm[0]}")

            print("[DEBUG] End of debug info")

        except mysql.connector.Error as e:
            print(f"[DEBUG] Error debugging permissions: {e}")

    def grant_connection_group_permission_to_user(self, username: str, conngroup_name: str) -> bool:
        """Grant connection group permission to a specific user"""
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not conngroup_name or not isinstance(conngroup_name, str):
            raise ValueError("Connection group name must be a non-empty string")

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
                raise ValueError(f"Connection group '{conngroup_name}' not found")
            connection_group_id, actual_conngroup_name = result

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id, name FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
                LIMIT 1
            """,
                (username,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"User lookup failed for: {username}")
                raise ValueError(f"User '{username}' not found")
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
                    raise ValueError(
                        f"User '{actual_username}' already has permission for connection group '{actual_conngroup_name}'"
                    )
                else:
                    self.debug_print(
                        f"Updating existing permission '{permission_type}' to 'READ' for user '{actual_username}'"
                    )

            # Grant permission (INSERT or UPDATE if unexpected permission exists)
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
            error_msg = f"Database error granting connection group permission for user '{username}' on group '{conngroup_name}': {e}"
            self.debug_print(error_msg)
            raise ValueError(error_msg) from e

    def revoke_connection_group_permission_from_user(self, username: str, conngroup_name: str) -> bool:
        """Revoke connection group permission from a specific user"""
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not conngroup_name or not isinstance(conngroup_name, str):
            raise ValueError("Connection group name must be a non-empty string")

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
                raise ValueError(f"Connection group '{conngroup_name}' not found")
            connection_group_id, actual_conngroup_name = result

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id, name FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
                LIMIT 1
            """,
                (username,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"User lookup failed for: {username}")
                raise ValueError(f"User '{username}' not found")
            entity_id, actual_username = result

            # Check if permission exists and get its type
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
                raise ValueError(
                    f"User '{actual_username}' has no permission for connection group '{actual_conngroup_name}'"
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

            # Verify deletion was successful
            if self.cursor.rowcount == 0:
                raise ValueError(
                    f"Failed to revoke permission - no rows affected. Permission may have been removed by another operation."
                )

            self.debug_print(
                f"Successfully revoked '{permission_type}' permission from user '{actual_username}' for connection group '{actual_conngroup_name}'"
            )
            return True
        except mysql.connector.Error as e:
            error_msg = f"Database error revoking connection group permission for user '{username}' on group '{conngroup_name}': {e}"
            self.debug_print(error_msg)
            raise ValueError(error_msg) from e

    def _atomic_permission_operation(self, operation_func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute a database operation with proper error handling and validation"""
        try:
            return operation_func(*args, **kwargs)
        except mysql.connector.Error as e:
            error_msg = f"Database error during permission operation: {e}"
            self.debug_print(error_msg)
            raise ValueError(error_msg) from e

    def grant_connection_group_permission_to_user_by_id(self, username: str, conngroup_id: int) -> bool:
        """Grant connection group permission to a specific user by connection group ID"""
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if (
            conngroup_id is None
            or not isinstance(conngroup_id, int)
            or conngroup_id <= 0
        ):
            raise ValueError("Connection group ID must be a positive integer")

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
                raise ValueError(f"Connection group ID '{conngroup_id}' not found")
            actual_conngroup_id, conngroup_name = result

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id, name FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
                LIMIT 1
            """,
                (username,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"User lookup failed for: {username}")
                raise ValueError(f"User '{username}' not found")
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
                    raise ValueError(
                        f"User '{actual_username}' already has permission for connection group ID '{actual_conngroup_id}'"
                    )
                else:
                    self.debug_print(
                        f"Updating existing permission '{permission_type}' to 'READ' for user '{actual_username}'"
                    )

            # Grant permission (INSERT or UPDATE if unexpected permission exists)
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
            error_msg = f"Database error granting connection group permission for user '{username}' on group ID '{conngroup_id}': {e}"
            self.debug_print(error_msg)
            raise ValueError(error_msg) from e

    def revoke_connection_group_permission_from_user_by_id(
        self, username: str, conngroup_id: int
    ) -> bool:
        """Revoke connection group permission from a specific user by connection group ID"""
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if (
            conngroup_id is None
            or not isinstance(conngroup_id, int)
            or conngroup_id <= 0
        ):
            raise ValueError("Connection group ID must be a positive integer")

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
                raise ValueError(f"Connection group ID '{conngroup_id}' not found")
            actual_conngroup_id, conngroup_name = result

            # Get user entity ID
            self.cursor.execute(
                """
                SELECT entity_id, name FROM guacamole_entity
                WHERE name = %s AND type = 'USER'
                LIMIT 1
            """,
                (username,),
            )
            result = self.cursor.fetchone()
            if not result:
                self.debug_print(f"User lookup failed for: {username}")
                raise ValueError(f"User '{username}' not found")
            entity_id, actual_username = result

            # Check if permission exists and get its type
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
                raise ValueError(
                    f"User '{actual_username}' has no permission for connection group ID '{actual_conngroup_id}'"
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

            # Verify deletion was successful
            if self.cursor.rowcount == 0:
                raise ValueError(
                    f"Failed to revoke permission - no rows affected. Permission may have been removed by another operation."
                )

            self.debug_print(
                f"Successfully revoked '{permission_type}' permission from user '{actual_username}' for connection group ID '{actual_conngroup_id}'"
            )
            return True
        except mysql.connector.Error as e:
            error_msg = f"Database error revoking connection group permission for user '{username}' on group ID '{conngroup_id}': {e}"
            self.debug_print(error_msg)
            raise ValueError(error_msg) from e
