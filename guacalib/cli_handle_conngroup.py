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
        # Validate --id if provided
        if hasattr(args, 'id') and args.id is not None:
            if args.id <= 0:
                print("Error: Connection group ID must be a positive integer greater than 0")
                sys.exit(1)
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
            # Rely on database layer validation via resolvers
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
        try:
            # Rely on database layer validation via resolvers
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
        try:
            # Rely on database layer validation via resolvers
            # Get group name for display purposes (resolvers handle the actual lookup)
            if hasattr(args, 'id') and args.id is not None:
                # For ID-based operations, get name for display
                group_name = guacdb.get_connection_group_name_by_id(args.id)
                if not group_name:
                    print(f"Error: Connection group with ID {args.id} not found")
                    sys.exit(1)
            else:
                group_name = args.name
                
            # Handle parent modification
            if args.parent is not None:
                guacdb.debug_print(f"Setting parent connection group: {args.parent}")
                if hasattr(args, 'id') and args.id is not None:
                    guacdb.modify_connection_group_parent(group_id=args.id, new_parent_name=args.parent)
                else:
                    guacdb.modify_connection_group_parent(group_name=args.name, new_parent_name=args.parent)
                guacdb.conn.commit()  # Explicitly commit the transaction
                print(f"Successfully set parent group for '{group_name}' to '{args.parent}'")

            # Handle connection addition/removal
            connection_modified = False

            if hasattr(args, 'addconn_by_name') and args.addconn_by_name is not None:
                guacdb.debug_print(f"Adding connection by name: {args.addconn_by_name}")
                guacdb.modify_connection_parent_group(connection_name=args.addconn_by_name, group_name=group_name)
                connection_modified = True
                print(f"Added connection '{args.addconn_by_name}' to group '{group_name}'")

            elif hasattr(args, 'addconn_by_id') and args.addconn_by_id is not None:
                guacdb.debug_print(f"Adding connection by ID: {args.addconn_by_id}")
                # Get connection name for display
                conn_name = guacdb.get_connection_name_by_id(args.addconn_by_id)
                if not conn_name:
                    print(f"Error: Connection with ID {args.addconn_by_id} not found")
                    sys.exit(1)
                guacdb.modify_connection_parent_group(connection_id=args.addconn_by_id, group_name=group_name)
                connection_modified = True
                print(f"Added connection '{conn_name}' to group '{group_name}'")

            elif hasattr(args, 'rmconn_by_name') and args.rmconn_by_name is not None:
                guacdb.debug_print(f"Removing connection by name: {args.rmconn_by_name}")
                guacdb.modify_connection_parent_group(connection_name=args.rmconn_by_name, group_name=None)
                connection_modified = True
                print(f"Removed connection '{args.rmconn_by_name}' from group '{group_name}'")

            elif hasattr(args, 'rmconn_by_id') and args.rmconn_by_id is not None:
                guacdb.debug_print(f"Removing connection by ID: {args.rmconn_by_id}")
                # Get connection name for display
                conn_name = guacdb.get_connection_name_by_id(args.rmconn_by_id)
                if not conn_name:
                    print(f"Error: Connection with ID {args.rmconn_by_id} not found")
                    sys.exit(1)
                guacdb.modify_connection_parent_group(connection_id=args.rmconn_by_id, group_name=None)
                connection_modified = True
                print(f"Removed connection '{conn_name}' from group '{group_name}'")

            # Validate that either parent or connection operation was specified
            if args.parent is None and not connection_modified:
                print("Error: No modification specified. Use --parent, --addconn-*, or --rmconn-*")
                sys.exit(2)

            # Commit connection operations
            if connection_modified:
                guacdb.conn.commit()

            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            guacdb.conn.rollback()  # Rollback on error
            print(f"Error modifying connection group: {e}")
            sys.exit(1)
