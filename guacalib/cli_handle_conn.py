import sys

def handle_conn_command(args, guacdb):
    command_handlers = {
        'new': handle_conn_new,
        'list': handle_conn_list,
        'del': handle_conn_delete,
        'exists': handle_conn_exists,
    }
    
    handler = command_handlers.get(args.conn_command)
    if handler:
        handler(args, guacdb)
    else:
        print(f"Unknown connection command: {args.conn_command}")
        sys.exit(1)

def handle_conn_list(args, guacdb):
    connections = guacdb.list_connections_with_groups()
    print("connections:")
    for conn in connections:
        name, host, port, groups = conn
        print(f"  {name}:")
        print(f"    hostname: {host}")
        print(f"    port: {port}")
        print("    groups:")
        for group in (groups.split(',') if groups else []):
            print(f"      - {group}")

def handle_conn_new(args, guacdb):
    try:
        connection_id = None
        
        if args.type == 'vnc':
            if not args.vnc_password:
                print("Error: --vnc-password is required for VNC connections")
                sys.exit(1)
                
            connection_id = guacdb.create_vnc_connection(
                args.name,
                args.hostname,
                args.port,
                args.vnc_password
            )
            guacdb.debug_print(f"Successfully created VNC connection '{args.name}'")
            
        elif args.type == 'rdp':
            print("RDP connections not yet implemented")
            sys.exit(1)
            
        elif args.type == 'ssh':
            print("SSH connections not yet implemented")
            sys.exit(1)
        
        if connection_id and args.group:
            groups = [g.strip() for g in args.group.split(',')]
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
