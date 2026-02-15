#!/usr/bin/env python3
"""Base repository class for Guacamole database operations."""

import mysql.connector
import configparser
import sys
import os
from typing import Optional, Dict, Any

# SSH tunnel support
try:
    from sshtunnel import SSHTunnelForwarder

    SSH_TUNNEL_AVAILABLE = True
except ImportError:
    SSH_TUNNEL_AVAILABLE = False
    SSHTunnelForwarder = None


class BaseGuacamoleRepository:
    """Base class for all Guacamole repositories.

    Provides common database connection and utility methods.
    """

    def __init__(
        self,
        config_file="db_config.ini",
        debug=False,
        conn=None,
        cursor=None,
        ssh_tunnel=None,
    ):
        """Initialize repository with database configuration.

        Args:
            config_file: Path to the configuration file
            debug: Enable debug output
            conn: External database connection (optional, for shared connection)
            cursor: External database cursor (optional, for shared cursor)
            ssh_tunnel: External SSH tunnel object (optional, for shared tunnel)
        """
        self.debug = debug
        self._external_conn = conn is not None
        self._external_tunnel = ssh_tunnel is not None

        if conn is not None and cursor is not None:
            # Use external connection and cursor
            self.conn = conn
            self.cursor = cursor
            self.db_config = None
            self.ssh_tunnel = ssh_tunnel
        else:
            # Create our own connection
            self.db_config = self.read_config(config_file)
            self.ssh_tunnel_config = self.read_ssh_tunnel_config(config_file)
            self.ssh_tunnel = None
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
            # Close SSH tunnel if we own it
            if not self._external_tunnel and self.ssh_tunnel:
                try:
                    self.ssh_tunnel.stop()
                except Exception:
                    pass

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

    @staticmethod
    def read_ssh_tunnel_config(config_file: str) -> Optional[Dict[str, Any]]:
        """Read SSH tunnel configuration from file or environment variables.

        Environment variables have priority over config file.

        Args:
            config_file: Path to the configuration file

        Returns:
            dict or None: SSH tunnel configuration dictionary, or None if not enabled
        """
        # Check environment variables first
        enabled_env = os.environ.get("GUACALIB_SSH_TUNNEL_ENABLED", "").lower()
        if enabled_env in ("true", "1", "yes"):
            # Read all SSH config from environment
            ssh_config = {
                "enabled": True,
                "host": os.environ.get("GUACALIB_SSH_TUNNEL_HOST"),
                "port": int(os.environ.get("GUACALIB_SSH_TUNNEL_PORT", "22")),
                "user": os.environ.get("GUACALIB_SSH_TUNNEL_USER"),
                "password": os.environ.get("GUACALIB_SSH_TUNNEL_PASSWORD"),
                "private_key": os.environ.get("GUACALIB_SSH_TUNNEL_PRIVATE_KEY"),
                "private_key_passphrase": os.environ.get(
                    "GUACALIB_SSH_TUNNEL_PRIVATE_KEY_PASSPHRASE"
                ),
            }

            # Validate required fields
            if not ssh_config["host"]:
                print(
                    "Error: GUACALIB_SSH_TUNNEL_HOST is required when SSH tunnel is enabled"
                )
                sys.exit(1)
            if not ssh_config["user"]:
                print(
                    "Error: GUACALIB_SSH_TUNNEL_USER is required when SSH tunnel is enabled"
                )
                sys.exit(1)

            return ssh_config

        # Read from config file
        if not os.path.exists(config_file):
            return None

        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if "ssh_tunnel" not in config:
                return None

            ssh_section = config["ssh_tunnel"]
            enabled = ssh_section.get("enabled", "false").lower()

            if enabled not in ("true", "1", "yes"):
                return None

            if not SSH_TUNNEL_AVAILABLE:
                print("Error: sshtunnel package is required for SSH tunnel support")
                print("Install it with: pip install sshtunnel")
                sys.exit(1)

            ssh_config = {
                "enabled": True,
                "host": ssh_section.get("host") or ssh_section.get("ssh_tunnel_host"),
                "port": int(
                    ssh_section.get("port", ssh_section.get("ssh_tunnel_port", "22"))
                ),
                "user": ssh_section.get("user") or ssh_section.get("ssh_tunnel_user"),
                "password": ssh_section.get("password")
                or ssh_section.get("ssh_tunnel_password"),
                "private_key": ssh_section.get("private_key")
                or ssh_section.get("ssh_tunnel_private_key"),
                "private_key_passphrase": ssh_section.get("private_key_passphrase")
                or ssh_section.get("ssh_tunnel_private_key_passphrase"),
            }

            # Validate required fields
            if not ssh_config["host"]:
                print("Error: SSH tunnel host is required when SSH tunnel is enabled")
                sys.exit(1)
            if not ssh_config["user"]:
                print("Error: SSH tunnel user is required when SSH tunnel is enabled")
                sys.exit(1)
            if not ssh_config["password"] and not ssh_config["private_key"]:
                print("Error: Either SSH tunnel password or private_key is required")
                sys.exit(1)

            return ssh_config

        except Exception as e:
            print(f"Error reading SSH tunnel config: {str(e)}")
            sys.exit(1)

    def connect_db(self):
        """Establish database connection.

        Creates SSH tunnel if configured, then connects to MySQL.

        Returns:
            mysql.connector.connection: Database connection object
        """
        db_config = self.db_config.copy()

        # Setup SSH tunnel if configured
        if hasattr(self, "ssh_tunnel_config") and self.ssh_tunnel_config:
            if self.ssh_tunnel_config.get("enabled"):
                if not SSH_TUNNEL_AVAILABLE:
                    print("Error: sshtunnel package is required for SSH tunnel support")
                    print("Install it with: pip install sshtunnel")
                    sys.exit(1)

                # Build SSH tunnel configuration
                tunnel_config = {
                    "ssh_address_or_host": (
                        self.ssh_tunnel_config["host"],
                        self.ssh_tunnel_config["port"],
                    ),
                    "ssh_username": self.ssh_tunnel_config["user"],
                    "remote_bind_address": (db_config["host"], 3306),
                }

                # Add authentication method
                if self.ssh_tunnel_config.get("private_key"):
                    tunnel_config["ssh_pkey"] = self.ssh_tunnel_config["private_key"]
                    if self.ssh_tunnel_config.get("private_key_passphrase"):
                        tunnel_config["ssh_pkey_password"] = self.ssh_tunnel_config[
                            "private_key_passphrase"
                        ]
                elif self.ssh_tunnel_config.get("password"):
                    tunnel_config["ssh_password"] = self.ssh_tunnel_config["password"]

                try:
                    self.debug_print(
                        f"Creating SSH tunnel to {self.ssh_tunnel_config['host']}"
                    )
                    self.ssh_tunnel = SSHTunnelForwarder(**tunnel_config)
                    self.ssh_tunnel.start()

                    # Update MySQL config to use tunnel
                    db_config["host"] = "127.0.0.1"
                    db_config["port"] = self.ssh_tunnel.local_bind_port

                    self.debug_print(
                        f"SSH tunnel established on port {self.ssh_tunnel.local_bind_port}"
                    )
                except Exception as e:
                    print(f"Error creating SSH tunnel: {e}")
                    sys.exit(1)

        try:
            return mysql.connector.connect(
                **db_config, charset="utf8mb4", collation="utf8mb4_general_ci"
            )
        except mysql.connector.Error as e:
            # Cleanup tunnel on connection failure
            if self.ssh_tunnel:
                try:
                    self.ssh_tunnel.stop()
                except Exception:
                    pass
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
