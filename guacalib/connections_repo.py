"""
Connections Repository Module

This module contains SQL repository functions for connection management operations.
It provides stateless functions that accept a database cursor and parameters,
returning data without any GuacamoleDB class dependencies.

Functions:
    connection_exists: Check if a connection exists in the database
    create_connection: Create a new connection with parameters
    delete_connection: Delete a connection and all associated data
    modify_connection_parameter: Modify a specific connection parameter

All functions are designed to be stateless and accept a cursor as the first parameter.
"""

import mysql.connector
from typing import Union, Optional
from .db_connection_parameters import CONNECTION_PARAMETERS


def connection_exists(cursor, connection_name: Optional[str] = None, connection_id: Optional[int] = None) -> bool:
    """Check if a connection exists in the Guacamole database.

    Args:
        cursor: Database cursor for executing queries
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
        >>> cursor = db.cursor()
        >>> if connection_exists(cursor, connection_name='my-server'):
        ...     print("Connection exists")
    """
    if not connection_name and not connection_id:
        raise ValueError("Either connection_name or connection_id must be provided")
    if connection_name and connection_id:
        raise ValueError("Provide either connection_name or connection_id, not both")

    try:
        if connection_name:
            cursor.execute(
                """
                SELECT COUNT(*) FROM guacamole_connection
                WHERE connection_name = %s
            """,
                (connection_name,),
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) FROM guacamole_connection
                WHERE connection_id = %s
            """,
                (connection_id,),
            )
        return cursor.fetchone()[0] > 0
    except mysql.connector.Error as e:
        raise


def create_connection(
    cursor,
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
        cursor: Database cursor for executing queries
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
        >>> cursor = db.cursor()
        >>> conn_id = create_connection(
        ...     cursor, 'vnc', 'server1', '192.168.1.100', 5901, 'password'
        ... )
        >>> print(f"Created connection with ID: {conn_id}")
    """
    if not all([connection_name, hostname, port]):
        raise ValueError("Missing required connection parameters")

    # Check if connection already exists
    if connection_exists(cursor, connection_name=connection_name):
        raise ValueError(f"Connection '{connection_name}' already exists")

    # Create connection
    cursor.execute(
        """
        INSERT INTO guacamole_connection
        (connection_name, protocol, parent_id)
        VALUES (%s, %s, %s)
    """,
        (connection_name, connection_type, parent_group_id),
    )

    # Get connection_id
    cursor.execute(
        """
        SELECT connection_id FROM guacamole_connection
        WHERE connection_name = %s
    """,
        (connection_name,),
    )
    connection_id = cursor.fetchone()[0]

    # Create connection parameters
    params = [
        ("hostname", hostname),
        ("port", port),
        ("password", vnc_password),
    ]

    for param_name, param_value in params:
        cursor.execute(
            """
            INSERT INTO guacamole_connection_parameter
            (connection_id, parameter_name, parameter_value)
            VALUES (%s, %s, %s)
        """,
            (connection_id, param_name, param_value),
        )

    return connection_id


def delete_connection(cursor, connection_name: Optional[str] = None, connection_id: Optional[int] = None) -> None:
    """Delete a connection and all its associated data.

    Removes a connection completely from the system, including its parameters,
    permissions, and history. This operation cascades through all related
    tables to maintain database integrity.

    Args:
        cursor: Database cursor for executing queries
        connection_name: The connection name to delete. Optional.
        connection_id: The connection ID to delete. Optional.

    Raises:
        ValueError: If the connection doesn't exist or neither/both parameters provided.
        mysql.connector.Error: If database operations fail.

    Note:
        This is a destructive operation that cannot be undone. The connection and
        all their associated parameters and permissions are permanently removed.
        Exactly one of connection_name or connection_id must be provided.

    Example:
        >>> cursor = db.cursor()
        >>> delete_connection(cursor, connection_name='old-server')
    """
    if not connection_name and not connection_id:
        raise ValueError("Either connection_name or connection_id must be provided")
    if connection_name and connection_id:
        raise ValueError("Provide either connection_name or connection_id, not both")

    # Resolve connection_id if only name is provided
    if connection_name:
        if not connection_exists(cursor, connection_name=connection_name):
            raise ValueError(f"Connection '{connection_name}' not found")
        cursor.execute(
            """
            SELECT connection_id FROM guacamole_connection
            WHERE connection_name = %s
        """,
            (connection_name,),
        )
        resolved_connection_id = cursor.fetchone()[0]
    else:
        # For ID-based deletion, verify connection exists
        if not connection_exists(cursor, connection_id=connection_id):
            raise ValueError(f"Connection with ID {connection_id} not found")
        resolved_connection_id = connection_id

    # Delete connection history
    cursor.execute(
        """
        DELETE FROM guacamole_connection_history
        WHERE connection_id = %s
    """,
        (resolved_connection_id,),
    )

    # Delete connection parameters
    cursor.execute(
        """
        DELETE FROM guacamole_connection_parameter
        WHERE connection_id = %s
    """,
        (resolved_connection_id,),
    )

    # Delete connection permissions
    cursor.execute(
        """
        DELETE FROM guacamole_connection_permission
        WHERE connection_id = %s
    """,
        (resolved_connection_id,),
    )

    # Finally delete the connection
    cursor.execute(
        """
        DELETE FROM guacamole_connection
        WHERE connection_id = %s
    """,
        (resolved_connection_id,),
    )


