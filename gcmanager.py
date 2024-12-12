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

def main():
    parser = argparse.ArgumentParser(description='Manage Guacamole users, groups, and connections')
    parser.add_argument('--config', default='db_config.ini', help='Path to database config file')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    setup_user_subcommands(subparsers)
    setup_group_subcommands(subparsers)

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
                    users = guacdb.list_users()
                    if users:
                        print("\nExisting users:")
                        for user in users:
                            print(f"- {user}")
                    else:
                        print("No users found")

            elif args.command == 'group':
                if args.group_command == 'new':
                    guacdb.delete_existing_group(args.name)
                    guacdb.create_group(args.name)
                    print(f"Successfully created group '{args.name}'")

                elif args.group_command == 'list':
                    groups = guacdb.list_groups()
                    if groups:
                        print("\nExisting groups:")
                        for group in groups:
                            print(f"- {group}")
                    else:
                        print("No groups found")

                elif args.group_command == 'del':
                    guacdb.delete_existing_group(args.name)
                    print(f"Successfully deleted group '{args.name}'")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
