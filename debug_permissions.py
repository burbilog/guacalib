#!/usr/bin/env python3

import sys
import configparser
import mysql.connector


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: debug_permissions.py CONFIG_FILE CONNECTION_NAME [CONNECTION_GROUP_NAME]"
        )
        print("  CONNECTION_NAME: Debug permissions for individual connection")
        print(
            "  CONNECTION_GROUP_NAME: Debug permissions for connection group (optional)"
        )
        sys.exit(1)

    config_file = sys.argv[1]
    target = sys.argv[2]
    is_conngroup = len(sys.argv) >= 4 and sys.argv[3] == "--conngroup"

    # Read config
    config = configparser.ConfigParser()
    config.read(config_file)

    if "mysql" not in config:
        print(f"Error: Missing [mysql] section in config file: {config_file}")
        sys.exit(1)

    db_config = {
        "host": config["mysql"]["host"],
        "user": config["mysql"]["user"],
        "password": config["mysql"]["password"],
        "database": config["mysql"]["database"],
        # Use a more universally compatible collation
        "charset": "utf8mb4",
        "collation": "utf8mb4_general_ci",
    }

    # Connect to DB
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(buffered=True)

        if is_conngroup:
            # Handle connection group
            # Check if connection group exists
            cursor.execute(
                "SELECT connection_group_id FROM guacamole_connection_group WHERE connection_group_name = %s",
                (target,),
            )
            result = cursor.fetchone()
            if not result:
                print(f"ERROR: Connection group '{target}' not found")
                sys.exit(1)

            target_id = result[0]
            print(f"Connection Group ID for '{target}': {target_id}")

            # Check all permissions for connection group
            cursor.execute(
                """
                SELECT cp.entity_id, e.name, e.type, cp.permission
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s
            """,
                (target_id,),
            )

            target_type = "connection group"

        else:
            # Handle connection
            # Check if connection exists
            cursor.execute(
                "SELECT connection_id FROM guacamole_connection WHERE connection_name = %s",
                (target,),
            )
            result = cursor.fetchone()
            if not result:
                print(f"ERROR: Connection '{target}' not found")
                sys.exit(1)

            target_id = result[0]
            print(f"Connection ID for '{target}': {target_id}")

            # Check all permissions for connection
            cursor.execute(
                """
                SELECT cp.entity_id, e.name, e.type, cp.permission
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s
            """,
                (target_id,),
            )

            target_type = "connection"

        permissions = cursor.fetchall()
        if not permissions:
            print(f"No permissions found for {target_type} '{target}'")
        else:
            print(f"Found {len(permissions)} permissions:")
            for perm in permissions:
                entity_id, name, entity_type, permission = perm
                print(
                    f"  Entity ID: {entity_id}, Name: {name}, Type: {entity_type}, Permission: {permission}"
                )

        # Let's check for user permissions specifically
        cursor.execute(
            """
            SELECT e.name
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s AND e.type = 'USER'
        """,
            (target_id,),
        )

        user_permissions = cursor.fetchall()
        if not user_permissions:
            print(f"No user permissions found for {target_type} '{target}'")
        else:
            print(f"Found {len(user_permissions)} user permissions:")
            for perm in user_permissions:
                print(f"  User: {perm[0]}")

        # Also check for USER_GROUP permissions
        cursor.execute(
            """
            SELECT e.name
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s AND e.type = 'USER_GROUP'
        """,
            (target_id,),
        )

        group_permissions = cursor.fetchall()
        if not group_permissions:
            print(f"No user group permissions found for {target_type} '{target}'")
        else:
            print(f"Found {len(group_permissions)} user group permissions:")
            for perm in group_permissions:
                print(f"  Group: {perm[0]}")

        # If debugging a connection group, show additional information
        if is_conngroup:
            print(f"\nConnection Group Details:")
            cursor.execute(
                """
                SELECT
                    cg.connection_group_id,
                    cg.connection_group_name,
                    cg.type,
                    parent_cg.connection_group_name as parent_name
                FROM guacamole_connection_group cg
                LEFT JOIN guacamole_connection_group parent_cg ON cg.parent_id = parent_cg.connection_group_id
                WHERE cg.connection_group_id = %s
            """,
                (target_id,),
            )

            group_info = cursor.fetchone()
            if group_info:
                group_id, group_name, group_type, parent_name = group_info
                print(f"  Group ID: {group_id}")
                print(f"  Group Name: {group_name}")
                print(f"  Type: {group_type}")
                print(f"  Parent: {parent_name if parent_name else 'None'}")

            # Show connections in this group
            cursor.execute(
                """
                SELECT c.connection_name, c.protocol
                FROM guacamole_connection c
                WHERE c.parent_id = %s
                ORDER BY c.connection_name
            """,
                (target_id,),
            )

            connections = cursor.fetchall()
            if connections:
                print(f"  Connections in group:")
                for conn_name, protocol in connections:
                    print(f"    - {conn_name} ({protocol})")
            else:
                print(f"  No direct connections in this group")

        # Only show connection details if not debugging connection group
        if not is_conngroup:
            # Test the current implementation
            print(
                "\nSimulating the list_connections_with_conngroups_and_parents query:"
            )
            cursor.execute(
                """
                SELECT
                    c.connection_id,
                    c.connection_name,
                    c.protocol,
                    (SELECT parameter_value FROM guacamole_connection_parameter
                     WHERE connection_id = c.connection_id AND parameter_name = 'hostname' LIMIT 1) as hostname,
                    (SELECT parameter_value FROM guacamole_connection_parameter
                     WHERE connection_id = c.connection_id AND parameter_name = 'port' LIMIT 1) as port,
                    cg.connection_group_name as parent
                FROM guacamole_connection c
                LEFT JOIN guacamole_connection_group cg ON c.parent_id = cg.connection_group_id
                WHERE c.connection_name = %s
            """,
                (target,),
            )

        if not is_conngroup:
            conn_info = cursor.fetchone()
            if conn_info:
                conn_id, name, protocol, hostname, port, parent = conn_info
                print(f"Basic connection info:")
                print(f"  Connection ID: {conn_id}")
                print(f"  Name: {name}")
                print(f"  Protocol: {protocol}")
                print(f"  Hostname: {hostname}")
                print(f"  Port: {port}")
                print(f"  Parent: {parent}")

                # Get groups separately
                cursor.execute(
                    """
                    SELECT e.name
                    FROM guacamole_connection_permission cp
                    JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                    WHERE cp.connection_id = %s AND e.type = 'USER_GROUP'
                """,
                    (conn_id,),
                )

                groups = [row[0] for row in cursor.fetchall()]
                print(f"  Groups: {', '.join(groups) if groups else 'None'}")

                # Get user permissions separately
                cursor.execute(
                    """
                    SELECT e.name
                    FROM guacamole_connection_permission cp
                    JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                    WHERE cp.connection_id = %s AND e.type = 'USER'
                """,
                    (conn_id,),
                )

                users = [row[0] for row in cursor.fetchall()]
                print(f"  User Permissions: {', '.join(users) if users else 'None'}")
            else:
                print(f"Connection '{target}' not found in basic query")

        cursor.close()
        conn.close()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
