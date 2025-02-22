#!/usr/bin/env python3

import argparse
import os
import sys
from guacalib import GuacamoleDB

def setup_user_subcommands(subparsers):
    user_parser = subparsers.add_parser('user', help='Manage Guacamole users')
    user_subparsers = user_parser.add_subparsers(dest='user_command', help='User commands')

    # User new command
    new_user = user_subparsers.add_parser('new', help='Create a new user')
    new_user.add_argument('--name', required=True, help='Username for Guacamole')
    new_user.add_argument('--password', required=True, help='Password for Guacamole user')
    new_user.add_argument('--group', help='Comma-separated list of groups to add user to')

    # User list command
    user_subparsers.add_parser('list', help='List all users')

    # User exists command
    exists_user = user_subparsers.add_parser('exists', help='Check if a user exists')
    exists_user.add_argument('--name', required=True, help='Username to check')

    # User delete command
    del_user = user_subparsers.add_parser('del', help='Delete a user')
    del_user.add_argument('--name', required=True, help='Username to delete')

def setup_group_subcommands(subparsers):
    group_parser = subparsers.add_parser('group', help='Manage Guacamole groups')
    group_subparsers = group_parser.add_subparsers(dest='group_command', help='Group commands')

    # Group new command
    new_group = group_subparsers.add_parser('new', help='Create a new group')
    new_group.add_argument('--name', required=True, help='Group name')

    # Group list command
    group_subparsers.add_parser('list', help='List all groups')

    # Group exists command
    exists_group = group_subparsers.add_parser('exists', help='Check if a group exists')
    exists_group.add_argument('--name', required=True, help='Group name to check')

    # Group delete command
    del_group = group_subparsers.add_parser('del', help='Delete a group')
    del_group.add_argument('--name', required=True, help='Group name to delete')

def setup_dump_subcommand(subparsers):
    subparsers.add_parser('dump', help='Dump all groups, users and connections in YAML format')

def setup_version_subcommand(subparsers):
    subparsers.add_parser('version', help='Show version information')

def setup_vconn_subcommands(subparsers):
    conn_parser = subparsers.add_parser('vconn', help='Manage VNC connections')
    conn_subparsers = conn_parser.add_subparsers(dest='vconn_command', help='Connection commands')

    # Connection new command
    new_conn = conn_subparsers.add_parser('new', help='Create a new VNC connection')
    new_conn.add_argument('--name', required=True, help='Connection name')
    new_conn.add_argument('--hostname', required=True, help='VNC server hostname/IP')
    new_conn.add_argument('--port', required=True, help='VNC server port')
    new_conn.add_argument('--vnc-password', required=True, help='VNC server password')
    new_conn.add_argument('--group', help='Comma-separated list of groups to grant access to')

    # Connection list command
    conn_subparsers.add_parser('list', help='List all VNC connections')

    # Connection exists command
    exists_conn = conn_subparsers.add_parser('exists', help='Check if a VNC connection exists')
    exists_conn.add_argument('--name', required=True, help='Connection name to check')

    # Connection delete command
    del_conn = conn_subparsers.add_parser('del', help='Delete a VNC connection')
    del_conn.add_argument('--name', required=True, help='Connection name to delete')

