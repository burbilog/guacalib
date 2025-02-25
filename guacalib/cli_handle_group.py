import sys

def handle_group_command(args, guacdb):
    """Handle all group subcommands"""
    if args.group_command == 'new':
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
