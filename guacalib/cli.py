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
    new_user.add_argument('--type', choices=['vnc', 'rdp', 'ssh'], required=True, 
                         help='Type of connection for this user (vnc, rdp, ssh)')

    # User list command
    user_subparsers.add_parser('list', help='List all users')

    # User exists command
    exists_user = user_subparsers.add_parser('exists', help='Check if a user exists')
    exists_user.add_argument('--name', required=True, help='Username to check')

    # User delete command
    del_user = user_subparsers.add_parser('del', help='Delete a user')
    del_user.add_argument('--name', required=True, help='Username to delete')
    
    # User modify command
    modify_user = user_subparsers.add_parser('modify', help='Modify user parameters')
    modify_user.add_argument('--name', help='Username to modify')
    modify_user.add_argument('--set', help='Parameter to set in format param=value')

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

def setup_conn_subcommands(subparsers):
    conn_parser = subparsers.add_parser('conn', help='Manage connections')
    conn_subparsers = conn_parser.add_subparsers(dest='conn_command', help='Connection commands')

    # Connection new command
    new_conn = conn_subparsers.add_parser('new', help='Create a new connection')
    new_conn.add_argument('--name', required=True, help='Connection name')
    new_conn.add_argument('--type', choices=['vnc', 'rdp', 'ssh'], required=True, 
                         help='Type of connection (vnc, rdp, ssh)')
    new_conn.add_argument('--hostname', required=True, help='Server hostname/IP')
    new_conn.add_argument('--port', required=True, help='Server port')
    new_conn.add_argument('--vnc-password', help='VNC server password (required for VNC)')
    new_conn.add_argument('--group', help='Comma-separated list of groups to grant access to')

    # Connection list command
    conn_subparsers.add_parser('list', help='List all connections')

    # Connection exists command
    exists_conn = conn_subparsers.add_parser('exists', help='Check if a connection exists')
    exists_conn.add_argument('--name', required=True, help='Connection name to check')

    # Connection delete command
    del_conn = conn_subparsers.add_parser('del', help='Delete a connection')
    del_conn.add_argument('--name', required=True, help='Connection name to delete')

def main():
    parser = argparse.ArgumentParser(description='Manage Guacamole users, groups, and connections')
    parser.add_argument('--config', 
                       default=os.path.expanduser('~/.guacaman.ini'), 
                       help='Path to database config file (default: ~/.guacaman.ini)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    setup_user_subcommands(subparsers)
    setup_group_subcommands(subparsers)
    setup_conn_subcommands(subparsers)
    setup_dump_subcommand(subparsers)
    setup_version_subcommand(subparsers)

    args = parser.parse_args()

    def check_config_permissions(config_path):
        """Check config file has secure permissions"""
        if not os.path.exists(config_path):
            return  # Will be handled later by GuacamoleDB
            
        mode = os.stat(config_path).st_mode
        if mode & 0o077:  # Check if group/others have any permissions
            print(f"ERROR: Config file {config_path} has insecure permissions!")
            print("Required permissions: -rw------- (600)")
            print("Fix with: chmod 600", config_path)
            sys.exit(2)

    # Check permissions before doing anything
    check_config_permissions(args.config)

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
                        
                    # Handle connection type
                    if args.type == 'vnc':
                        guacdb.debug_print(f"User '{args.name}' created with VNC connection type")
                    elif args.type == 'rdp':
                        # TODO: Implement RDP connection handling
                        guacdb.debug_print(f"RDP connections not yet implemented")
                    elif args.type == 'ssh':
                        # TODO: Implement SSH connection handling
                        guacdb.debug_print(f"SSH connections not yet implemented")

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
                        
                elif args.user_command == 'modify':
                    # If no arguments provided, show the list of allowed parameters
                    if not args.name or not args.set:
                        print("Usage: guacaman user modify --name USERNAME --set PARAMETER=VALUE")
                        print("\nAllowed parameters:")
                        print("-------------------")
                        max_param_len = max(len(param) for param in guacdb.USER_PARAMETERS.keys())
                        max_type_len = max(len(info['type']) for info in guacdb.USER_PARAMETERS.values())
                        
                        # Print header
                        print(f"{'PARAMETER':<{max_param_len+2}} {'TYPE':<{max_type_len+2}} {'DEFAULT':<10} DESCRIPTION")
                        print(f"{'-'*(max_param_len+2)} {'-'*(max_type_len+2)} {'-'*10} {'-'*40}")
                        
                        # Print each parameter
                        for param, info in sorted(guacdb.USER_PARAMETERS.items()):
                            print(f"{param:<{max_param_len+2}} {info['type']:<{max_type_len+2}} {info['default']:<10} {info['description']}")
                        
                        print("\nExample usage:")
                        print("  guacaman user modify --name john.doe --set disabled=1")
                        print("  guacaman user modify --name john.doe --set \"organization=Example Corp\"")
                        sys.exit(0)
                    
                    try:
                        # Parse the parameter and value
                        if '=' not in args.set:
                            print("Error: --set must be in format 'parameter=value'")
                            sys.exit(1)
                            
                        param_name, param_value = args.set.split('=', 1)
                        param_name = param_name.strip()
                        param_value = param_value.strip()
                        
                        # Check if user exists
                        if not guacdb.user_exists(args.name):
                            print(f"Error: User '{args.name}' does not exist")
                            sys.exit(1)
                        
                        # Modify the user parameter
                        guacdb.modify_user(args.name, param_name, param_value)
                        guacdb.debug_print(f"Successfully modified user '{args.name}': {param_name}={param_value}")
                        
                    except ValueError as e:
                        print(f"Error: {e}")
                        sys.exit(1)
                    except Exception as e:
                        print(f"Error modifying user: {e}")
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
                print(f"guacaman version {VERSION}")
                
            elif args.command == 'conn':
                if args.conn_command == 'list':
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
                        
                elif args.conn_command == 'new':
                    try:
                        connection_id = None
                        
                        # Handle different connection types
                        if args.type == 'vnc':
                            if not args.vnc_password:
                                print("Error: --vnc-password is required for VNC connections")
                                sys.exit(1)
                                
                            # Create new VNC connection
                            connection_id = guacdb.create_vnc_connection(
                                args.name,
                                args.hostname,
                                args.port,
                                args.vnc_password
                            )
                            guacdb.debug_print(f"Successfully created VNC connection '{args.name}'")
                            
                        elif args.type == 'rdp':
                            # TODO: Implement RDP connection creation
                            print("RDP connections not yet implemented")
                            sys.exit(1)
                            
                        elif args.type == 'ssh':
                            # TODO: Implement SSH connection creation
                            print("SSH connections not yet implemented")
                            sys.exit(1)
                        
                        # Grant to groups if specified and connection was created
                        if connection_id and args.group:
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

                elif args.conn_command == 'exists':
                    if guacdb.connection_exists(args.name):
                        sys.exit(0)
                    else:
                        sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
