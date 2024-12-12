#!/usr/bin/env python3

#!/usr/bin/env python3

import argparse
import sys
from gcmylib import GuacamoleDB

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

    # Group command - simplified
    group_parser = subparsers.add_parser('group', help='Manage groups')
    group_parser.add_argument('--name', required=True, help='Group name')

    # Common arguments
    parser.add_argument('--config', default='db_config.ini', help='Path to database config file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        with GuacamoleDB(args.config) as guacdb:
            if args.command == 'user':
                # Handle user creation
                connection_name = f"vnc-{args.username}"
                guacdb.delete_existing_user(args.username)
                guacdb.delete_existing_connection(connection_name)

                guacdb.create_user(args.username, args.password)
                connection_id = guacdb.create_vnc_connection(connection_name, 
                                                          args.vnc_host, 
                                                          args.vnc_port, 
                                                          args.vnc_password)
                
                guacdb.grant_connection_permission(args.username, 'USER', connection_id)

                if args.group:
                    guacdb.add_user_to_group(args.username, args.group)
                    print(f"Added user '{args.username}' to group '{args.group}'")

                print(f"Successfully created user '{args.username}' and VNC connection '{connection_name}'")

            elif args.command == 'group':
                # Handle group creation - simplified
                guacdb.delete_existing_group(args.name)
                guacdb.create_group(args.name)
                print(f"Successfully created group '{args.name}'")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
