#!/usr/bin/env python3

import mysql.connector
import configparser
import sys

class GuacamoleDB:
    def __init__(self, config_file='db_config.ini'):
        self.db_config = self.read_config(config_file)
        self.conn = self.connect_db()
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            if exc_type is not None:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()

    @staticmethod
    def read_config(config_file):
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

    def connect_db(self):
        try:
            return mysql.connector.connect(
                **self.db_config,
                charset='utf8mb4',
                collation='utf8mb4_general_ci'
            )
        except mysql.connector.Error as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)

    def get_group_id(self, group_name):
        try:
            self.cursor.execute("""
                SELECT user_group_id 
                FROM guacamole_user_group g
                JOIN guacamole_entity e ON g.entity_id = e.entity_id
                WHERE e.name = %s AND e.type = 'USER_GROUP'
            """, (group_name,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                raise Exception(f"Group '{group_name}' not found")
        except mysql.connector.Error as e:
            print(f"Error getting group ID: {e}")
            raise

    def delete_existing_user(self, username):
        try:
            # Delete user group permissions first
            self.cursor.execute("""
                DELETE FROM guacamole_user_group_permission 
                WHERE entity_id IN (
                    SELECT entity_id FROM guacamole_entity 
                    WHERE name = %s AND type = 'USER'
                )
            """, (username,))

            # Delete user group memberships
            self.cursor.execute("""
                DELETE FROM guacamole_user_group_member 
                WHERE member_entity_id IN (
                    SELECT entity_id FROM guacamole_entity 
                    WHERE name = %s AND type = 'USER'
                )
            """, (username,))

            # Delete user permissions
            self.cursor.execute("""
                DELETE FROM guacamole_connection_permission 
                WHERE entity_id IN (
                    SELECT entity_id FROM guacamole_entity 
                    WHERE name = %s AND type = 'USER'
                )
            """, (username,))

            # Delete user
            self.cursor.execute("""
                DELETE FROM guacamole_user 
                WHERE entity_id IN (
                    SELECT entity_id FROM guacamole_entity 
                    WHERE name = %s AND type = 'USER'
                )
            """, (username,))

            # Delete entity
            self.cursor.execute("""
                DELETE FROM guacamole_entity 
                WHERE name = %s AND type = 'USER'
            """, (username,))

        except mysql.connector.Error as e:
            print(f"Error deleting existing user: {e}")
            raise

    def delete_existing_group(self, group_name):
        try:
            # Delete group memberships
            self.cursor.execute("""
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
            self.cursor.execute("""
                DELETE FROM guacamole_connection_permission 
                WHERE entity_id IN (
                    SELECT entity_id FROM guacamole_entity 
                    WHERE name = %s AND type = 'USER_GROUP'
                )
            """, (group_name,))

            # Delete user group
            self.cursor.execute("""
                DELETE FROM guacamole_user_group 
                WHERE entity_id IN (
                    SELECT entity_id FROM guacamole_entity 
                    WHERE name = %s AND type = 'USER_GROUP'
                )
            """, (group_name,))

            # Delete entity
            self.cursor.execute("""
                DELETE FROM guacamole_entity 
                WHERE name = %s AND type = 'USER_GROUP'
            """, (group_name,))

        except mysql.connector.Error as e:
            print(f"Error deleting existing group: {e}")
            raise

    def delete_existing_connection(self, connection_name):
        try:
            # Delete connection parameters first (foreign key constraint)
            self.cursor.execute("""
                DELETE FROM guacamole_connection_parameter 
                WHERE connection_id IN (
                    SELECT connection_id FROM guacamole_connection 
                    WHERE connection_name = %s
                )
            """, (connection_name,))

            # Delete connection permissions
            self.cursor.execute("""
                DELETE FROM guacamole_connection_permission 
                WHERE connection_id IN (
                    SELECT connection_id FROM guacamole_connection 
                    WHERE connection_name = %s
                )
            """, (connection_name,))

            # Delete connection
            self.cursor.execute("""
                DELETE FROM guacamole_connection 
                WHERE connection_name = %s
            """, (connection_name,))

        except mysql.connector.Error as e:
            print(f"Error deleting existing connection: {e}")
            raise

    def create_user(self, username, password):
        try:
            # Create entity
            self.cursor.execute("""
                INSERT INTO guacamole_entity (name, type) 
                VALUES (%s, 'USER')
            """, (username,))

            # Create user
            self.cursor.execute("""
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

    def create_group(self, group_name):
        try:
            # Create entity
            self.cursor.execute("""
                INSERT INTO guacamole_entity (name, type) 
                VALUES (%s, 'USER_GROUP')
            """, (group_name,))

            # Create group
            self.cursor.execute("""
                INSERT INTO guacamole_user_group (entity_id, disabled)
                SELECT entity_id, FALSE
                FROM guacamole_entity 
                WHERE name = %s AND type = 'USER_GROUP'
            """, (group_name,))

        except mysql.connector.Error as e:
            print(f"Error creating group: {e}")
            raise

    def add_user_to_group(self, username, group_name):
        try:
            # Get the group ID
            group_id = self.get_group_id(group_name)
            
            # Get the user's entity ID
            self.cursor.execute("""
                SELECT entity_id 
                FROM guacamole_entity 
                WHERE name = %s AND type = 'USER'
            """, (username,))
            user_entity_id = self.cursor.fetchone()[0]

            # Add user to group
            self.cursor.execute("""
                INSERT INTO guacamole_user_group_member 
                (user_group_id, member_entity_id)
                VALUES (%s, %s)
            """, (group_id, user_entity_id))

            # Grant group permissions to user
            self.cursor.execute("""
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

    def create_vnc_connection(self, connection_name, hostname, port, vnc_password):
        try:
            # Create connection
            self.cursor.execute("""
                INSERT INTO guacamole_connection (connection_name, protocol)
                VALUES (%s, 'vnc')
            """, (connection_name,))

            # Get connection_id
            self.cursor.execute("""
                SELECT connection_id FROM guacamole_connection
                WHERE connection_name = %s
            """, (connection_name,))
            connection_id = self.cursor.fetchone()[0]

            # Create connection parameters
            params = [
                ('hostname', hostname),
                ('port', port),
                ('password', vnc_password)
            ]

            for param_name, param_value in params:
                self.cursor.execute("""
                    INSERT INTO guacamole_connection_parameter 
                    (connection_id, parameter_name, parameter_value)
                    VALUES (%s, %s, %s)
                """, (connection_id, param_name, param_value))

            return connection_id

        except mysql.connector.Error as e:
            print(f"Error creating VNC connection: {e}")
            raise

    def grant_connection_permission(self, entity_name, entity_type, connection_id):
        try:
            self.cursor.execute("""
                INSERT INTO guacamole_connection_permission (entity_id, connection_id, permission)
                SELECT entity.entity_id, %s, 'READ'
                FROM guacamole_entity entity
                WHERE entity.name = %s AND entity.type = %s
            """, (connection_id, entity_name, entity_type))

        except mysql.connector.Error as e:
            print(f"Error granting connection permission: {e}")
            raise
