#!/usr/bin/env python3
"""Base repository class for Guacamole database operations."""

import mysql.connector
import configparser
import sys
import os


class BaseGuacamoleRepository:
    """Base class for all Guacamole repositories.

    Provides common database connection and utility methods.
    """

    def __init__(
        self, config_file="db_config.ini", debug=False, conn=None, cursor=None
    ):
        """Initialize repository with database configuration.

        Args:
            config_file: Path to the configuration file
            debug: Enable debug output
            conn: External database connection (optional, for shared connection)
            cursor: External database cursor (optional, for shared cursor)
        """
        self.debug = debug
        self._external_conn = conn is not None

        if conn is not None and cursor is not None:
            # Use external connection and cursor
            self.conn = conn
            self.cursor = cursor
            self.db_config = None
        else:
            # Create our own connection
            self.db_config = self.read_config(config_file)
            self.conn = self.connect_db()
            self.cursor = self.conn.cursor()

    def debug_print(self, *args, **kwargs):
        """Print debug messages if debug mode is enabled."""
        if self.debug:
            print("[DEBUG]", *args, **kwargs)

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit context manager with proper cleanup."""
        # Only cleanup if we own the connection
        if not self._external_conn:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                try:
                    if exc_type is None:
                        self.conn.commit()
                    else:
                        self.conn.rollback()
                finally:
                    self.conn.close()

    @staticmethod
    def read_config(config_file):
        """Read database configuration from file.

        Args:
            config_file: Path to the configuration file

        Returns:
            dict: Database configuration dictionary
        """
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

    def connect_db(self):
        """Establish database connection.

        Returns:
            mysql.connector.connection: Database connection object
        """
        try:
            return mysql.connector.connect(
                **self.db_config, charset="utf8mb4", collation="utf8mb4_general_ci"
            )
        except mysql.connector.Error as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)

    @staticmethod
    def validate_positive_id(id_value, entity_type="entity"):
        """Validate that ID is a positive integer.

        Args:
            id_value: The ID value to validate
            entity_type: Type of entity for error messages

        Returns:
            The validated ID value

        Raises:
            ValueError: If ID is not positive
        """
        if id_value is not None and id_value <= 0:
            raise ValueError(
                f"{entity_type} ID must be a positive integer greater than 0"
            )
        return id_value
