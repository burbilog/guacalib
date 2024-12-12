#!/usr/bin/env python3

import mysql.connector
import argparse
import configparser
import sys

def read_config(config_file='db_config.ini'):
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        return {
            'host': config['mysql']['host'],
            'user': config['mysql']['user'],
            'password': config['mysql']['password'],
            'database': config['mysql']['database']
        }
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

def connect_db(db_config):
    try:
        return mysql.connector.connect(
            **db_config,
            charset='utf8mb4',
            collation='utf8mb4_general_ci'
        )
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def get_group_id(cursor, group_name):
    try:
        cursor.execute("""
            SELECT user_group_id 
            FROM guacamole_user_group g
            JOIN guacamole_entity e ON g.entity_id = e.entity_id
            WHERE e.name = %s AND e.type = 'USER_GROUP'
        """, (group_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            raise Exception(f"Group '{group_name}' not found")
    except mysql.connector.Error as e:
        print(f"Error getting group ID: {e}")
        raise

def delete_existing_user(cursor, username):
    try:
        # Delete user group permissions first
        cursor.execute("""
            DELETE FROM guacamole_user_group_permission 
            WHERE entity_id IN (
                SELECT entity_id FROM guacamole_entity 
                WHERE name = %s AND type = 'USER'
            )
        """, (username,))

        # Delete user group memberships
        cursor.execute("""
            DELETE FROM guacamole_user_group_member 
            WHERE member_entity_id IN (
                SELECT entity_id FROM guacamole_entity 
                WHERE name = %s AND type = 'USER'
            )
        """, (username,))

        # Delete user permissions
        cursor.execute("""
            DELETE FROM guacamole_connection_permission 
            WHERE entity_id IN (
                SELECT entity_id FROM guacamole_entity 
                WHERE name = %s AND type = 'USER'
            )
        """, (username,))

        # Delete user
        cursor.execute("""
            DELETE FROM guacamole_user 
            WHERE entity_id IN (
                SELECT entity_id FROM guacamole_entity 
                WHERE name = %s AND type = 'USER'
            )
        """, (username,))

        # Delete entity
        cursor.execute("""
            DELETE FROM guacamole_entity 
            WHERE name = %s AND type = 'USER'
        """, (username,))

    except mysql.connector.Error as e:
        print(f"Error deleting existing user: {e}")
        raise

def delete_existing_group(cursor, group_name):
    try:
        # Delete group memberships
        cursor.execute("""
            DELETE FROM guacamole_user_group_member 
            WHERE user_group_id IN (
                SELECT user_group_id FROM guacamole_user_group 
                WHERE entity_id IN (
                    SELECT entity_id FROM guacamole_entity 
                    WHERE name = %s AND type = 'USER_GROUP'
                )
            )
        """, (group_name,))

        # Delete group permissions
        cursor.execute("""
            DELETE FROM guacamole_connection_permission 
            WHERE entity_id IN (
                SELECT entity_id FROM guacamole_entity 
                WHERE name = %s AND type = 'USER_GROUP'
            )
        """, (group_name,))

        # Delete user group
        cursor.execute("""
            DELETE FROM guacamole_user_group 
            WHERE entity_id IN (
                SELECT entity_id FROM guacamole_entity 
                WHERE name = %s AND type = 'USER_GROUP'
            )
        """, (group_name,))

        # Delete entity
        cursor.execute("""
            DELETE FROM guacamole_entity 
            WHERE name = %s AND type = 'USER_GROUP'
        """, (group_name,))

    except mysql.connector.Error as e:
        print(f"Error deleting existing group: {e}")
        raise

def delete_existing_connection(cursor, connection_name):
    try:
        # Delete connection parameters first (foreign key constraint)
        cursor.execute("""
            DELETE FROM guacamole_connection_parameter 
            WHERE connection_id IN (
                SELECT connection_id FROM guacamole_connection 
                WHERE connection_name = %s
            )
        """, (connection_name,))

        # Delete connection permissions
        cursor.execute("""
            DELETE FROM guacamole_connection_permission 
            WHERE connection_id IN (
                SELECT connection_id FROM guacamole_connection 
                WHERE connection_name = %s
            )
        """, (connection_name,))

        # Delete connection
        cursor.execute("""
            DELETE FROM guacamole_connection 
            WHERE connection_name = %s
        """, (connection_name,))

    except mysql.connector.Error as e:
        print(f"Error deleting existing connection: {e}")
        raise

def create_user(cursor, username, password):
    try:
        # Create entity
        cursor.execute("""
            INSERT INTO guacamole_entity (name, type) 
            VALUES (%s, 'USER')
        """, (username,))

        # Create user
        cursor.execute("""
            INSERT INTO guacamole_user (entity_id, password_hash, password_salt, password_date)
            SELECT entity_id, 
                   UNHEX(SHA2(CONCAT(%s, HEX(RANDOM_BYTES(32))), 256)),
                   RANDOM_BYTES(32),
                   NOW()
            FROM guacamole_entity 
            WHERE name = %s AND type = 'USER'
        """, (password, username))

    except mysql.connector.Error as e:
        print(f"Error creating user: {e}")
        raise

def create_group(cursor, group_name):
    try:
        # Create entity
        cursor.execute("""
            INSERT INTO guacamole_entity (name, type) 
            VALUES (%s, 'USER_GROUP')
        """, (group_name,))

        # Create group
        cursor.execute("""
            INSERT INTO guacamole_user_group (entity_id, disabled)
            SELECT entity_id, FALSE
            FROM guacamole_entity 
            WHERE name = %s AND type = 'USER_GROUP'
        """, (group_name,))

    except mysql.connector.Error as e:
        print(f"Error creating group: {e}")
        raise

def add_user_to_group(cursor, username, group_name):
    try:
        # Get the group ID
        group_id = get_group_id(cursor, group_name)
        
        # Get the user's entity ID
        cursor.execute("""
            SELECT entity_id 
            FROM guacamole_entity 
            WHERE name = %s AND type = 'USER'
        """, (username,))
        user_entity_id = cursor.fetchone()[0]

        # Add user to group
        cursor.execute("""
            INSERT INTO guacamole_user_group_member 
            (user_group_id, member_entity_id)
            VALUES (%s, %s)
        """, (group_id, user_entity_id))

        # Grant group permissions to user
        cursor.execute("""
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
        """, (user_entity_id, group_id, user_entity_id, group_id))

    except mysql.connector.Error as e:
        print(f"Error adding user to group: {e}")
        raise

def create_vnc_connection(cursor, connection_name, hostname, port, vnc_password):
    try:
        # Create connection
        cursor.execute("""
            INSERT INTO guacamole_connection (connection_name, protocol)
            VALUES (%s, 'vnc')
        """, (connection_name,))

        # Get connection_id
        cursor.execute("""
            SELECT connection_id FROM guacamole_connection
            WHERE connection_name = %s
        """, (connection_name,))
        connection_id = cursor.fetchone()[0]

        # Create connection parameters
        params = [
            ('hostname', hostname),
            ('port', port),
            ('password', vnc_password)
        ]

        for param_name, param_value in params:
            cursor.execute("""
                INSERT INTO guacamole_connection_parameter 
                (connection_id, parameter_name, parameter_value)
                VALUES (%s, %s, %s)
            """, (connection_id, param_name, param_value))

        return connection_id

    except mysql.connector.Error as e:
        print(f"Error creating VNC connection: {e}")
        raise

def grant_connection_permission(cursor, entity_name, entity_type, connection_id):
    try:
        cursor.execute("""
            INSERT INTO guacamole_connection_permission (entity_id, connection_id, permission)
            SELECT entity.entity_id, %s, 'READ'
            FROM guacamole_entity entity
            WHERE entity.name = %s AND entity.type = %s
        """, (connection_id, entity_name, entity_type))

    except mysql.connector.Error as e:
        print(f"Error granting connection permission: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Manage Guacamole users, groups, and connections')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # User command
    user_parser = subparsers.add_parser('user', help='Manage users')
    user_parser.add_argument('--username', required=True, help='Username for Guacamole')
    user_parser.add_argument('--password', required=True, help='Password for Guacamole user')
    user_parser.add_argument('--group', help='Group to add user to')
    user_parser.add_argument('--vnc-host', required=True, help='VNC server hostname/IP')
    user_parser.add_argument('--vnc-port', required=True, help='VNC server port')
    user_parser.add_argument('--vnc-password', required=True, help='VNC server password')

    # Group command
    group_parser = subparsers.add_parser('group', help='Manage groups')
    group_parser.add_argument('--name', required=True, help='Group name')
    group_parser.add_argument('--vnc-host', required=True, help='VNC server hostname/IP')
    group_parser.add_argument('--vnc-port', required=True, help='VNC server port')
    group_parser.add_argument('--vnc-password', required=True, help='VNC server password')

    # Common arguments
    parser.add_argument('--config', default='db_config.ini', help='Path to database config file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Read database configuration
    db_config = read_config(args.config)
    
    # Connect to database
    conn = connect_db(db_config)
    cursor = conn.cursor()

    try:
        if args.command == 'user':
            # Handle user creation
            connection_name = f"vnc-{args.username}"
            delete_existing_user(cursor, args.username)
            delete_existing_connection(cursor, connection_name)

            create_user(cursor, args.username, args.password)
            connection_id = create_vnc_connection(cursor, connection_name, 
                                               args.vnc_host, args.vnc_port, 
                                               args.vnc_password)
            
            grant_connection_permission(cursor, args.username, 'USER', connection_id)

            if args.group:
                add_user_to_group(cursor, args.username, args.group)
                print(f"Added user '{args.username}' to group '{args.group}'")

            print(f"Successfully created user '{args.username}' and VNC connection '{connection_name}'")

        elif args.command == 'group':
            # Handle group creation
            connection_name = f"vnc-{args.name}"
            delete_existing_group(cursor, args.name)
            delete_existing_connection(cursor, connection_name)

            create_group(cursor, args.name)
            connection_id = create_vnc_connection(cursor, connection_name,
                                               args.vnc_host, args.vnc_port,
                                               args.vnc_password)
            
            grant_connection_permission(cursor, args.name, 'USER_GROUP', connection_id)
            print(f"Successfully created group '{args.name}' and VNC connection '{connection_name}'")

        # Commit changes
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
