#!/usr/bin/env python3

import argparse
import sys
from gcmylib import GuacamoleDB

def setup_user_subcommands(subparsers):
    user_parser = subparsers.add_parser('user', help='Manage Guacamole users')
    user_subparsers = user_parser.add_subparsers(dest='user_command', help='User commands')

    # User new command
    new_user = user_subparsers.add_parser('new', help='Create a new user')
    new_user.add_argument('--username', required=True, help='Username for Guacamole')
    new_user.add_argument('--password', required=True, help='Password for Guacamole user')
    new_user.add_argument('--group', help='Group to add user to')
    new_user.add_argument('--vnc-host', required=True, help='VNC server hostname/IP')
    new_user.add_argument('--vnc-port', required=True, help='VNC server port')
    new_user.add_argument('--vnc-password', required=True, help='VNC server password')

    # User list command
    user_subparsers.add_parser('list', help='List all users')

    # NEW: User delete command
    del_user = user_subparsers.add_parser('del', help='Delete a user')
    del_user.add_argument('--username', required=True, help='Username to delete')

def setup_group_subcommands(subparsers):
    group_parser = subparsers.add_parser('group', help='Manage Guacamole groups')
    group_subparsers = group_parser.add_subparsers(dest='group_command', help='Group commands')

    # Group new command
    new_group = group_subparsers.add_parser('new', help='Create a new group')
    new_group.add_argument('--name', required=True, help='Group name')

    # Group list command
    group_subparsers.add_parser('list', help='List all groups')

    # Group delete command
    del_group = group_subparsers.add_parser('del', help='Delete a group')
    del_group.add_argument('--name', required=True, help='Group name to delete')

def setup_conn_subcommands(subparsers):
    conn_parser = subparsers.add_parser('conn', help='Manage VNC connections')
    conn_subparsers = conn_parser.add_subparsers(dest='conn_command', help='Connection commands')

    # Connection new command
    new_conn = conn_subparsers.add_parser('new', help='Create a new VNC connection')
    new_conn.add_argument('--name', required=True, help='Connection name')
    new_conn.add_argument('--hostname', required=True, help='VNC server hostname/IP')
    new_conn.add_argument('--port', required=True, help='VNC server port')
    new_conn.add_argument('--vnc-password', required=True, help='VNC server password')
    new_conn.add_argument('--group', help='Group to grant access to')

    # Connection list command
    conn_subparsers.add_parser('list', help='List all VNC connections')

    # Connection delete command
    del_conn = conn_subparsers.add_parser('del', help='Delete a VNC connection')
    del_conn.add_argument('--name', required=True, help='Connection name to delete')

def main():
    parser = argparse.ArgumentParser(description='Manage Guacamole users, groups, and connections')
    parser.add_argument('--config', default='db_config.ini', help='Path to database config file')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    setup_user_subcommands(subparsers)
    setup_group_subcommands(subparsers)
    setup_conn_subcommands(subparsers)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'user' and not args.user_command:
        subparsers.choices['user'].print_help()
        sys.exit(1)

    if args.command == 'group' and not args.group_command:
        subparsers.choices['group'].print_help()
        sys.exit(1)
        
    if args.command == 'conn' and not args.conn_command:
        subparsers.choices['conn'].print_help()
        sys.exit(1)

    try:
        with GuacamoleDB(args.config) as guacdb:
            if args.command == 'user':
                if args.user_command == 'new':
                    connection_name = f"vnc-{args.username}"
                    guacdb.delete_existing_user(args.username)
                    guacdb.delete_existing_connection(connection_name)

                    guacdb.create_user(args.username, args.password)
                    connection_id = guacdb.create_vnc_connection(
                        connection_name, 
                        args.vnc_host, 
                        args.vnc_port, 
                        args.vnc_password
                    )
                    
                    guacdb.grant_connection_permission(args.username, 'USER', connection_id)

                    if args.group:
                        guacdb.add_user_to_group(args.username, args.group)
                        print(f"Added user '{args.username}' to group '{args.group}'")

                    print(f"Successfully created user '{args.username}' and VNC connection '{connection_name}'")

                elif args.user_command == 'list':
                    users_and_groups = guacdb.list_users_with_groups()
                    if users_and_groups:
                        print("\nExisting users:")
                        for user, groups in users_and_groups.items():
                            groups_str = ", ".join(groups) if groups else "no groups"
                            print(f"- {user} ({groups_str})")
                    else:
                        print("No users found")

                # NEW: User deletion command implementation
                elif args.user_command == 'del':
                    connection_name = f"vnc-{args.username}"
                    guacdb.delete_existing_connection(connection_name)
                    guacdb.delete_existing_user(args.username)
                    print(f"Successfully deleted user '{args.username}' and associated connection")

            elif args.command == 'group':
                if args.group_command == 'new':
                    guacdb.delete_existing_group(args.name)
                    guacdb.create_group(args.name)
                    print(f"Successfully created group '{args.name}'")

                elif args.group_command == 'list':
                    groups_and_users = guacdb.list_groups_with_users()
                    if groups_and_users:
                        print("\nExisting groups:")
                        for group, users in groups_and_users.items():
                            users_str = ", ".join(users) if users else "no users"
                            print(f"- {group} ({users_str})")
                    else:
                        print("No groups found")

                elif args.group_command == 'del':
                    guacdb.delete_existing_group(args.name)
                    print(f"Successfully deleted group '{args.name}'")

            elif args.command == 'conn':
                if args.conn_command == 'list':
                    connections = guacdb.list_connections()
                    if connections:
                        print("\nExisting VNC connections:")
                        for conn in connections:
                            name, host, port, password = conn
                            print(f"- {name}")
                            print(f"  Host: {host}:{port}")
                            print(f"  Password: {'*' * 8 if password else 'not set'}")
                    else:
                        print("No VNC connections found")
                        
                elif args.conn_command == 'del':
                    # Try exact match first
                    try:
                        guacdb.delete_existing_connection(args.name)
                        print(f"Successfully deleted connection '{args.name}'")
                    except Exception:
                        # Try matching connection name with port number
                        try:
                            guacdb.delete_existing_connection(f"{args.name}(7333)")
                            print(f"Successfully deleted connection '{args.name}(7333)'")
                        except Exception as e:
                            print(f"Error: Connection '{args.name}' not found")
                            sys.exit(1)
                    
                else:
                    print("Connection management is not yet implemented")
                    sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
