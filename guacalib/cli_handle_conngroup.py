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
            guacdb.debug_print(f"Successfully created connection group: {args.name}")
            sys.exit(0)
        except Exception as e:
            # Rollback on error
            guacdb.conn.rollback()
            print(f"Error creating connection group: {e}")
            sys.exit(1)

    elif args.conngroup_command == 'list':
        # Check if specific ID is requested
        if hasattr(args, 'id') and args.id:
            # Get specific connection group by ID
            groups = guacdb.get_connection_group_by_id(args.id)
            if not groups:
                print(f"Connection group with ID {args.id} not found")
                sys.exit(1)
        else:
            # Get all connection groups
            groups = guacdb.list_connection_groups()
        
        print("conngroups:")
        for group_name, data in groups.items():
            print(f"  {group_name}:")
            print(f"    id: {data['id']}")
            print(f"    parent: {data['parent']}")
            print("    connections:")
            for conn in data['connections']:
                print(f"      - {conn}")
        sys.exit(0)

    elif args.conngroup_command == 'exists':
        try:
            if hasattr(args, 'id') and args.id is not None:
                # Validate ID format
                guacdb.validate_positive_id(args.id, "Connection group")
                # Check if connection group exists by ID
                name = guacdb.get_connection_group_name_by_id(args.id)
                if name:
                    guacdb.debug_print(f"Connection group with ID '{args.id}' exists: {name}")
                    sys.exit(0)
                else:
                    guacdb.debug_print(f"Connection group with ID '{args.id}' does not exist")
                    sys.exit(1)
            else:
                # Use name-based lookup
                if guacdb.connection_group_exists(args.name):
                    guacdb.debug_print(f"Connection group '{args.name}' exists")
                    sys.exit(0)
                else:
                    guacdb.debug_print(f"Connection group '{args.name}' does not exist")
                    sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.conngroup_command == 'del':
        try:
            group_name = None
            if hasattr(args, 'id') and args.id is not None:
                # Validate ID format
                guacdb.validate_positive_id(args.id, "Connection group")
                # Get group name by ID
                group_name = guacdb.get_connection_group_name_by_id(args.id)
                if not group_name:
                    print(f"Error: Connection group with ID '{args.id}' does not exist")
                    sys.exit(1)
            else:
                # Use name-based deletion
                group_name = args.name
                # Check if group exists
                groups = guacdb.list_connection_groups()
                if group_name not in groups:
                    print(f"Error: Connection group '{group_name}' does not exist")
                    sys.exit(1)
                
            # Delete the group
            guacdb.delete_connection_group(group_name)
            guacdb.debug_print(f"Successfully deleted connection group: {group_name}")
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error deleting connection group: {e}")
            sys.exit(1)

    elif args.conngroup_command == 'modify':
        try:
            group_name = None
            if hasattr(args, 'id') and args.id is not None:
                # Validate ID format
                guacdb.validate_positive_id(args.id, "Connection group")
                # Get group name by ID
                group_name = guacdb.get_connection_group_name_by_id(args.id)
                if not group_name:
                    print(f"Error: Connection group with ID '{args.id}' does not exist")
                    sys.exit(1)
            else:
                # Use name-based modification
                group_name = args.name
                
            if args.parent is not None:
                guacdb.debug_print(f"Setting parent connection group: {args.parent}")
                guacdb.modify_connection_group_parent(group_name=group_name, new_parent_name=args.parent)
                guacdb.conn.commit()  # Explicitly commit the transaction
                print(f"Successfully set parent group for '{group_name}' to '{args.parent}'")
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            guacdb.conn.rollback()  # Rollback on error
            print(f"Error modifying connection group: {e}")
            sys.exit(1)
