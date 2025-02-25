import sys

def handle_conngroup_command(args, guacdb):
    """Handle all conngroup subcommands"""
    if args.conngroup_command == 'new':
        try:
            # Check if group already exists
            groups = guacdb.list_connection_groups()
            if args.name in groups:
                print(f"Error: Connection group '{args.name}' already exists")
                sys.exit(1)
                
            guacdb.create_connection_group(args.name, args.parent)
            # Explicitly commit the transaction
            guacdb.conn.commit()
            print(f"Successfully created connection group: {args.name}")
            sys.exit(0)
        except Exception as e:
            # Rollback on error
            guacdb.conn.rollback()
            print(f"Error creating connection group: {e}")
            sys.exit(1)

    elif args.conngroup_command == 'list':
        groups = guacdb.list_connection_groups()
        print("conngroups:")
        for group_name, data in groups.items():
            print(f"  {group_name}:")
            print(f"    parent: {data['parent']}")
            print("    connections:")
            for conn in data['connections']:
                print(f"      - {conn}")
        sys.exit(0)

    elif args.conngroup_command == 'exists':
        if guacdb.connection_group_exists(args.name):
            print(f"Connection group '{args.name}' exists")
            sys.exit(0)
        else:
            print(f"Connection group '{args.name}' does not exist")
            sys.exit(1)

    elif args.conngroup_command == 'del':
        try:
            # Check if group exists
            groups = guacdb.list_connection_groups()
            if args.name not in groups:
                print(f"Error: Connection group '{args.name}' does not exist")
                sys.exit(1)
                
            # Delete the group
            guacdb.delete_connection_group(args.name)
            print(f"Successfully deleted connection group: {args.name}")
            sys.exit(0)
        except Exception as e:
            print(f"Error deleting connection group: {e}")
            sys.exit(1)

    elif args.conngroup_command == 'modify':
        print(f"Modifying connection group: {args.name}")
        if args.addconn:
            print(f"Adding connection: {args.addconn}")
            # TODO: Implement connection addition
        if args.rmconn:
            print(f"Removing connection: {args.rmconn}")
            # TODO: Implement connection removal
        if args.set_parent_conngroup:
            print(f"Setting parent connection group: {args.set_parent_conngroup}")
            # TODO: Implement parent connection group setting
        sys.exit(0)
