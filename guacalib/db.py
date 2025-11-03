#!/usr/bin/env python3

import mysql.connector
import configparser
import logging
import sys
import hashlib
import os
import binascii
from typing import Optional, Union, Dict, List, Tuple, Any, Type, Callable

from mysql.connector.connection import MySQLConnection

from .db_connection_parameters import CONNECTION_PARAMETERS
from .db_user_parameters import USER_PARAMETERS
from .logging_config import get_logger
from . import db_utils
from . import users_repo
from . import usergroups_repo
from . import connections_repo
from . import conngroups_repo
from . import permissions_repo

# Custom type definitions
ConnectionConfig = Dict[str, str]
ConnectionParameters = Dict[str, Union[str, int, bool]]
UserParameters = Dict[str, Dict[str, Union[str, str, str]]]
UserInfo = Tuple[str, List[str]]
ConnectionInfo = Tuple[int, str, str, str, str, str, str, List[str]]
GroupInfo = Dict[str, Dict[str, Union[int, List[str]]]]
PermissionInfo = Tuple[str, str, str]  # (entity_name, entity_type, permission)


class GuacamoleDB:
    """Database interface for Apache Guacamole management.

    Provides a high-level interface for managing Apache Guacamole database entities
    including users, user groups, connections, connection groups, and permissions.
    This class handles MySQL database connections and provides methods for CRUD
    operations on Guacamole entities.

    Attributes:
        CONNECTION_PARAMETERS: Dictionary defining valid connection parameters by protocol.
        USER_PARAMETERS: Dictionary defining valid user account parameters.

    Example:
        >>> # Using config file
        >>> with GuacamoleDB("~/.guacaman.ini") as db:
        ...     users = db.list_users()
        ...     print(f"Found {len(users)} users")
        >>>
        >>> # Using environment variables
        >>> import os
        >>> os.environ['GUACALIB_HOST'] = 'localhost'
        >>> os.environ['GUACALIB_USER'] = 'guacamole_user'
        >>> os.environ['GUACALIB_PASSWORD'] = 'secret_password'
        >>> os.environ['GUACALIB_DATABASE'] = 'guacamole_db'
        >>> with GuacamoleDB() as db:
        ...     users = db.list_users()
        ...     print(f"Found {len(users)} users")

    Note:
        This class implements the context manager protocol for automatic
        database connection handling and transaction management.

        Database connection can be configured using:
        1. Environment variables (GUACALIB_HOST, GUACALIB_USER, GUACALIB_PASSWORD,
           GUACALIB_DATABASE) - takes precedence
        2. Configuration file with [mysql] section containing host, user, password,
           and database keys
    """

    CONNECTION_PARAMETERS = CONNECTION_PARAMETERS
    USER_PARAMETERS = USER_PARAMETERS

    def __init__(self, config_file: str = "db_config.ini", debug: bool = False) -> None:
        """Initialize GuacamoleDB with configuration and database connection.

        Args:
            config_file: Path to MySQL configuration file. Defaults to "db_config.ini".
            debug: Enable debug output for database operations. Defaults to False.

        Raises:
            SystemExit: If configuration file is not found or invalid and environment
                       variables are not set.
            mysql.connector.Error: If database connection fails.

        Note:
            Configuration is loaded in the following priority order:
            1. Environment variables (GUACALIB_HOST, GUACALIB_USER, GUACALIB_PASSWORD,
               GUACALIB_DATABASE)
            2. Configuration file containing a [mysql] section with host, user,
               password, and database keys.

            Environment variables take precedence over configuration file settings.
        """
        self.debug = debug
        self.logger = get_logger('db')
        self.db_config = self.read_config(config_file)
        self.conn = self.connect_db()
        self.cursor = self.conn.cursor()

    def _scrub_credentials(self, message: str) -> str:
        """Scrub sensitive credentials from log messages.

        This function removes sensitive information like passwords, tokens,
        and other credentials from log messages to prevent accidental exposure
        in logs. It replaces sensitive values with [REDACTED] placeholders.

        Args:
            message: The original message that may contain sensitive credentials.

        Returns:
            The message with sensitive values replaced with [REDACTED].

        Note:
            This function handles common credential patterns but may not catch
            all possible formats. Review log output to ensure no credentials
            are accidentally exposed.

        Example:
            >>> scrubbed = self._scrub_credentials("password=secret123")
            >>> print(scrubbed)
            password=[REDACTED]
        """
        import re

        # Enhanced list of sensitive parameter names to scrub
        sensitive_patterns = [
            # Basic password patterns
            (r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password=[REDACTED]'),
            (r'passwd["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'passwd=[REDACTED]'),
            (r'pwd["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'pwd=[REDACTED]'),

            # Authentication secrets
            (r'salt["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'salt=[REDACTED]'),
            (r'secret["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'secret=[REDACTED]'),
            (r'token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'token=[REDACTED]'),
            (r'api_key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'api_key=[REDACTED]'),
            (r'apikey["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'apikey=[REDACTED]'),
            (r'access_key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'access_key=[REDACTED]'),
            (r'secret_key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'secret_key=[REDACTED]'),

            # Database connection patterns
            (r'database["\']?\s*[:=]\s*["\']?([^"\'\s,}]+@[^\s\'"]+)', 'database=user@[REDACTED]'),
            (r'mysql://[^@]+@', 'mysql://[REDACTED]@'),
            (r'mysql\+://[^@]+@', 'mysql+://[REDACTED]@'),

            # Common authentication field names
            (r'auth["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'auth=[REDACTED]'),
            (r'private_key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'private_key=[REDACTED]'),
            (r'credential["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'credential=[REDACTED]'),
            (r'credentials["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'credentials=[REDACTED]'),
        ]

        scrubbed = message
        for pattern, replacement in sensitive_patterns:
            scrubbed = re.sub(pattern, replacement, scrubbed, flags=re.IGNORECASE)

        return scrubbed

    def debug_print(self, *args: Any, **kwargs: Any) -> None:
        """Print debug messages if debug mode is enabled with credential scrubbing.

        This method provides backward compatibility by using logging when configured
        and falling back to print statements when logging is not available. All
        messages are scrubbed for sensitive credentials before output.

        Args:
            *args: Arguments to pass to print function or logger. All arguments
                  will be converted to strings and scrubbed for credentials.
            **kwargs: Keyword arguments to pass to print function or logger.

        Note:
            This method automatically scrubs all arguments for sensitive
            credentials before output to prevent accidental exposure in logs
            or debug output. It maintains the original debug functionality
            while enhancing security.

        Example:
            >>> self.debug_print("Connecting with password=secret123")
            [DEBUG] Connecting with password=[REDACTED]
        """
        if self.debug:
            # Convert all arguments to strings and scrub credentials
            scrubbed_args = []
            for arg in args:
                if isinstance(arg, str):
                    scrubbed_args.append(self._scrub_credentials(arg))
                else:
                    # For non-string arguments, convert to string then scrub
                    scrubbed_args.append(self._scrub_credentials(str(arg)))

            # Try to use logging if it's configured, otherwise fall back to print
            # Check if logging has been configured by checking if the logger has handlers
            if hasattr(self.logger, 'handlers') and self.logger.handlers:
                self.logger.debug(" ".join(scrubbed_args), **kwargs)
            else:
                # Fallback to original print behavior
                print("[DEBUG]", *scrubbed_args, **kwargs)

    def __enter__(self) -> "GuacamoleDB":
        """Enter the runtime context for the database connection.

        Returns:
            The GuacamoleDB instance for use in the with statement.
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        """Exit the runtime context and handle database connection cleanup.

        Commits transactions if no exception occurred, rolls back if there was
        an exception, and closes database connections.

        Args:
            exc_type: Exception type if an exception occurred, None otherwise.
            exc_value: Exception value if an exception occurred, None otherwise.
            traceback: Exception traceback if an exception occurred, None otherwise.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            try:
                # Always commit unless there was an exception
                if exc_type is None:
                    self.conn.commit()
                    self.debug_print("Transaction committed successfully")
                elif exc_type is SystemExit:
                    # SystemExit (from sys.exit()) is used for normal CLI termination
                    # Commit the transaction before exiting
                    self.conn.commit()
                    self.debug_print("Transaction committed successfully before SystemExit")
                else:
                    self.conn.rollback()
                    self.logger.warning(f"Transaction rolled back due to {exc_type.__name__}")
            finally:
                if self.debug:
                    self.debug_print("Closing database connection")
                self.conn.close()

    @staticmethod
    def read_config(config_file: str) -> ConnectionConfig:
        """Read and validate MySQL database configuration from environment variables or file.

        First checks for environment variables (GUACALIB_HOST, GUACALIB_USER,
        GUACALIB_PASSWORD, GUACALIB_DATABASE). If all required environment variables
        are present, they are used. Otherwise, falls back to reading from configuration
        file.

        Args:
            config_file: Path to the configuration file.

        Returns:
            Dictionary containing MySQL connection parameters with keys:
            'host', 'user', 'password', 'database'.

        Raises:
            SystemExit: If config file is not found, missing required sections,
                       contains invalid configuration, or environment variables
                       are incomplete.

        Example:
            >>> # Using environment variables
            >>> os.environ['GUACALIB_HOST'] = 'localhost'
            >>> os.environ['GUACALIB_USER'] = 'guacamole_user'
            >>> os.environ['GUACALIB_PASSWORD'] = 'secret_password'
            >>> os.environ['GUACALIB_DATABASE'] = 'guacamole_db'
            >>> config = GuacamoleDB.read_config("~/.guacaman.ini")
            >>> print(config['host'])
            'localhost'

            >>> # Using config file
            >>> config = GuacamoleDB.read_config("~/.guacaman.ini")
            >>> print(config['host'])
            'localhost'

        Note:
            Environment variables take precedence over configuration file settings.

            Environment variables:
            - GUACALIB_HOST: MySQL server hostname
            - GUACALIB_USER: MySQL username
            - GUACALIB_PASSWORD: MySQL password
            - GUACALIB_DATABASE: MySQL database name

            Configuration file format:
            [mysql]
            host = localhost
            user = guacamole_user
            password = secret_password
            database = guacamole_db
        """
        # First try to get configuration from environment variables
        env_vars = {
            "host": os.environ.get("GUACALIB_HOST"),
            "user": os.environ.get("GUACALIB_USER"),
            "password": os.environ.get("GUACALIB_PASSWORD"),
            "database": os.environ.get("GUACALIB_DATABASE"),
        }

        # Check if all required environment variables are present
        if all(env_vars.values()):
            return env_vars

        # If environment variables are not complete, fall back to config file
        config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            logger = logging.getLogger('guacalib.db')
            logger.error(f"Config file not found: {config_file}")
            print("Error: Config file not found. Please set environment variables or create a config file at ~/.guacaman.ini")
            print("\nOption 1: Set environment variables:")
            print("export GUACALIB_HOST=your_mysql_host")
            print("export GUACALIB_USER=your_mysql_user")
            print("export GUACALIB_PASSWORD=your_mysql_password")
            print("export GUACALIB_DATABASE=your_mysql_database")
            print("\nOption 2: Create a config file with the following format:")
            print("[mysql]")
            print("host = your_mysql_host")
            print("user = your_mysql_user")
            print("password = your_mysql_password")
            print("database = your_mysql_database")
            sys.exit(1)

        try:
            config.read(config_file)
            if "mysql" not in config:
                logger = logging.getLogger('guacalib.db')
                logger.error(f"Missing [mysql] section in config file: {config_file}")
                print(f"Error: Missing [mysql] section in config file: {config_file}")
                sys.exit(1)

            required_keys = ["host", "user", "password", "database"]
            missing_keys = [key for key in required_keys if key not in config["mysql"]]
            if missing_keys:
                logger = logging.getLogger('guacalib.db')
                logger.error(f"Missing required keys in [mysql] section: {', '.join(missing_keys)} in config file: {config_file}")
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
            logger = logging.getLogger('guacalib.db')
            # Simple credential scrubbing for static method
            scrubbed_error = str(e).replace('password=', 'password=[REDACTED]')
            logger.error(f"Error reading config file {config_file}: {scrubbed_error}")
            print(f"Error reading config file {config_file}: {str(e)}")
            sys.exit(1)

    def connect_db(self) -> MySQLConnection:
        """Establish MySQL database connection using loaded configuration.

        Creates a MySQL connection using the configuration loaded by read_config().
        Sets UTF8MB4 charset and collation for proper Unicode support.

        Returns:
            MySQLConnection object for database operations.

        Raises:
            SystemExit: If database connection fails.
            mysql.connector.Error: For various MySQL connection errors.

        Note:
            Uses UTF8MB4 charset to support full Unicode including emoji and
            special characters. Connection parameters are loaded from the
            configuration file during initialization.
        """
        try:
            conn = mysql.connector.connect(
                **self.db_config, charset="utf8mb4", collation="utf8mb4_general_ci"
            )
            self.logger.info(f"Database connection established to {self.db_config.get('host', 'unknown')}")
            return conn
        except mysql.connector.Error as e:
            self.logger.error(f"Database connection failed: {self._scrub_credentials(str(e))}")
            sys.exit(1)

    def list_users(self) -> List[str]:
        """Retrieve all users from the Guacamole database.

        Queries the guacamole_entity table to find all entities of type 'USER'
        and returns them as an alphabetically sorted list.

        Returns:
            List of usernames sorted alphabetically.

        Raises:
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     users = db.list_users()
            ...     print(f"Found users: {', '.join(users)}")
        """
        try:
            return users_repo.list_users(self.cursor)
        except mysql.connector.Error as e:
            self.logger.error(f"Failed to list users: {self._scrub_credentials(str(e))}")
            raise

    def list_usergroups(self) -> List[str]:
        """Retrieve all user groups from the Guacamole database.

        Queries the guacamole_entity table to find all entities of type 'USER_GROUP'
        and returns them as an alphabetically sorted list.

        Returns:
            List of user group names sorted alphabetically.

        Raises:
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     groups = db.list_usergroups()
            ...     print(f"Found groups: {', '.join(groups)}")
        """
        try:
            return usergroups_repo.list_usergroups(self.cursor)
        except mysql.connector.Error as e:
            self.logger.error(f"Failed to list usergroups: {self._scrub_credentials(str(e))}")
            raise

    def usergroup_exists(self, group_name: str) -> bool:
        """Check if a user group exists in the Guacamole database.

        Queries the guacamole_entity table to determine if a user group with the
        specified name exists.

        Args:
            group_name: The user group name to check for existence.

        Returns:
            True if the user group exists, False otherwise.

        Raises:
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     if db.usergroup_exists('admins'):
            ...         print("Admin group exists")
        """
        try:
            return usergroups_repo.usergroup_exists(self.cursor, group_name)
        except mysql.connector.Error as e:
            self.logger.error(f"Error checking usergroup existence: {self._scrub_credentials(str(e))}")
            raise

    def get_usergroup_id(self, group_name: str) -> int:
        """Get the database ID for a user group by name.

        Queries the guacamole_user_group and guacamole_entity tables to find
        the internal database ID for a user group.

        Args:
            group_name: The name of the user group.

        Returns:
            The user group ID from the database.

        Raises:
            ValueError: If the user group is not found.
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     group_id = db.get_usergroup_id('admins')
            ...     print(f"Admin group ID: {group_id}")
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
            self.logger.error(f"Error getting usergroup ID: {self._scrub_credentials(str(e))}")
            raise

    def user_exists(self, username: str) -> bool:
        """Check if a user exists in the Guacamole database.

        Queries the guacamole_entity table to determine if a user with the
        specified username exists.

        Args:
            username: The username to check for existence.

        Returns:
            True if the user exists, False otherwise.

        Raises:
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     if db.user_exists('admin'):
            ...         print("Admin user exists")
        """
        try:
            return users_repo.user_exists(self.cursor, username)
        except mysql.connector.Error as e:
            self.logger.error(f"Error checking user existence: {self._scrub_credentials(str(e))}")
            raise

  
    def get_connection_group_id_by_name(self, group_name: str) -> Optional[int]:
        """Get connection group ID by name from the database.

        Retrieves the database ID for a connection group given its name.
        Returns None for empty group names to handle root-level assignments.

        Args:
            group_name: Name of the connection group to look up.

        Returns:
            The database ID of the connection group, or None if group_name is empty.

        Raises:
            ValueError: If the connection group with the specified name is not found.
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     group_id = db.get_connection_group_id_by_name("Production Servers")
            ...     print(f"Group ID: {group_id}")
            Group ID: 42
        """
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
            self.logger.error(f"Error getting connection group ID: {self._scrub_credentials(str(e))}")
            raise

    def modify_connection_parent_group(
        self,
        connection_name: Optional[str] = None,
        connection_id: Optional[int] = None,
        group_name: Optional[str] = None,
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
            self.logger.error(f"Error modifying connection parent group: {self._scrub_credentials(str(e))}")
            raise

    def get_connection_user_permissions(self, connection_name: str) -> List[str]:
        """Get list of users with direct permissions to a connection"""
        try:
            return permissions_repo.get_connection_user_permissions(self.cursor, connection_name)
        except mysql.connector.Error as e:
            self.logger.error(f"Error getting connection user permissions: {self._scrub_credentials(str(e))}")
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
            return connections_repo.modify_connection_parameter(
                self.cursor, connection_name, connection_id, param_name, param_value
            )
        except mysql.connector.Error as e:
            self.logger.error(f"Error modifying connection parameter: {self._scrub_credentials(str(e))}")
            raise

    def change_user_password(self, username: str, new_password: str) -> bool:
        """Change the password for an existing user.

        Updates a user's password with secure hashing using a new random salt.
        Uses the same hashing method as create_user() for consistency.

        Args:
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
            ...     db.change_user_password('user1', 'newsecurepassword')
        """
        try:
            return users_repo.change_user_password(self.cursor, username, new_password)
        except mysql.connector.Error as e:
            self.logger.error(f"Error changing password: {self._scrub_credentials(str(e))}")
            raise

    def modify_user(
        self, username: str, param_name: str, param_value: Union[str, int]
    ) -> bool:
        """Modify a user parameter in the Guacamole database.

        Updates user account parameters such as disabled status, expiration dates,
        time windows, timezone, and contact information.

        Args:
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
            ...     db.modify_user('user1', 'disabled', '1')
            ...     db.modify_user('user1', 'full_name', 'John Doe')
        """
        try:
            return users_repo.modify_user_parameter(self.cursor, username, param_name, param_value)
        except mysql.connector.Error as e:
            self.logger.error(f"Error modifying user parameter: {self._scrub_credentials(str(e))}")
            raise

    def delete_existing_user(self, username: str) -> None:
        """Delete a user and all associated data from the Guacamole database.

        Removes a user completely from the system, including their entity record,
        user account, group memberships, and all permissions. This operation
        cascades through all related tables to maintain database integrity.

        Args:
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
            ...     db.delete_existing_user('olduser')
        """
        try:
            self.debug_print(f"Deleting user: {username}")
            users_repo.delete_user(self.cursor, username)
        except mysql.connector.Error as e:
            self.logger.error(f"Failed to delete user '{username}': {self._scrub_credentials(str(e))}")
            raise

    def delete_existing_usergroup(self, group_name: str) -> None:
        try:
            self.debug_print(f"Deleting usergroup: {group_name}")
            usergroups_repo.delete_usergroup(self.cursor, group_name)
        except mysql.connector.Error as e:
            self.logger.error(f"Error deleting existing usergroup: {self._scrub_credentials(str(e))}")
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
            self.logger.error(f"Error deleting existing usergroup: {self._scrub_credentials(str(e))}")
            raise
        except ValueError as e:
            self.logger.error(f"Error: {e}")
            print(f"Error: {e}")
            raise

    def delete_existing_connection(
        self, connection_name: Optional[str] = None, connection_id: Optional[int] = None
    ) -> None:
        """Delete a connection and all its associated data"""
        try:
            # Get connection name for logging if we only have ID
            log_name = connection_name
            if connection_name is None and connection_id:
                log_name = self.get_connection_name_by_id(connection_id)

            self.debug_print(
                f"Attempting to delete connection: {log_name} (ID: {connection_id})"
            )

            connections_repo.delete_connection(self.cursor, connection_name, connection_id)

            # Transaction will be committed by context manager
            self.debug_print(f"Successfully deleted connection '{log_name}'")

        except mysql.connector.Error as e:
            self.logger.error(f"Error deleting existing connection: {self._scrub_credentials(str(e))}")
            raise

    def delete_connection_group(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> bool:
        """Delete a connection group and update references to it"""
        try:
            # Get group name for logging if we only have ID
            group_name_display = None
            if group_name is None and group_id is not None:
                group_name_display = self.get_connection_group_name_by_id(group_id)

            self.debug_print(
                f"Attempting to delete connection group: {group_name_display or group_name} (ID: {group_id})"
            )

            result = conngroups_repo.delete_connection_group(self.cursor, group_name, group_id)

            # Transaction will be committed by context manager
            self.debug_print(f"Successfully deleted connection group '{group_name_display or group_name}'")
            return result

        except mysql.connector.Error as e:
            self.logger.error(f"Error deleting connection group: {self._scrub_credentials(str(e))}")
            raise

    def create_user(self, username: str, password: str) -> None:
        """Create a new user in the Guacamole database.

        Creates a new user with secure password hashing using Guacamole's
        authentication method. Generates a random salt and hashes the password
        using SHA256.

        Args:
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
            ...     db.create_user('newuser', 'securepassword')
        """
        try:
            users_repo.create_user(self.cursor, username, password)
            self.logger.info(f"User '{username}' created successfully")
        except mysql.connector.Error as e:
            self.logger.error(f"Failed to create user '{username}': {self._scrub_credentials(str(e))}")
            raise

    def create_usergroup(self, group_name: str) -> None:
        """Create a new user group in the Guacamole database.

        Creates both the entity record and the user group record for a new
        user group with disabled status set to FALSE (enabled).

        Args:
            group_name: The name for the new user group.

        Raises:
            mysql.connector.Error: If database operations fail.

        Example:
            >>> with GuacamoleDB() as db:
            ...     db.create_usergroup('developers')
        """
        try:
            usergroups_repo.create_usergroup(self.cursor, group_name)
        except mysql.connector.Error as e:
            self.logger.error(f"Error creating usergroup: {self._scrub_credentials(str(e))}")
            raise

    def add_user_to_usergroup(self, username: str, group_name: str) -> None:
        try:
            permissions_repo.add_user_to_usergroup(self.cursor, username, group_name)
            self.debug_print(
                f"Successfully added user '{username}' to usergroup '{group_name}'"
            )

        except mysql.connector.Error as e:
            self.logger.error(f"Error adding user to usergroup: {self._scrub_credentials(str(e))}")
            raise

    def remove_user_from_usergroup(self, username: str, group_name: str) -> None:
        try:
            permissions_repo.remove_user_from_usergroup(self.cursor, username, group_name)
            self.debug_print(
                f"Successfully removed user '{username}' from usergroup '{group_name}'"
            )

        except mysql.connector.Error as e:
            self.logger.error(f"Error removing user from group: {self._scrub_credentials(str(e))}")
            raise

    def get_connection_group_id(self, group_path: str) -> int:
        """Resolve nested connection group path to connection group ID.

        Resolves a hierarchical path (e.g., "parent/child/grandchild") to the
        database ID of the final group in the path. This method traverses the
        hierarchy to find the exact group at the specified path.

        Args:
            group_path: Slash-separated path to the connection group.
                       Examples: "Production", "Production/Web", "Servers/Linux"

        Returns:
            The database ID of the connection group at the specified path.

        Raises:
            ValueError: If the group path cannot be resolved or any group in the
                       path doesn't exist.
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     group_id = db.get_connection_group_id("Production/Web Servers")
            ...     print(f"Group ID: {group_id}")
            Group ID: 42
        """
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
            self.logger.error(f"Error resolving group path: {self._scrub_credentials(str(e))}")
            raise

    def connection_exists(
        self, connection_name: Optional[str] = None, connection_id: Optional[int] = None
    ) -> bool:
        """Check if a connection exists in the Guacamole database.

        Uses the resolve_connection_id method to validate inputs and determine
        if a connection with the specified name or ID exists.

        Args:
            connection_name: The connection name to check. Optional.
            connection_id: The connection ID to check. Optional.

        Returns:
            True if the connection exists, False otherwise.

        Raises:
            ValueError: If neither or both parameters are provided.
            mysql.connector.Error: If database query fails.

        Note:
            Exactly one of connection_name or connection_id must be provided.

        Example:
            >>> with GuacamoleDB() as db:
            ...     if db.connection_exists(connection_name='my-server'):
            ...         print("Connection exists")
        """
        try:
            return connections_repo.connection_exists(self.cursor, connection_name, connection_id)
        except mysql.connector.Error as e:
            self.logger.error(f"Error checking connection existence: {self._scrub_credentials(str(e))}")
            raise

    def connection_group_exists(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> bool:
        """Check if a connection group with the given name or ID exists"""
        try:
            return conngroups_repo.connection_group_exists(self.cursor, group_name, group_id)
        except mysql.connector.Error as e:
            self.logger.error(f"Error checking connection group existence: {self._scrub_credentials(str(e))}")
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
        """Create a new connection in the Guacamole database.

        Creates a new connection with basic parameters. Currently designed
        for VNC connections but can be extended for other protocols.

        Args:
            connection_type: The connection protocol (e.g., 'vnc', 'rdp', 'ssh').
            connection_name: The name for the new connection.
            hostname: The hostname or IP address of the target server.
            port: The port number for the connection.
            vnc_password: The password for VNC authentication.
            parent_group_id: Optional parent connection group ID.

        Returns:
            The ID of the newly created connection.

        Raises:
            ValueError: If required parameters are missing or connection already exists.
            mysql.connector.Error: If database operations fail.

        Example:
            >>> with GuacamoleDB() as db:
            ...     conn_id = db.create_connection(
            ...         'vnc', 'server1', '192.168.1.100', 5901, 'password'
            ...     )
            ...     print(f"Created connection with ID: {conn_id}")
        """
        try:
            return connections_repo.create_connection(
                self.cursor, connection_type, connection_name, hostname, port, vnc_password, parent_group_id
            )
        except mysql.connector.Error as e:
            self.logger.error(f"Error creating VNC connection: {self._scrub_credentials(str(e))}")
            raise

    def grant_connection_permission(
        self, entity_name, entity_type, connection_id, group_path=None
    ):
        try:
            if group_path:
                self.debug_print(f"Processing group path: {group_path}")
            permissions_repo.grant_connection_permission(
                self.cursor, entity_name, entity_type, connection_id, group_path
            )
            if group_path:
                parent_group_id = self.get_connection_group_id(group_path)
                self.debug_print(
                    f"Assigning connection {connection_id} to parent group {parent_group_id}"
                )
            self.debug_print(f"Granting permission to {entity_type}:{entity_name}")

        except mysql.connector.Error as e:
            self.logger.error(f"Error granting connection permission: {self._scrub_credentials(str(e))}")
            raise

    def list_users_with_usergroups(self) -> Dict[str, List[str]]:
        """List all users with their associated user group memberships.

        Retrieves a comprehensive mapping of all users in the system and the
        user groups they belong to. This provides a complete view of user
        group memberships for reporting and analysis.

        Returns:
            Dict[str, List[str]]: Mapping of usernames to lists of user group names.
                Users with no group memberships will have an empty list.

        Raises:
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     users = db.list_users_with_usergroups()
            ...     for username, groups in users.items():
            ...         print(f"{username}: {groups}")
            john.doe: ['admin', 'developers']
            jane.smith: ['users']
            guest: []
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
            self.logger.error(f"Error listing connections: {self._scrub_credentials(str(e))}")
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
            self.logger.error(f"Error getting connection by ID: {self._scrub_credentials(str(e))}")
            raise

    def list_usergroups_with_users_and_connections(self):
        """List all user groups with their associated users and connections.

        Retrieves a comprehensive mapping of all user groups in the system,
        including the users belonging to each group and the connections
        accessible to those users through group permissions.

        Returns:
            Dict[str, Dict[str, Any]]: Nested dictionary with group names as keys.
                Each group dictionary contains:
                - id (int): The database ID of the user group
                - users (List[str]): List of usernames belonging to the group
                - connections (List[str]): List of connection names accessible to the group

        Raises:
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     result = db.list_usergroups_with_users_and_connections()
            ...     admin_group = result.get('admin', {})
            ...     print(f"Admin users: {admin_group.get('users', [])}")
            ...     print(f"Admin connections: {admin_group.get('connections', [])}")
            Admin users: ['admin1', 'admin2']
            Admin connections: ['server1', 'server2']
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
            self.logger.error(f"Error listing groups with users and connections: {self._scrub_credentials(str(e))}")
            raise

    def _check_connection_group_cycle(self, group_id: int, parent_id: Optional[int]) -> bool:
        """Check if setting a parent connection group would create a cycle.

        Validates whether assigning a parent group to a connection group would
        result in a circular reference in the connection group hierarchy.
        This prevents infinite loops and maintains a proper tree structure.

        Args:
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
            >>> db._check_connection_group_cycle(1, 3)  # Returns True
            >>> db._check_connection_group_cycle(4, None)  # Returns False
        """
        return conngroups_repo.check_connection_group_cycle(self.cursor, group_id, parent_id)

    def create_connection_group(
        self, group_name: str, parent_group_name: Optional[str] = None
    ) -> bool:
        """Create a new connection group in the Guacamole database.

        Creates a new connection group with the specified name and optionally
        assigns it to a parent group to establish a hierarchical structure.

        Args:
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
            >>> with GuacamoleDB() as db:
            ...     # Create root-level group
            ...     db.create_connection_group("Production Servers")
            ...     # Create child group
            ...     db.create_connection_group("Web Servers", "Production Servers")
        """
        try:
            return conngroups_repo.create_connection_group(self.cursor, group_name, parent_group_name)
        except mysql.connector.Error as e:
            self.logger.error(f"Error creating connection group: {self._scrub_credentials(str(e))}")
            raise

    def grant_connection_permission_to_user(
        self, username: str, connection_name: str
    ) -> bool:
        """Grant connection permission to a specific user"""
        try:
            return permissions_repo.grant_connection_permission_to_user(
                self.cursor, username, connection_name
            )

        except mysql.connector.Error as e:
            self.logger.error(f"Error granting connection permission: {self._scrub_credentials(str(e))}")
            raise

    def revoke_connection_permission_from_user(
        self, username: str, connection_name: str
    ) -> bool:
        """Revoke connection permission from a specific user"""
        try:
            return permissions_repo.revoke_connection_permission_from_user(
                self.cursor, username, connection_name
            )

        except mysql.connector.Error as e:
            self.logger.error(f"Error revoking connection permission: {self._scrub_credentials(str(e))}")
            raise

    def modify_connection_group_parent(
        self,
        group_name: Optional[str] = None,
        group_id: Optional[int] = None,
        new_parent_name: Optional[str] = None,
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
            self.logger.error(f"Error modifying connection group parent: {self._scrub_credentials(str(e))}")
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
            self.logger.error(f"Error listing groups: {self._scrub_credentials(str(e))}")
            raise

    def get_connection_group_by_id(
        self, group_id: int
    ) -> Optional[Dict[str, Dict[str, Union[int, List[str]]]]]:
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
            self.logger.error(f"Error getting connection group by ID: {self._scrub_credentials(str(e))}")
            raise

    def get_connection_name_by_id(self, connection_id: int) -> Optional[str]:
        """Get connection name by ID"""
        try:
            return db_utils.get_connection_name_by_id(self.cursor, connection_id)
        except mysql.connector.Error as e:
            self.logger.error(f"Error getting connection name by ID: {self._scrub_credentials(str(e))}")
            raise

    def get_connection_group_name_by_id(self, group_id: int) -> Optional[str]:
        """Get connection group name by ID"""
        try:
            return db_utils.get_connection_group_name_by_id(self.cursor, group_id)
        except mysql.connector.Error as e:
            self.logger.error(f"Error getting connection group name by ID: {self._scrub_credentials(str(e))}")
            raise

    def validate_positive_id(
        self, id_value: Optional[int], entity_type: str = "entity"
    ) -> Optional[int]:
        """Validate that ID is a positive integer"""
        return db_utils.validate_positive_id(id_value, entity_type)

    def resolve_connection_id(
        self, connection_name: Optional[str] = None, connection_id: Optional[int] = None
    ) -> int:
        """Validate inputs and resolve to connection_id with centralized validation.

        This is a core utility method that handles the common pattern of accepting
        either a connection name or ID and resolving it to a validated connection ID.
        Provides comprehensive input validation and error handling.

        Args:
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
            >>> with GuacamoleDB() as db:
            ...     # Resolve by name
            ...     conn_id = db.resolve_connection_id(connection_name='my-server')
            ...     # Resolve by ID (validates existence)
            ...     conn_id = db.resolve_connection_id(connection_id=123)
        """
        return db_utils.resolve_connection_id(self.cursor, connection_name, connection_id)

    def resolve_conngroup_id(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> int:
        """Validate inputs and resolve to connection_group_id with centralized validation"""
        return db_utils.resolve_conngroup_id(self.cursor, group_name, group_id)

    def resolve_usergroup_id(
        self, group_name: Optional[str] = None, group_id: Optional[int] = None
    ) -> int:
        """Validate inputs and resolve to user_group_id with centralized validation"""
        return db_utils.resolve_usergroup_id(self.cursor, group_name, group_id)

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
        """Get user group name by its database ID.

        Retrieves the name of a user group given its database ID.
        This is useful for converting internal IDs back to human-readable names.

        Args:
            group_id: The database ID of the user group.

        Returns:
            The name of the user group.

        Raises:
            ValueError: If user group with the specified ID is not found.
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     name = db.get_usergroup_name_by_id(42)
            ...     print(f"Group name: {name}")
            Group name: admin-group
        """
        return db_utils.get_usergroup_name_by_id(self.cursor, group_id)

    def list_groups_with_users(self) -> Dict[str, List[str]]:
        """List all user groups with their associated users.

        Retrieves a mapping of user group names to the list of usernames
        that belong to each group. This provides a simplified view of
        user group membership.

        Returns:
            Dict[str, List[str]]: Mapping of group names to lists of usernames.
                Groups with no members will have an empty list.

        Raises:
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     groups = db.list_groups_with_users()
            ...     for group_name, users in groups.items():
            ...         print(f"{group_name}: {users}")
            admin: ['admin1', 'admin2']
            users: ['john.doe', 'jane.smith']
            guests: []
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

    def debug_connection_permissions(self, connection_name: str) -> None:
        """Debug function to check and display permissions for a connection.

        Outputs detailed debugging information about all permissions associated
        with a specific connection, including both user and user group permissions.
        This function is intended for troubleshooting connection access issues.

        Args:
            connection_name: The name of the connection to debug.

        Returns:
            None (outputs debug information to stdout).

        Raises:
            mysql.connector.Error: If database query fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     db.debug_connection_permissions("my-server")
            [DEBUG] Checking permissions for connection 'my-server'
            [DEBUG] Connection ID: 42
            [DEBUG] Found 2 permissions:
            [DEBUG]   Entity ID: 15, Name: john.doe, Type: USER, Permission: READ
            [DEBUG]   Entity ID: 20, Name: admin-group, Type: USER_GROUP, Permission: READ
            [DEBUG] Found 1 user permissions:
            [DEBUG]   User: john.doe
            [DEBUG] End of debug info
        """
        try:
            self.logger.debug(f"Checking permissions for connection '{connection_name}'")

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
                self.logger.debug(f"Connection '{connection_name}' not found")
                return
            connection_id = result[0]
            self.logger.debug(f"Connection ID: {connection_id}")

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
                self.logger.debug(
                    f"No permissions found for connection '{connection_name}'"
                )
            else:
                self.logger.debug(f"Found {len(permissions)} permissions:")
                for perm in permissions:
                    entity_id, name, entity_type, permission = perm
                    self.logger.debug(
                        f"  Entity ID: {entity_id}, Name: {name}, Type: {entity_type}, Permission: {permission}"
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
                self.logger.debug(
                    f"No user permissions found for connection '{connection_name}'"
                )
            else:
                self.logger.debug(f"Found {len(user_permissions)} user permissions:")
                for perm in user_permissions:
                    self.logger.debug(f"  User: {perm[0]}")

            self.logger.debug("End of debug info")

        except mysql.connector.Error as e:
            self.logger.debug(f"Error debugging permissions: {self._scrub_credentials(str(e))}")

    def grant_connection_group_permission_to_user(
        self, username: str, conngroup_name: str
    ) -> bool:
        """Grant connection group permission to a specific user.

        Grants READ permission to a user for accessing a connection group.
        This allows the user to see and use all connections within that group.

        Args:
            username: Name of the user to grant permission to.
            conngroup_name: Name of the connection group to grant access to.

        Returns:
            True if the permission was granted successfully.

        Raises:
            ValueError: If username or connection group name is invalid, or if
                       the user or connection group doesn't exist.
            mysql.connector.Error: If database operation fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     success = db.grant_connection_group_permission_to_user(
            ...         "john.doe", "Production Servers"
            ...     )
            ...     print(f"Permission granted: {success}")
            Permission granted: True
        """
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

            # Grant permission
            permissions_repo.grant_connection_group_permission_to_user(
                self.cursor, username, conngroup_name
            )
            self.debug_print(
                f"Granted 'READ' permission to user '{actual_username}' for connection group '{actual_conngroup_name}'"
            )

            return True
        except mysql.connector.Error as e:
            error_msg = f"Database error granting connection group permission for user '{username}' on group '{conngroup_name}': {e}"
            self.logger.error(self._scrub_credentials(error_msg))
            raise ValueError(error_msg) from e

    def revoke_connection_group_permission_from_user(
        self, username: str, conngroup_name: str
    ) -> bool:
        """Revoke connection group permission from a specific user"""
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not conngroup_name or not isinstance(conngroup_name, str):
            raise ValueError("Connection group name must be a non-empty string")

        try:
            return permissions_repo.revoke_connection_group_permission_from_user(
                self.cursor, username, conngroup_name
            )
        except mysql.connector.Error as e:
            error_msg = f"Database error revoking connection group permission for user '{username}' on group '{conngroup_name}': {e}"
            self.logger.error(self._scrub_credentials(error_msg))
            raise ValueError(error_msg) from e

    def _atomic_permission_operation(
        self, operation_func: Callable, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute a database operation with proper error handling and validation"""
        try:
            return operation_func(*args, **kwargs)
        except mysql.connector.Error as e:
            error_msg = f"Database error during permission operation: {e}"
            self.logger.error(self._scrub_credentials(error_msg))
            raise ValueError(error_msg) from e

    def grant_connection_group_permission_to_user_by_id(
        self, username: str, conngroup_id: int
    ) -> bool:
        """Grant connection group permission to a user using connection group ID.

        Grants READ permission to a user for accessing a connection group
        when you have the database ID rather than the name.

        Args:
            username: Name of the user to grant permission to.
            conngroup_id: Database ID of the connection group to grant access to.

        Returns:
            True if the permission was granted successfully.

        Raises:
            ValueError: If username is invalid, conngroup_id is not a positive
                       integer, or if the user or connection group doesn't exist.
            mysql.connector.Error: If database operation fails.

        Example:
            >>> with GuacamoleDB() as db:
            ...     success = db.grant_connection_group_permission_to_user_by_id(
            ...         "john.doe", 42
            ...     )
            ...     print(f"Permission granted: {success}")
            Permission granted: True
        """
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

            # Grant permission
            permissions_repo.grant_connection_group_permission_to_user_by_id(
                self.cursor, username, conngroup_id
            )
            self.debug_print(
                f"Granted 'READ' permission to user '{actual_username}' for connection group ID '{actual_conngroup_id}'"
            )

            return True
        except mysql.connector.Error as e:
            error_msg = f"Database error granting connection group permission for user '{username}' on group ID '{conngroup_id}': {e}"
            self.logger.error(self._scrub_credentials(error_msg))
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
            permissions_repo.revoke_connection_group_permission_from_user_by_id(
                self.cursor, username, conngroup_id
            )
            self.debug_print(
                f"Successfully revoked '{permission_type}' permission from user '{actual_username}' for connection group ID '{actual_conngroup_id}'"
            )
            return True
        except mysql.connector.Error as e:
            error_msg = f"Database error revoking connection group permission for user '{username}' on group ID '{conngroup_id}': {e}"
            self.logger.error(self._scrub_credentials(error_msg))
            raise ValueError(error_msg) from e
