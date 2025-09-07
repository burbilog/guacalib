import sys

def validate_selector(args, entity_type="connection group"):
    """Validate exactly one of name or id is provided and validate ID format"""
    has_name = hasattr(args, 'name') and args.name is not None
    has_id = hasattr(args, 'id') and args.id is not None
    
    if not (has_name ^ has_id):
        print(f"Error: Exactly one of --name or --id must be provided for {entity_type}")
        sys.exit(1)
    
    # Validate ID format if ID is provided
    if has_id and args.id <= 0:
        print(f"Error: {entity_type.capitalize()} ID must be a positive integer greater than 0")
        sys.exit(1)

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
        # Validate exactly one selector provided
        validate_selector(args, "connection group")
        
        try:
            if hasattr(args, 'id') and args.id is not None:
                # Check if connection group exists by ID using resolver
                if guacdb.connection_group_exists(group_id=args.id):
                    guacdb.debug_print(f"Connection group with ID '{args.id}' exists")
                    sys.exit(0)
                else:
                    guacdb.debug_print(f"Connection group with ID '{args.id}' does not exist")
                    sys.exit(1)
            else:
                # Use name-based lookup
                if guacdb.connection_group_exists(group_name=args.name):
                    guacdb.debug_print(f"Connection group '{args.name}' exists")
                    sys.exit(0)
                else:
                    guacdb.debug_print(f"Connection group '{args.name}' does not exist")
                    sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error checking connection group existence: {e}")
            sys.exit(1)

    elif args.conngroup_command == 'del':
        # Validate exactly one selector provided
        validate_selector(args, "connection group")
        
        try:
            if hasattr(args, 'id') and args.id is not None:
                # Delete by ID using resolver
                guacdb.delete_connection_group(group_id=args.id)
            else:
                # Delete by name using resolver
                guacdb.delete_connection_group(group_name=args.name)
            guacdb.debug_print(f"Successfully deleted connection group")
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error deleting connection group: {e}")
            sys.exit(1)

    elif args.conngroup_command == 'modify':
        # Validate exactly one selector provided
        validate_selector(args, "connection group")
        
        try:
            # Get group name for display purposes (resolvers handle the actual lookup)
            if hasattr(args, 'id') and args.id is not None:
                # For ID-based operations, get name for display
                group_name = guacdb.get_connection_group_name_by_id(args.id)
                if not group_name:
                    print(f"Error: Connection group with ID {args.id} not found")
                    sys.exit(1)
            else:
                group_name = args.name
                
            if args.parent is not None:
                guacdb.debug_print(f"Setting parent connection group: {args.parent}")
                if hasattr(args, 'id') and args.id is not None:
                    guacdb.modify_connection_group_parent(group_id=args.id, new_parent_name=args.parent)
                else:
                    guacdb.modify_connection_group_parent(group_name=args.name, new_parent_name=args.parent)
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
