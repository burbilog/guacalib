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
    new_user.add_argument('--group', help='Comma-separated list of groups to add user to')

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
    new_conn.add_argument('--group', help='Comma-separated list of groups to grant access to')

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
                    guacdb.delete_existing_user(args.username)
                    guacdb.create_user(args.username, args.password)

                    if args.group:
                        groups = [g.strip() for g in args.group.split(',')]
                        success = True
                        
                        for group in groups:
                            try:
                                guacdb.add_user_to_group(args.username, group)
                                print(f"[+] Added user '{args.username}' to group '{group}'")
                            except Exception as e:
                                print(f"[-] Failed to add to group '{group}': {e}")
                                success = False
                        
                        if not success:
                            raise RuntimeError("Failed to add to one or more groups")

                    print(f"\n[+] Successfully created user '{args.username}'")
                    if groups:
                        print(f"    Group memberships: {', '.join(groups)}")

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
                        
                elif args.conn_command == 'new':
                    try:
                        # Delete existing connection if it exists
                        guacdb.delete_existing_connection(args.name)
                        
                        # Create new connection
                        connection_id = guacdb.create_vnc_connection(
                            args.name,
                            args.hostname,
                            args.port,
                            args.vnc_password
                        )
                        
                        # Grant to groups if specified
                        if args.group:
                            groups = [g.strip() for g in args.group.split(',')]
                            success = True
                            
                            for group in groups:
                                try:
                                    guacdb.grant_connection_permission(
                                        group,  # Direct group name
                                        'USER_GROUP', 
                                        connection_id,
                                        group_path=None  # No path nesting
                                    )
                                    print(f"[+] Granted access to group '{group}'")
                                except Exception as e:
                                    print(f"[-] Failed to grant access to group '{group}': {e}")
                                    success = False
                            
                            if not success:
                                raise RuntimeError("Failed to grant access to one or more groups")
                        
                        print(f"Successfully created VNC connection '{args.name}'")
                        
                    except Exception as e:
                        print(f"Error creating connection: {e}")
                        sys.exit(1)

                elif args.conn_command == 'del':
                    try:
                        # Try exact match first
                        guacdb.delete_existing_connection(args.name)
                    except Exception as e:
                        print(f"Error deleting connection: {e}")
                        sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
