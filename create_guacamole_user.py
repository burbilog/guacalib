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

def delete_existing_user(cursor, username):
    try:
        # Delete user permissions first (foreign key constraint)
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

def grant_connection_permission(cursor, username, connection_id):
    try:
        cursor.execute("""
            INSERT INTO guacamole_connection_permission (entity_id, connection_id, permission)
            SELECT entity.entity_id, %s, 'READ'
            FROM guacamole_entity entity
            WHERE entity.name = %s AND entity.type = 'USER'
        """, (connection_id, username))

    except mysql.connector.Error as e:
        print(f"Error granting connection permission: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Create Guacamole user and VNC connection')
    parser.add_argument('--username', required=True, help='Username for Guacamole')
    parser.add_argument('--password', required=True, help='Password for Guacamole user')
    parser.add_argument('--vnc-host', required=True, help='VNC server hostname/IP')
    parser.add_argument('--vnc-port', required=True, help='VNC server port')
    parser.add_argument('--vnc-password', required=True, help='VNC server password')
    parser.add_argument('--config', default='db_config.ini', help='Path to database config file')

    args = parser.parse_args()

    # Read database configuration
    db_config = read_config(args.config)
    
    # Connect to database
    conn = connect_db(db_config)
    cursor = conn.cursor()

    try:
        # Delete existing user and connection if they exist
        connection_name = f"vnc-{args.username}"
        delete_existing_user(cursor, args.username)
        delete_existing_connection(cursor, connection_name)

        # Create new user and connection
        create_user(cursor, args.username, args.password)
        connection_id = create_vnc_connection(cursor, connection_name, 
                                           args.vnc_host, args.vnc_port, 
                                           args.vnc_password)
        
        # Grant permission
        grant_connection_permission(cursor, args.username, connection_id)

        # Commit changes
        conn.commit()
        print(f"Successfully created user '{args.username}' and VNC connection '{connection_name}'")

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
