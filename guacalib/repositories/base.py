#!/usr/bin/env python3
"""Base repository class for Guacamole database operations."""

import configparser
import mysql.connector
import os
from typing import Optional, Dict, Any

from ..exceptions import DatabaseError, EntityNotFoundError, ValidationError

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
        config_file="~/.guacaman.ini",
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

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Config file not found. Please create a config file at {config_file} "
                "with the following format:\n"
                "[mysql]\n"
                "host = your_mysql_host\n"
                "user = your_mysql_user\n"
                "password = your_mysql_password\n"
                "database = your_mysql_database"
            )

        try:
            config.read(config_file)
            if "mysql" not in config:
                raise ValueError("Missing [mysql] section in config file")

            required_keys = ["host", "user", "password", "database"]
            missing_keys = [key for key in required_keys if key not in config["mysql"]]
            if missing_keys:
                raise ValueError(
                    f"Missing required keys in [mysql] section: {', '.join(missing_keys)}"
                )

            return {
                "host": config["mysql"]["host"],
                "user": config["mysql"]["user"],
                "password": config["mysql"]["password"],
                "database": config["mysql"]["database"],
            }
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            raise ValueError(f"Error reading config file: {str(e)}") from e

    @staticmethod
    def read_ssh_tunnel_config(config_file: str) -> Optional[Dict[str, Any]]:
        """Read SSH tunnel configuration from file or environment variables.

        Environment variables have priority over config file.

        Args:
            config_file: Path to the configuration file

        Returns:
            dict or None: SSH tunnel configuration dictionary, or None if not enabled

        Raises:
            ValueError: If SSH tunnel configuration is invalid
            ImportError: If sshtunnel package is required but not installed
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
                raise ValueError(
                    "GUACALIB_SSH_TUNNEL_HOST is required when SSH tunnel is enabled"
                )
            if not ssh_config["user"]:
                raise ValueError(
                    "GUACALIB_SSH_TUNNEL_USER is required when SSH tunnel is enabled"
                )

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
                raise ImportError(
                    "sshtunnel package is required for SSH tunnel support. "
                    "Install it with: pip install sshtunnel"
                )

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
                raise ValueError(
                    "SSH tunnel host is required when SSH tunnel is enabled"
                )
            if not ssh_config["user"]:
                raise ValueError(
                    "SSH tunnel user is required when SSH tunnel is enabled"
                )
            if not ssh_config["password"] and not ssh_config["private_key"]:
                raise ValueError(
                    "Either SSH tunnel password or private_key is required"
                )

            return ssh_config

        except (ValueError, ImportError):
            raise
        except Exception as e:
            raise ValueError(f"Error reading SSH tunnel config: {str(e)}") from e

    def connect_db(self):
        """Establish database connection.

        Creates SSH tunnel if configured, then connects to MySQL.

        Returns:
            mysql.connector.connection: Database connection object

        Raises:
            ImportError: If sshtunnel package is required but not installed
            RuntimeError: If SSH tunnel creation fails
            mysql.connector.Error: If database connection fails
        """
        db_config = self.db_config.copy()

        # Setup SSH tunnel if configured
        if hasattr(self, "ssh_tunnel_config") and self.ssh_tunnel_config:
            if self.ssh_tunnel_config.get("enabled"):
                if not SSH_TUNNEL_AVAILABLE:
                    raise ImportError(
                        "sshtunnel package is required for SSH tunnel support. "
                        "Install it with: pip install sshtunnel"
                    )

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
                    raise RuntimeError(f"Failed to create SSH tunnel: {e}") from e

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
            raise

    @staticmethod
    def validate_positive_id(id_value, entity_type="entity"):
        """Validate that ID is a positive integer.

        Args:
            id_value: The ID value to validate
            entity_type: Type of entity for error messages

        Returns:
            The validated ID value

        Raises:
            ValidationError: If ID is not positive
        """
        if id_value is not None and id_value <= 0:
            raise ValidationError(
                f"{entity_type} ID must be a positive integer greater than 0",
                field="id",
                value=str(id_value),
            )
        return id_value

    def _resolve_entity_id(
        self,
        entity_name: Optional[str],
        entity_id: Optional[int],
        entity_type: str,
        id_query: str,
        name_query: str,
    ) -> int:
        """Generic method to resolve entity name or ID to a database ID.

        Args:
            entity_name: Entity name (optional)
            entity_id: Entity ID (optional)
            entity_type: Type of entity for error messages (e.g., 'User', 'Connection')
            id_query: SQL query to verify ID exists (should have one %s placeholder)
            name_query: SQL query to get ID by name (should have one %s placeholder)

        Returns:
            int: Resolved entity ID

        Raises:
            ValidationError: If both or neither parameter is provided
            EntityNotFoundError: If entity not found in database
            DatabaseError: If database operation fails
        """
        # Validate exactly one parameter provided
        if (entity_name is None) == (entity_id is None):
            raise ValidationError(
                f"Exactly one of {entity_type.lower()}_name or {entity_type.lower()}_id must be provided"
            )

        # If ID provided, validate and return it
        if entity_id is not None:
            self.validate_positive_id(entity_id, entity_type)

            try:
                self.cursor.execute(id_query, (entity_id,))
                result = self.cursor.fetchone()
                if not result:
                    raise EntityNotFoundError(entity_type, str(entity_id))
                return entity_id
            except mysql.connector.Error as e:
                raise DatabaseError(
                    f"Database error while resolving {entity_type.lower()} ID: {e}"
                ) from e

        # If name provided, resolve to ID
        if entity_name is not None:
            try:
                self.cursor.execute(name_query, (entity_name,))
                result = self.cursor.fetchone()
                if not result:
                    raise EntityNotFoundError(entity_type, entity_name)
                return result[0]
            except mysql.connector.Error as e:
                raise DatabaseError(
                    f"Database error while resolving {entity_type.lower()} name: {e}"
                ) from e

    def _entity_exists(
        self,
        entity_name: Optional[str],
        entity_id: Optional[int],
        entity_type: str,
        id_query: str,
        name_query: str,
    ) -> bool:
        """Generic method to check if an entity exists.

        Args:
            entity_name: Entity name (optional)
            entity_id: Entity ID (optional)
            entity_type: Type of entity for error messages
            id_query: SQL query to verify ID exists
            name_query: SQL query to verify name exists

        Returns:
            bool: True if entity exists, False otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            self._resolve_entity_id(
                entity_name, entity_id, entity_type, id_query, name_query
            )
            return True
        except EntityNotFoundError:
            return False
        except ValidationError:
            return False
        except DatabaseError:
            raise

    def _validate_param_name(
        self, param_name: str, allowed_params: Dict[str, Any]
    ) -> str:
        """Validate parameter name against whitelist.

        Args:
            param_name: Parameter name to validate
            allowed_params: Dictionary of allowed parameter names

        Returns:
            str: Validated parameter name

        Raises:
            ValidationError: If parameter name is not in whitelist
        """
        if param_name not in allowed_params:
            raise ValidationError(
                f"Invalid parameter: {param_name}. "
                f"Run 'guacaman' without arguments to see allowed parameters.",
                field="param_name",
                value=param_name,
            )
        return param_name
