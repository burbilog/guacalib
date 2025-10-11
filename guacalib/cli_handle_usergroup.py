import sys
from typing import Any

from guacalib.db import GuacamoleDB


def handle_usergroup_command(args: Any, guacdb: GuacamoleDB) -> None:
    """Handle all usergroup subcommands"""
    if args.usergroup_command == "new":
        if guacdb.usergroup_exists(args.name):
            print(f"Error: Group '{args.name}' already exists")
            sys.exit(1)

        guacdb.create_usergroup(args.name)
        guacdb.debug_print(f"Successfully created group '{args.name}'")

    elif args.usergroup_command == "list":
        groups_data = guacdb.list_usergroups_with_users_and_connections()
        print("usergroups:")
        for group, data in groups_data.items():
            print(f"  {group}:")
            print(f"    id: {data['id']}")
            print("    users:")
            for user in data["users"]:
                print(f"      - {user}")
            print("    connections:")
            for conn in data["connections"]:
                print(f"      - {conn}")

    elif args.usergroup_command == "del":
        # Validate exactly one selector provided
        from .cli import validate_selector

        validate_selector(args, "usergroup")

        if hasattr(args, "id") and args.id is not None:
            # Delete by ID using resolver
            group_name = guacdb.get_usergroup_name_by_id(args.id)
            guacdb.delete_existing_usergroup_by_id(args.id)
            guacdb.debug_print(
                f"Successfully deleted user group '{group_name}' (ID: {args.id})"
            )
        else:
            # Delete by name (original behavior)
            if not guacdb.usergroup_exists(args.name):
                print(f"Error: Group '{args.name}' does not exist")
                sys.exit(1)
            guacdb.delete_existing_usergroup(args.name)
            guacdb.debug_print(f"Successfully deleted user group '{args.name}'")

    elif args.usergroup_command == "exists":
        # Validate exactly one selector provided
        from .cli import validate_selector

        validate_selector(args, "usergroup")

        if hasattr(args, "id") and args.id is not None:
            # Check existence by ID using resolver
            if guacdb.usergroup_exists_by_id(args.id):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            # Check existence by name (original behavior)
            if guacdb.usergroup_exists(args.name):
                sys.exit(0)
            else:
                sys.exit(1)

    elif args.usergroup_command == "modify":
        # Validate exactly one selector provided
        from .cli import validate_selector

        validate_selector(args, "usergroup")

        if hasattr(args, "id") and args.id is not None:
            # Modify by ID using resolver
            group_name = guacdb.get_usergroup_name_by_id(args.id)
            group_id = args.id
        else:
            # Modify by name (original behavior)
            if not guacdb.usergroup_exists(args.name):
                print(f"Error: Group '{args.name}' does not exist")
                sys.exit(1)
            group_name = args.name
            group_id = guacdb.resolve_usergroup_id(group_name=group_name)

        if args.adduser:
            if not guacdb.user_exists(args.adduser):
                print(f"Error: User '{args.adduser}' does not exist")
                sys.exit(1)
            guacdb.add_user_to_usergroup(args.adduser, group_name)

        if args.rmuser:
            if not guacdb.user_exists(args.rmuser):
                print(f"Error: User '{args.rmuser}' does not exist")
                sys.exit(1)
            guacdb.remove_user_from_usergroup(args.rmuser, group_name)
