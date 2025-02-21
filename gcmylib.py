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
            try:
                # Always commit unless there was an exception
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
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

    def list_users(self):
        try:
            self.cursor.execute("""
                SELECT name 
                FROM guacamole_entity 
                WHERE type = 'USER' 
                ORDER BY name
            """)
            return [row[0] for row in self.cursor.fetchall()]
        except mysql.connector.Error as e:
            print(f"Error listing users: {e}")
            raise

    def list_groups(self):
        try:
            self.cursor.execute("""
                SELECT name 
                FROM guacamole_entity 
                WHERE type = 'USER_GROUP' 
                ORDER BY name
            """)
            return [row[0] for row in self.cursor.fetchall()]
        except mysql.connector.Error as e:
            print(f"Error listing groups: {e}")
            raise

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
            print(f"Attempting to delete connection: {connection_name}")
            
            # Get connection_id first
            self.cursor.execute("""
                SELECT connection_id FROM guacamole_connection
                WHERE connection_name = %s
            """, (connection_name,))
            result = self.cursor.fetchone()
            if not result:
                print(f"Connection '{connection_name}' doesn't exist - skipping deletion")
                return  # Exit early instead of raising error
            connection_id = result[0]
            print(f"Found connection_id: {connection_id}")

            # Delete connection history
            print("Deleting connection history...")
            self.cursor.execute("""
                DELETE FROM guacamole_connection_history
                WHERE connection_id = %s
            """, (connection_id,))

            # Delete connection parameters
            print("Deleting connection parameters...")
            self.cursor.execute("""
                DELETE FROM guacamole_connection_parameter
                WHERE connection_id = %s
            """, (connection_id,))

            # Delete connection permissions
            print("Deleting connection permissions...")
            self.cursor.execute("""
                DELETE FROM guacamole_connection_permission
                WHERE connection_id = %s
            """, (connection_id,))

            # Finally delete the connection
            print("Deleting connection...")
            self.cursor.execute("""
                DELETE FROM guacamole_connection
                WHERE connection_id = %s
            """, (connection_id,))

            # Commit the transaction
            print("Committing transaction...")
            self.conn.commit()
            print(f"Successfully deleted connection '{connection_name}'")

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

    def get_connection_group_id(self, group_path):
        """Resolve nested connection group path to group_id"""
        try:
            groups = group_path.split('/')
            parent_group_id = None
            
            for group_name in groups:
                self.cursor.execute("""
                    SELECT connection_group_id 
                    FROM guacamole_connection_group 
                    WHERE connection_group_name = %s
                    AND parent_group_id %s
                    ORDER BY connection_group_id
                    LIMIT 1
                """, (
                    group_name, 
                    "IS NULL" if parent_group_id is None else "= %s"
                ) + ((parent_group_id,) if parent_group_id is not None else ()))
                
                result = self.cursor.fetchone()
                if not result:
                    raise ValueError(f"Group '{group_name}' not found in path '{group_path}'")
                
                parent_group_id = result[0]
                
            return parent_group_id

        except mysql.connector.Error as e:
            print(f"Error resolving group path: {e}")
            raise

    def create_vnc_connection(self, connection_name, hostname, port, vnc_password, parent_group_id=None):
        if not all([connection_name, hostname, port]):
            raise ValueError("Missing required connection parameters")
            
        try:
            # Create connection
            self.cursor.execute("""
                INSERT INTO guacamole_connection 
                (connection_name, protocol, parent_id)
                VALUES (%s, 'vnc', %s)
            """, (connection_name, parent_group_id))

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

    def grant_connection_permission(self, entity_name, entity_type, connection_id, group_path=None):
        try:
            # If group path is specified
            if group_path:
                parent_group_id = self.get_connection_group_id(group_path)
                
                # Get existing connection group assignment
                self.cursor.execute("""
                    SELECT connection_group_id FROM guacamole_connection_group
                    WHERE connection_group_name = %s
                """, (group_path.split('/')[-1],))
                group_id_result = self.cursor.fetchone()
                
                if not group_id_result:
                    raise ValueError(f"Final group in path '{group_path}' not found")
                
                # Assign connection to the group
                self.cursor.execute("""
                    UPDATE guacamole_connection
                    SET parent_id = %s
                    WHERE connection_id = %s
                """, (parent_group_id, connection_id))

            # Grant permission
            self.cursor.execute("""
                INSERT INTO guacamole_connection_permission (entity_id, connection_id, permission)
                SELECT entity.entity_id, %s, 'READ'
                FROM guacamole_entity entity
                WHERE entity.name = %s AND entity.type = %s
            """, (connection_id, entity_name, entity_type))

        except mysql.connector.Error as e:
            print(f"Error granting connection permission: {e}")
            raise

    def list_users_with_groups(self):
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
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        users_groups = {}
        for row in results:
            username = row[0]
            groupnames = row[1].split(',') if row[1] else []
            users_groups[username] = groupnames
        
        return users_groups

    def list_connections(self):
        """List all VNC connections with their parameters"""
        try:
            self.cursor.execute("""
                SELECT 
                    c.connection_name,
                    p1.parameter_value AS hostname,
                    p2.parameter_value AS port,
                    p3.parameter_value AS password
                FROM guacamole_connection c
                JOIN guacamole_connection_parameter p1 
                    ON c.connection_id = p1.connection_id AND p1.parameter_name = 'hostname'
                JOIN guacamole_connection_parameter p2 
                    ON c.connection_id = p2.connection_id AND p2.parameter_name = 'port'
                LEFT JOIN guacamole_connection_parameter p3 
                    ON c.connection_id = p3.connection_id AND p3.parameter_name = 'password'
                WHERE c.protocol = 'vnc'
                ORDER BY c.connection_name
            """)
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Error listing connections: {e}")
            raise

    def list_groups_with_users(self):
        query = """
            SELECT DISTINCT 
                e1.name as groupname,
                GROUP_CONCAT(e2.name) as usernames
            FROM guacamole_entity e1
            JOIN guacamole_user_group ug ON e1.entity_id = ug.entity_id
            LEFT JOIN guacamole_user_group_member ugm 
                ON ug.user_group_id = ugm.user_group_id
            LEFT JOIN guacamole_entity e2
                ON ugm.member_entity_id = e2.entity_id
            WHERE e1.type = 'USER_GROUP'
            GROUP BY e1.name
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        groups_users = {}
        for row in results:
            groupname = row[0]
            usernames = row[1].split(',') if row[1] else []
            groups_users[groupname] = usernames
        
        return groups_users
