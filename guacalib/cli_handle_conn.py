import sys

def handle_conn_command(args, guacdb):
    command_handlers = {
        'new': handle_conn_new,
        'list': handle_conn_list,
        'del': handle_conn_delete,
        'exists': handle_conn_exists,
        'modify': handle_conn_modify,
    }
    
    handler = command_handlers.get(args.conn_command)
    if handler:
        handler(args, guacdb)
    else:
        print(f"Unknown connection command: {args.conn_command}")
        sys.exit(1)

def handle_conn_list(args, guacdb):
    # Get connections with both groups and parent group info
    connections = guacdb.list_connections_with_groups_and_parents()
    print("connections:")
    for conn in connections:
        name, protocol, host, port, groups, parent = conn
        print(f"  {name}:")
        print(f"    type: {protocol}")
        print(f"    hostname: {host}")
        print(f"    port: {port}")
        if parent:
            print(f"    parent: {parent}")
        print("    groups:")
        for group in (groups.split(',') if groups else []):
            print(f"      - {group}")

def handle_conn_new(args, guacdb):
    try:
        connection_id = None
        
        connection_id = guacdb.create_connection(
            args.type,
            args.name,
            args.hostname,
            args.port,
            args.password
        )
        guacdb.debug_print(f"Successfully created connection '{args.name}'")
            
        if connection_id and args.usergroup:
            groups = [g.strip() for g in args.usergroup.split(',')]
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

def handle_conn_delete(args, guacdb):
    try:
        guacdb.delete_existing_connection(args.name)
    except Exception as e:
        print(f"Error deleting connection: {e}")
        sys.exit(1)

def handle_conn_exists(args, guacdb):
    if guacdb.connection_exists(args.name):
        sys.exit(0)
    else:
        sys.exit(1)
        
def handle_conn_modify(args, guacdb):
    """Handle the connection modify command"""
    if not args.name or (not args.set and args.parent is None):
        # Print help information about modifiable parameters
        print("Usage: guacaman conn modify --name <connection_name> [--set <param=value> ...] [--parent CONNGROUP]")
        print("\nModification options:")
        print("  --set: Modify connection parameters")
        print("  --parent: Set parent connection group (use empty string to remove group)")
        print("\nModifiable connection parameters:")
        print("\nParameters in guacamole_connection table:")
        for param, info in sorted(guacdb.CONNECTION_PARAMETERS.items()):
            if info['table'] == 'connection':
                print(f"  {param}: {info['description']} (type: {info['type']}, default: {info['default']})")
        
        print("\nParameters in guacamole_connection_parameter table:")
        for param, info in sorted(guacdb.CONNECTION_PARAMETERS.items()):
            if info['table'] == 'parameter':
                print(f"  {param}: {info['description']} (type: {info['type']}, default: {info['default']})")
        
        sys.exit(1)
    
    try:
        # Handle parent group modification
        if args.parent is not None:
            try:
                # Convert empty string to None to unset parent group
                parent_group = args.parent if args.parent != "" else None
                guacdb.modify_connection_parent_group(args.name, parent_group)
                guacdb.debug_print(f"Successfully set parent group to '{args.parent}' for connection '{args.name}'")
            except Exception as e:
                print(f"Error setting parent group: {e}")
                sys.exit(1)
        # Process each --set argument (if any)
        for param_value in args.set or []:
            if '=' not in param_value:
                print(f"Error: Invalid format for --set. Must be param=value, got: {param_value}")
                sys.exit(1)
                
            param, value = param_value.split('=', 1)
            guacdb.debug_print(f"Modifying connection '{args.name}': setting {param}={value}")
            
            try:
                guacdb.modify_connection(args.name, param, value)
                guacdb.debug_print(f"Successfully updated {param} for connection '{args.name}'")
            except ValueError as e:
                print(f"Error: {str(e)}")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error modifying connection: {e}")
        sys.exit(1)
