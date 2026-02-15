from guacalib import GuacamoleDB


def handle_dump_command(guacdb: GuacamoleDB) -> None:
    """Handle dump command - fetch and format all Guacamole data in YAML format.

    This function directly uses the API instead of CLI handlers to avoid
    unnecessary argument parsing overhead.
    """

    # Print users with their groups
    users_and_groups = guacdb.list_users_with_usergroups()
    print("users:")
    for user, groups in users_and_groups.items():
        print(f"  {user}:")
        print("    usergroups:")
        for group in groups:
            print(f"      - {group}")

    # Print user groups with users and connections
    groups_data = guacdb.list_usergroups_with_users_and_connections()
    print("usergroups:")
    for group_name, data in groups_data.items():
        print(f"  {group_name}:")
        print("    users:")
        for user in data.get("users", []):
            print(f"      - {user}")
        print("    connections:")
        for conn in data.get("connections", []):
            print(f"      - {conn}")

    # Print connections with groups, parent, and permissions
    connections = guacdb.list_connections_with_conngroups_and_parents()
    print("connections:")
    for conn in connections:
        conn_id, name, protocol, host, port, groups, parent, user_permissions = conn
        print(f"  {name}:")
        print(f"    id: {conn_id}")
        print(f"    type: {protocol}")
        print(f"    hostname: {host}")
        print(f"    port: {port}")
        if parent:
            print(f"    parent: {parent}")
        print("    groups:")
        for group in groups.split(",") if groups else []:
            if group:
                print(f"      - {group}")
        if user_permissions:
            print("    permissions:")
            for user in user_permissions:
                print(f"      - {user}")

    # Print connection groups
    conngroups = guacdb.list_connection_groups()
    print("conngroups:")
    for group_name, data in conngroups.items():
        print(f"  {group_name}:")
        print(f"    id: {data['id']}")
        print(f"    parent: {data['parent']}")
        print("    connections:")
        for conn in data["connections"]:
            print(f"      - {conn}")
