def handle_dump_command(guacdb):
    """Handle dump command - fetch and format all Guacamole data in YAML format"""
    # Print user groups using existing list functionality
    from guacalib.cli_handle_usergroup import handle_usergroup_command
    from guacalib.cli_handle_conngroup import handle_conngroup_command
    
    # Create dummy args object for list commands
    class Args:
        def __init__(self):
            self.usergroup_command = 'list'
            self.conngroup_command = 'list'
    
    args = Args()
    
    # Print users
    users_data = guacdb.list_users_with_groups()
    print("users:")
    for user, groups in users_data.items():
        print(f"  {user}:")
        print("    groups:")
        for group in groups:
            print(f"      - {group}")
    
    # Print user groups
    handle_usergroup_command(args, guacdb)
    
    # Print connections
    connections_data = guacdb.list_connections_with_groups_and_parents()
    print("vnc-connections:")
    for conn in connections_data:
        name, host, port, groups, parent = conn
        print(f"  {name}:")
        print(f"    hostname: {host}")
        print(f"    port: {port}")
        print("    groups:")
        for group in (groups.split(',') if groups else []):
            print(f"      - {group}")
        print(f"    parent: {parent if parent else 'ROOT'}")
    
    # Print connection groups
    handle_conngroup_command(args, guacdb)
