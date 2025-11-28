"""
Cross-domain reporting repository for Guacamole database operations.

This module contains functions for cross-domain reporting and complex
queries that span multiple tables or domains. These functions have
been extracted from the GuacamoleDB facade to improve maintainability
and follow the repository pattern.

All functions in this module accept a database cursor as the first
parameter and are stateless - they don't depend on GuacamoleDB instance
variables, making them easy to test and reuse.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
import mysql.connector


logger = logging.getLogger(__name__)


def debug_connection_permissions(cursor, connection_name: str) -> None:
    """Debug function to check and display permissions for a connection.

    Outputs detailed debugging information about all permissions associated
    with a specific connection, including both user and user group permissions.
    This function is intended for troubleshooting connection access issues.

    Args:
        cursor: Database cursor for executing queries.
        connection_name: The name of the connection to debug.

    Returns:
        None (outputs debug information to logger).

    Raises:
        mysql.connector.Error: If database query fails.
        ValueError: If connection is not found.

    Example:
        >>> cursor = db.cursor()
        >>> debug_connection_permissions(cursor, "my-server")
        # Outputs debug information via logger
    """
    try:
        logger.debug(f"Checking permissions for connection '{connection_name}'")

        # Get connection ID
        cursor.execute(
            """
            SELECT connection_id FROM guacamole_connection
            WHERE connection_name = %s
        """,
            (connection_name,),
        )
        result = cursor.fetchone()
        if not result:
            logger.debug(f"Connection '{connection_name}' not found")
            raise ValueError(f"Connection '{connection_name}' not found")
        connection_id = result[0]
        logger.debug(f"Connection ID: {connection_id}")

        # Check all permissions
        cursor.execute(
            """
            SELECT cp.entity_id, e.name, e.type, cp.permission
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s
        """,
            (connection_id,),
        )

        permissions = cursor.fetchall()
        if not permissions:
            logger.debug(
                f"No permissions found for connection '{connection_name}'"
            )
        else:
            logger.debug(f"Found {len(permissions)} permissions:")
            for perm in permissions:
                entity_id, name, entity_type, permission = perm
                logger.debug(
                    f"  Entity ID: {entity_id}, Name: {name}, Type: {entity_type}, Permission: {permission}"
                )

        # Specifically check user permissions
        cursor.execute(
            """
            SELECT e.name
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s AND e.type = 'USER'
        """,
            (connection_id,),
        )

        user_permissions = cursor.fetchall()
        if not user_permissions:
            logger.debug(
                f"No user permissions found for connection '{connection_name}'"
            )
        else:
            logger.debug(f"Found {len(user_permissions)} user permissions:")
            for perm in user_permissions:
                logger.debug(f"  User: {perm[0]}")

        logger.debug("End of debug info")

    except mysql.connector.Error as e:
        logger.debug(f"Error debugging permissions: {e}")
        raise


def list_groups_with_users(cursor) -> Dict[str, List[str]]:
    """List all user groups with their associated users.

    Retrieves a mapping of user group names to the list of usernames
    that belong to each group. This provides a simplified view of
    user group membership.

    Args:
        cursor: Database cursor for executing queries.

    Returns:
        Dictionary mapping group names to lists of usernames.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> groups = list_groups_with_users(cursor)
        >>> print(groups)
        {'admin-group': ['admin', 'manager'], 'users': ['john', 'jane']}
    """
    try:
        cursor.execute(
            """
            SELECT
                ug.name as group_name,
                u.username
            FROM guacamole_user_group ug
            LEFT JOIN guacamole_user_group_member ugm ON ug.user_group_id = ugm.user_group_id
            LEFT JOIN guacamole_user u ON ugm.user_id = u.user_id
            ORDER BY ug.name, u.username
        """
        )

        results = cursor.fetchall()
        groups_dict = {}

        for group_name, username in results:
            if group_name not in groups_dict:
                groups_dict[group_name] = []
            if username:  # Only add non-null usernames
                groups_dict[group_name].append(username)

        return groups_dict

    except mysql.connector.Error as e:
        raise ValueError(f"Error listing groups with users: {e}")


def list_users_with_usergroups(cursor) -> Dict[str, List[str]]:
    """List all users with their associated user group memberships.

    Retrieves a comprehensive mapping of all users in the system and the
    user groups they belong to. This provides a complete view of user
    group memberships for reporting and analysis.

    Args:
        cursor: Database cursor for executing queries.

    Returns:
        Dict[str, List[str]]: Mapping of usernames to lists of user group names.
            Users with no group memberships will have an empty list.

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> users = list_users_with_usergroups(cursor)
        >>> for username, groups in users.items():
        ...     print(f"{username}: {groups}")
        john.doe: ['admin', 'developers']
        jane.smith: ['users']
        guest: []
    """
    try:
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
        cursor.execute(query)
        results = cursor.fetchall()

        users_groups = {}
        for row in results:
            username = row[0]
            groupnames = row[1].split(",") if row[1] else []
            users_groups[username] = groupnames

        return users_groups

    except mysql.connector.Error as e:
        raise ValueError(f"Error listing users with user groups: {e}")


def list_connections_with_conngroups_and_parents(cursor) -> List[Tuple]:
    """List all connections with their groups, parent group, and user permissions.

    Retrieves comprehensive information about all connections including
    their protocols, parameters, associated groups, parent groups, and
    user permissions.

    Args:
        cursor: Database cursor for executing queries.

    Returns:
        List of tuples with connection information:
        (connection_id, name, protocol, hostname, port, groups, parent, user_permissions)

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> connections = list_connections_with_conngroups_and_parents(cursor)
        >>> for conn_id, name, protocol, host, port, groups, parent, users in connections:
        ...     print(f"{name}: {protocol} ({host}:{port})")
    """
    try:
        # Get basic connection info with groups
        cursor.execute(
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

        connections_info = cursor.fetchall()

        # Create a mapping of connection names to connection IDs
        connection_map = {
            name: conn_id for conn_id, name, _, _, _, _, _ in connections_info
        }

        # Now prepare the result array
        result = []
        for conn_info in connections_info:
            conn_id, name, protocol, host, port, groups, parent = conn_info

            # Get user permissions for this connection
            cursor.execute(
                """
                SELECT e.name
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s AND e.type = 'USER'
                """,
                (conn_id,),
            )

            user_permissions = [row[0] for row in cursor.fetchall()]

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
        raise ValueError(f"Error listing connections with groups: {e}")


def get_connection_by_id(cursor, connection_id: int) -> Optional[Tuple]:
    """Get a specific connection by its ID with comprehensive information.

    Retrieves detailed information about a single connection including
    its parameters, groups, parent group, and user permissions.

    Args:
        cursor: Database cursor for executing queries.
        connection_id: The database ID of the connection to retrieve.

    Returns:
        Optional tuple with connection information or None if not found:
        (connection_id, name, protocol, hostname, port, groups, parent, user_permissions)

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> connection = get_connection_by_id(cursor, 42)
        >>> if connection:
        ...     print(f"Found: {connection[1]} ({connection[2]})")
        >>> else:
        ...     print("Connection not found")
    """
    try:
        # Get basic connection info with groups
        cursor.execute(
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

        result = cursor.fetchone()
        if not result:
            return None

        conn_id, name, protocol, host, port, groups, parent = result

        # Get user permissions for this connection
        cursor.execute(
            """
            SELECT e.name
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s AND e.type = 'USER'
            """,
            (conn_id,),
        )

        user_permissions = [row[0] for row in cursor.fetchall()]

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
        raise ValueError(f"Error getting connection by ID: {e}")


def list_usergroups_with_users_and_connections(cursor) -> Dict[str, Dict[str, Any]]:
    """List all user groups with their associated users and connections.

    Retrieves a comprehensive mapping of all user groups in the system,
    including the users belonging to each group and the connections
    accessible to those users through group permissions.

    Args:
        cursor: Database cursor for executing queries.

    Returns:
        Dict[str, Dict[str, Any]]: Nested dictionary with group names as keys.
            Each group dictionary contains:
            - id (int): The database ID of the user group
            - users (List[str]): List of usernames belonging to the group
            - connections (List[str]): List of connection names accessible to the group

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> result = list_usergroups_with_users_and_connections(cursor)
        >>> admin_group = result.get('admin', {})
        >>> print(f"Admin users: {admin_group.get('users', [])}")
        >>> print(f"Admin connections: {admin_group.get('connections', [])}")
        Admin users: ['admin1', 'admin2']
        Admin connections: ['server1', 'server2']
    """
    try:
        # Get users per group with IDs
        cursor.execute(
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
            for row in cursor.fetchall()
        }

        # Get connections per group with IDs
        cursor.execute(
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
            for row in cursor.fetchall()
        }

        # Combine the results
        result = {}
        # Get all unique group names and their IDs
        all_groups = set(groups_users.keys()) | set(groups_connections.keys())

        for group_name, group_id in all_groups:
            users = groups_users.get((group_name, group_id), [])
            connections = groups_connections.get((group_name, group_id), [])

            result[group_name] = {
                'id': group_id,
                'users': users,
                'connections': connections
            }

        return result

    except mysql.connector.Error as e:
        raise ValueError(f"Error listing user groups with users and connections: {e}")


def list_connection_groups(cursor) -> Dict[str, Dict[str, Any]]:
    """List all connection groups with their connections and parent groups.

    Retrieves a comprehensive view of all connection groups in the system,
    including their associated connections and hierarchical parent relationships.

    Args:
        cursor: Database cursor for executing queries.

    Returns:
        Dict mapping group names to dictionaries with:
        - id (int): The group ID
        - parent (str): The parent group name or "ROOT"
        - connections (list): List of connection names

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> groups = list_connection_groups(cursor)
        >>> for group_name, data in groups.items():
        ...     print(f"{group_name}: {data['connections']}")
    """
    try:
        cursor.execute(
            """
            SELECT
                cg.connection_group_id,
                cg.connection_group_name,
                parent_cg.connection_group_name as parent_name,
                COUNT(c.connection_id) as connection_count,
                GROUP_CONCAT(c.connection_name ORDER BY c.connection_name) as connections
            FROM guacamole_connection_group cg
            LEFT JOIN guacamole_connection_group parent_cg
                ON cg.parent_id = parent_cg.connection_group_id
            LEFT JOIN guacamole_connection c ON cg.connection_group_id = c.parent_id
            GROUP BY cg.connection_group_id, cg.connection_group_name, parent_cg.connection_group_name
            ORDER BY cg.connection_group_name
            """
        )

        results = cursor.fetchall()
        groups_dict = {}

        for row in results:
            group_id, group_name, parent_name, connection_count, connections = row
            connections_list = connections.split(",") if connections else []

            groups_dict[group_name] = {
                'id': group_id,
                'parent': parent_name if parent_name else "ROOT",
                'connections': [conn for conn in connections_list if conn.strip()]
            }

        return groups_dict

    except mysql.connector.Error as e:
        raise ValueError(f"Error listing connection groups: {e}")


def get_connection_group_by_id(cursor, group_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific connection group by its ID with comprehensive information.

    Retrieves detailed information about a single connection group including
    its parent group and associated connections.

    Args:
        cursor: Database cursor for executing queries.
        group_id: The database ID of the connection group to retrieve.

    Returns:
        Optional dictionary with group information or None if not found:
        - id (int): The group ID
        - name (str): The group name
        - parent (str): The parent group name or "ROOT"
        - connections (list): List of connection names

    Raises:
        mysql.connector.Error: If database query fails.

    Example:
        >>> cursor = db.cursor()
        >>> group = get_connection_group_by_id(cursor, 42)
        >>> if group:
        ...     print(f"Found: {group['name']} with {len(group['connections'])} connections")
        >>> else:
        ...     print("Group not found")
    """
    try:
        cursor.execute(
            """
            SELECT
                cg.connection_group_id,
                cg.connection_group_name,
                parent_cg.connection_group_name as parent_name,
                COUNT(c.connection_id) as connection_count,
                GROUP_CONCAT(c.connection_name ORDER BY c.connection_name) as connections
            FROM guacamole_connection_group cg
            LEFT JOIN guacamole_connection_group parent_cg
                ON cg.parent_id = parent_cg.connection_group_id
            LEFT JOIN guacamole_connection c ON cg.connection_group_id = c.parent_id
            WHERE cg.connection_group_id = %s
            GROUP BY cg.connection_group_id, cg.connection_group_name, parent_cg.connection_group_name
            """,
            (group_id,),
        )

        result = cursor.fetchone()
        if not result:
            return None

        group_id_val, group_name, parent_name, connection_count, connections = result
        connections_list = connections.split(",") if connections else []

        return {
            'id': group_id_val,
            'name': group_name,
            'parent': parent_name if parent_name else "ROOT",
            'connections': [conn for conn in connections_list if conn.strip()]
        }

    except mysql.connector.Error as e:
        raise ValueError(f"Error getting connection group by ID: {e}")