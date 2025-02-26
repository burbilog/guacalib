import sys

def handle_usergroup_command(args, guacdb):
    """Handle all usergroup subcommands"""
    if args.usergroup_command == 'new':
        if guacdb.usergroup_exists(args.name):
            print(f"Error: Group '{args.name}' already exists")
            sys.exit(1)
            
        guacdb.create_usergroup(args.name)
        guacdb.debug_print(f"Successfully created group '{args.name}'")

    elif args.usergroup_command == 'list':
        groups_data = guacdb.list_usergroups_with_users_and_connections()
        print("usergroups:")
        for group, data in groups_data.items():
            print(f"  {group}:")
            print("    users:")
            for user in data['users']:
                print(f"      - {user}")
            print("    connections:")
            for conn in data['connections']:
                print(f"      - {conn}")

    elif args.usergroup_command == 'del':
        if not guacdb.usergroup_exists(args.name):
            print(f"Error: Group '{args.name}' does not exist")
            sys.exit(1)
            
        guacdb.delete_existing_usergroup(args.name)
        guacdb.debug_print(f"Successfully deleted user group '{args.name}'")

    elif args.usergroup_command == 'exists':
        if guacdb.usergroup_exists(args.name):
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.usergroup_command == 'modify':
        if not guacdb.usergroup_exists(args.name):
            print(f"Error: Group '{args.name}' does not exist")
            sys.exit(1)

        if args.adduser:
            if not guacdb.user_exists(args.adduser):
                print(f"Error: User '{args.adduser}' does not exist")
                sys.exit(1)
            guacdb.add_user_to_usergroup(args.adduser, args.name)

        if args.rmuser:
            if not guacdb.user_exists(args.rmuser):
                print(f"Error: User '{args.rmuser}' does not exist")
                sys.exit(1)
            guacdb.remove_user_from_usergroup(args.rmuser, args.name)