def main():
    parser = argparse.ArgumentParser(description='Manage Guacamole users, groups, and connections')
    parser.add_argument('--config', 
                       default=os.path.expanduser('~/.guacalib.ini'), 
                       help='Path to database config file (default: ~/.guacalib.ini)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    setup_user_subcommands(subparsers)
    setup_group_subcommands(subparsers)
    setup_vconn_subcommands(subparsers)
    setup_dump_subcommand(subparsers)
    setup_version_subcommand(subparsers)

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
        
    if args.command == 'vconn' and not args.vconn_command:
        subparsers.choices['vconn'].print_help()
        sys.exit(1)

    try:
        with GuacamoleDB(args.config, debug=args.debug) as guacdb:
            if args.command == 'user':
                if args.user_command == 'new':
                    # Check if user exists first
                    if guacdb.user_exists(args.name):
                        print(f"Error: User '{args.name}' already exists")
                        sys.exit(1)
                        
                    # Create new user
                    guacdb.create_user(args.name, args.password)

                    # Handle group memberships
                    groups = []
                    if args.group:
                        groups = [g.strip() for g in args.group.split(',')]
                        success = True
                        
                        for group in groups:
                            try:
                                guacdb.add_user_to_group(args.name, group)
                                guacdb.debug_print(f"Added user '{args.name}' to group '{group}'")
                            except Exception as e:
                                print(f"[-] Failed to add to group '{group}': {e}")
                                success = False
                        
                        if not success:
                            raise RuntimeError("Failed to add to one or more groups")

                    guacdb.debug_print(f"Successfully created user '{args.name}'")
                    if groups:
                        guacdb.debug_print(f"Group memberships: {', '.join(groups)}")

                elif args.user_command == 'list':
                    users_and_groups = guacdb.list_users_with_groups()
                    print("users:")
                    for user, groups in users_and_groups.items():
                        print(f"  {user}:")
                        print("    groups:")
                        for group in groups:
                            print(f"      - {group}")

                # NEW: User deletion command implementation
                elif args.user_command == 'del':
                    try:
                        guacdb.delete_existing_user(args.name)
                        guacdb.debug_print(f"Successfully deleted user '{args.name}'")
                    except ValueError as e:
                        print(f"Error: {e}")
                        sys.exit(1)
                    except Exception as e:
                        print(f"Error deleting user: {e}")
                        sys.exit(1)

                elif args.user_command == 'exists':
                    if guacdb.user_exists(args.name):
                        sys.exit(0)
                    else:
                        sys.exit(1)

            elif args.command == 'group':
                if args.group_command == 'new':
                    # Check if group exists first
                    if guacdb.group_exists(args.name):
                        print(f"Error: Group '{args.name}' already exists")
                        sys.exit(1)
                        
                    guacdb.create_group(args.name)
                    guacdb.debug_print(f"Successfully created group '{args.name}'")

                elif args.group_command == 'list':
                    groups_data = guacdb.list_groups_with_users_and_connections()
                    print("groups:")
                    for group, data in groups_data.items():
                        print(f"  {group}:")
                        print("    users:")
                        for user in data['users']:
                            print(f"      - {user}")
                        print("    connections:")
                        for conn in data['connections']:
                            print(f"      - {conn}")

                elif args.group_command == 'del':
                    # Check if group exists first
                    if not guacdb.group_exists(args.name):
                        print(f"Error: Group '{args.name}' does not exist")
                        sys.exit(1)
                        
                    guacdb.delete_existing_group(args.name)
                    guacdb.debug_print(f"Successfully deleted group '{args.name}'")

                elif args.group_command == 'exists':
                    if guacdb.group_exists(args.name):
                        sys.exit(0)
                    else:
                        sys.exit(1)

            elif args.command == 'dump':
                # Get all data
                groups_data = guacdb.list_groups_with_users_and_connections()
                users_data = guacdb.list_users_with_groups()
                connections_data = guacdb.list_connections_with_groups()
        
                # Print groups
                print("groups:")
                for group, data in groups_data.items():
                    print(f"  {group}:")
                    print("    users:")
                    for user in data['users']:
                        print(f"      - {user}")
                    print("    connections:")
                    for conn in data['connections']:
                        print(f"      - {conn}")
        
                # Print users
                print("users:")
                for user, groups in users_data.items():
                    print(f"  {user}:")
                    print("    groups:")
                    for group in groups:
                        print(f"      - {group}")
        
                # Print connections
                print("vnc-connections:")
                for conn in connections_data:
                    name, host, port, groups = conn
                    print(f"  {name}:")
                    print(f"    hostname: {host}")
                    print(f"    port: {port}")
                    print("    groups:")
                    for group in (groups.split(',') if groups else []):
                        print(f"      - {group}")

            elif args.command == 'version':
                from guacalib import VERSION
                print(f"gcmanager version {VERSION}")
                
            elif args.command == 'vconn':
                if args.vconn_command == 'list':
                    connections = guacdb.list_connections_with_groups()
                    print("connections:")
                    for conn in connections:
                        name, host, port, groups = conn
                        print(f"  {name}:")
                        print(f"    hostname: {host}")
                        print(f"    port: {port}")
                        print("    groups:")
                        for group in (groups.split(',') if groups else []):
                            print(f"      - {group}")
                        
                elif args.vconn_command == 'new':
                    try:
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
                                    guacdb.debug_print(f"Granted access to group '{group}'")
                                except Exception as e:
                                    print(f"[-] Failed to grant access to group '{group}': {e}")
                                    success = False
                            
                            if not success:
                                raise RuntimeError("Failed to grant access to one or more groups")
                        
                        guacdb.debug_print(f"Successfully created VNC connection '{args.name}'")
                        
                    except Exception as e:
                        print(f"Error creating connection: {e}")
                        sys.exit(1)

                elif args.vconn_command == 'del':
                    try:
                        # Try exact match first
                        guacdb.delete_existing_connection(args.name)
                    except Exception as e:
                        print(f"Error deleting connection: {e}")
                        sys.exit(1)

                elif args.vconn_command == 'exists':
                    if guacdb.connection_exists(args.name):
                        sys.exit(0)
                    else:
                        sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
