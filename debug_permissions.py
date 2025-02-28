#!/usr/bin/env python3

import sys
import configparser
import mysql.connector

def main():
    if len(sys.argv) < 3:
        print("Usage: debug_permissions.py CONFIG_FILE CONNECTION_NAME")
        sys.exit(1)
    
    config_file = sys.argv[1]
    connection_name = sys.argv[2]
    
    # Read config
    config = configparser.ConfigParser()
    config.read(config_file)
    
    if 'mysql' not in config:
        print(f"Error: Missing [mysql] section in config file: {config_file}")
        sys.exit(1)
    
    db_config = {
        'host': config['mysql']['host'],
        'user': config['mysql']['user'],
        'password': config['mysql']['password'],
        'database': config['mysql']['database'],
        # Use a more universally compatible collation
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_general_ci'
    }
    
    # Connect to DB
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if connection exists
        cursor.execute("SELECT connection_id FROM guacamole_connection WHERE connection_name = %s", (connection_name,))
        result = cursor.fetchone()
        if not result:
            print(f"ERROR: Connection '{connection_name}' not found")
            sys.exit(1)
        
        connection_id = result[0]
        print(f"Connection ID for '{connection_name}': {connection_id}")
        
        # Check all permissions
        cursor.execute("""
            SELECT cp.entity_id, e.name, e.type, cp.permission
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s
        """, (connection_id,))
        
        permissions = cursor.fetchall()
        if not permissions:
            print(f"No permissions found for connection '{connection_name}'")
        else:
            print(f"Found {len(permissions)} permissions:")
            for perm in permissions:
                entity_id, name, entity_type, permission = perm
                print(f"  Entity ID: {entity_id}, Name: {name}, Type: {entity_type}, Permission: {permission}")
        
        # Let's check for user permissions specifically
        cursor.execute("""
            SELECT e.name
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s AND e.type = 'USER'
        """, (connection_id,))
        
        user_permissions = cursor.fetchall()
        if not user_permissions:
            print(f"No user permissions found for connection '{connection_name}'")
        else:
            print(f"Found {len(user_permissions)} user permissions:")
            for perm in user_permissions:
                print(f"  User: {perm[0]}")
        
        # Also check for USER_GROUP permissions
        cursor.execute("""
            SELECT e.name
            FROM guacamole_connection_permission cp
            JOIN guacamole_entity e ON cp.entity_id = e.entity_id
            WHERE cp.connection_id = %s AND e.type = 'USER_GROUP'
        """, (connection_id,))
        
        group_permissions = cursor.fetchall()
        if not group_permissions:
            print(f"No user group permissions found for connection '{connection_name}'")
        else:
            print(f"Found {len(group_permissions)} user group permissions:")
            for perm in group_permissions:
                print(f"  Group: {perm[0]}")
        
        # Test the current implementation
        print("\nSimulating the list_connections_with_conngroups_and_parents query:")
        cursor.execute("""
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
        """, (connection_name,))
        
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
            cursor.execute("""
                SELECT e.name
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s AND e.type = 'USER_GROUP'
            """, (conn_id,))
            
            groups = [row[0] for row in cursor.fetchall()]
            print(f"  Groups: {', '.join(groups) if groups else 'None'}")
            
            # Get user permissions separately
            cursor.execute("""
                SELECT e.name
                FROM guacamole_connection_permission cp
                JOIN guacamole_entity e ON cp.entity_id = e.entity_id
                WHERE cp.connection_id = %s AND e.type = 'USER'
            """, (conn_id,))
            
            users = [row[0] for row in cursor.fetchall()]
            print(f"  User Permissions: {', '.join(users) if users else 'None'}")
        else:
            print(f"Connection '{connection_name}' not found in basic query")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
