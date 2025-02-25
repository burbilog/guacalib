#!/usr/bin/env python3

import argparse
import os
import sys
from guacalib import GuacamoleDB
from guacalib.cli_handle_group import handle_group_command
from guacalib.cli_handle_dump import handle_dump_command
from guacalib.cli_handle_user import handle_user_command
from guacalib.cli_handle_conn import handle_conn_command

def setup_user_subcommands(subparsers):
    user_parser = subparsers.add_parser('user', help='Manage Guacamole users')
    user_subparsers = user_parser.add_subparsers(dest='user_command', help='User commands')

    # User new command
    new_user = user_subparsers.add_parser('new', help='Create a new user')
    new_user.add_argument('--name', required=True, help='Username for Guacamole')
    new_user.add_argument('--password', required=True, help='Password for Guacamole user')
    new_user.add_argument('--group', help='Comma-separated list of groups to add user to')
    #new_user.add_argument('--type', choices=['vnc', 'rdp', 'ssh'], required=True, 
    #                     help='Type of connection for this user (vnc, rdp, ssh)')

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
    
    # Connection modify command
    modify_conn = conn_subparsers.add_parser('modify', help='Modify connection parameters')
    modify_conn.add_argument('--name', help='Connection name to modify')
    modify_conn.add_argument('--set', action='append', help='Parameter to set in format param=value (can be used multiple times)')
    modify_conn.add_argument('--set-parent-group', 
                           help='Set parent connection group name (use empty string to unset group)')

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
                handle_user_command(args, guacdb)

            elif args.command == 'group':
                handle_group_command(args, guacdb)

            elif args.command == 'dump':
                handle_dump_command(guacdb)

            elif args.command == 'version':
                from guacalib import VERSION
                print(f"guacaman version {VERSION}")
                
            elif args.command == 'conn':
                handle_conn_command(args, guacdb)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
