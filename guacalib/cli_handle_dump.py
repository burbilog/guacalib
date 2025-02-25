def handle_dump_command(guacdb):
    """Handle dump command - fetch and format all Guacamole data in YAML format"""
    # Get all data
    groups_data = guacdb.list_groups_with_users_and_connections()
    users_data = guacdb.list_users_with_groups()
    connections_data = guacdb.list_connections_with_groups()

    # Print groups
    print("groups:")
    for group, data in groups_data.items():
        print(f"  {group}:")
        print("    users:")
        for user in data['users']:
            print(f"      - {user}")
        print("    connections:")
        for conn in data['connections']:
            print(f"      - {conn}")

    # Print users
    print("users:")
    for user, groups in users_data.items():
        print(f"  {user}:")
        print("    groups:")
        for group in groups:
            print(f"      - {group}")

    # Print connections
    print("vnc-connections:")
    for conn in connections_data:
        name, host, port, groups = conn
        print(f"  {name}:")
        print(f"    hostname: {host}")
        print(f"    port: {port}")
        print("    groups:")
        for group in (groups.split(',') if groups else []):
            print(f"      - {group}")