def modify_connection_parameter(
    cursor,
    connection_name: Optional[str] = None,
    connection_id: Optional[int] = None,
    param_name: Optional[str] = None,
    param_value: Optional[Union[str, int]] = None,
) -> bool:
    """Modify a connection parameter in either guacamole_connection or guacamole_connection_parameter table.

    Args:
        cursor: Database cursor for executing queries
        connection_name: The connection name. Optional.
        connection_id: The connection ID. Optional.
        param_name: The parameter name to modify.
        param_value: The new value for the parameter.

    Returns:
        True if the parameter was successfully updated.

    Raises:
        ValueError: If parameter name is invalid, connection doesn't exist,
                   or parameter update fails.
        mysql.connector.Error: If database operations fail.

    Note:
        Exactly one of connection_name or connection_id must be provided.
        Valid parameters are defined in CONNECTION_PARAMETERS.

    Example:
        >>> cursor = db.cursor()
        >>> modify_connection_parameter(cursor, connection_name='server1',
        ...                             param_name='hostname', param_value='192.168.1.200')
    """
    if not connection_name and not connection_id:
        raise ValueError("Either connection_name or connection_id must be provided")
    if connection_name and connection_id:
        raise ValueError("Provide either connection_name or connection_id, not both")

    # Validate parameter name
    if param_name not in CONNECTION_PARAMETERS:
        raise ValueError(
            f"Invalid parameter: {param_name}. Run 'guacaman conn modify' without arguments to see allowed parameters."
        )

    # Resolve connection_id if only name is provided
    if connection_name:
        if not connection_exists(cursor, connection_name=connection_name):
            raise ValueError(f"Connection '{connection_name}' not found")
        cursor.execute(
            """
            SELECT connection_id FROM guacamole_connection
            WHERE connection_name = %s
        """,
            (connection_name,),
        )
        resolved_connection_id = cursor.fetchone()[0]
    else:
        # For ID-based modification, verify connection exists
        if not connection_exists(cursor, connection_id=connection_id):
            raise ValueError(f"Connection with ID {connection_id} not found")
        resolved_connection_id = connection_id

    param_info = CONNECTION_PARAMETERS[param_name]
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
        cursor.execute(query, (param_value, resolved_connection_id))

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
                cursor.execute(
                    """
                    SELECT parameter_value FROM guacamole_connection_parameter
                    WHERE connection_id = %s AND parameter_name = %s
                """,
                    (resolved_connection_id, param_name),
                )

                if cursor.fetchone():
                    # Update existing parameter
                    cursor.execute(
                        """
                        UPDATE guacamole_connection_parameter
                        SET parameter_value = 'true'
                        WHERE connection_id = %s AND parameter_name = %s
                    """,
                        (resolved_connection_id, param_name),
                    )
                else:
                    # Insert new parameter
                    cursor.execute(
                        """
                        INSERT INTO guacamole_connection_parameter
                        (connection_id, parameter_name, parameter_value)
                        VALUES (%s, %s, 'true')
                    """,
                        (resolved_connection_id, param_name),
                    )
            else:  # param_value.lower() == 'false'
                # Remove the parameter if it exists
                cursor.execute(
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
            cursor.execute(
                """
                SELECT parameter_value FROM guacamole_connection_parameter
                WHERE connection_id = %s AND parameter_name = %s
            """,
                (resolved_connection_id, param_name),
            )

            if cursor.fetchone():
                # Update existing parameter
                cursor.execute(
                    """
                    UPDATE guacamole_connection_parameter
                    SET parameter_value = %s
                    WHERE connection_id = %s AND parameter_name = %s
                """,
                    (param_value, resolved_connection_id, param_name),
                )
            else:
                # Insert new parameter
                cursor.execute(
                    """
                    INSERT INTO guacamole_connection_parameter
                    (connection_id, parameter_name, parameter_value)
                    VALUES (%s, %s, %s)
                """,
                    (resolved_connection_id, param_name, param_value),
                )

    if cursor.rowcount == 0:
        raise ValueError(f"Failed to update connection parameter: {param_name}")

    return True