import sys
from typing import Any

from guacalib.db import GuacamoleDB


def handle_user_command(args: Any, guacdb: GuacamoleDB) -> None:
    """Route user management commands to appropriate handler functions.

    This function serves as the main dispatcher for all user-related CLI commands,
    mapping command names to their corresponding handler functions and providing
    error handling for unknown commands.

    Args:
        args: Parsed command line arguments containing user_command attribute.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 1 if an unknown command is provided.
    """
    command_handlers = {
        "new": handle_user_new,
        "list": handle_user_list,
        "del": handle_user_delete,
        "exists": handle_user_exists,
        "modify": handle_user_modify,
    }

    handler = command_handlers.get(args.user_command)
    if handler:
        handler(args, guacdb)
    else:
        print(f"Unknown user command: {args.user_command}")
        sys.exit(1)


def handle_user_new(args: Any, guacdb: GuacamoleDB) -> None:
    """Create a new user with optional group assignments.

    Creates a new Guacamole user with the specified name and password,
    optionally assigning the user to one or more user groups. Validates
    that the user doesn't already exist and handles group assignment errors.

    Args:
        args: Parsed command line arguments containing name, password, and optional usergroup.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 1 if user already exists or group assignment fails.
        RuntimeError: Raised if user creation succeeds but group assignment partially fails.

    Note:
        If group assignment fails for some groups but succeeds for others, the user
        will still be created but the function will raise a RuntimeError to indicate
        partial failure.
    """
    if guacdb.user_exists(args.name):
        print(f"Error: User '{args.name}' already exists")
        sys.exit(1)

    guacdb.create_user(args.name, args.password)
    groups = []

    if args.usergroup:
        groups = [g.strip() for g in args.usergroup.split(",")]
        success = True

        for group in groups:
            try:
                guacdb.add_user_to_usergroup(args.name, group)
                guacdb.debug_print(f"Added user '{args.name}' to usergroup '{group}'")
            except Exception as e:
                print(f"[-] Failed to add to group '{group}': {e}")
                success = False

        if not success:
            raise RuntimeError("Failed to add to one or more groups")

    guacdb.debug_print(f"Successfully created user '{args.name}'")
    if groups:
        guacdb.debug_print(f"Group memberships: {', '.join(groups)}")


def handle_user_list(args: Any, guacdb: GuacamoleDB) -> None:
    """List all users with their group memberships.

    Retrieves and displays a comprehensive list of all Guacamole users
    along with their associated user group memberships in a hierarchical
    YAML-like format.

    Args:
        args: Parsed command line arguments (not used in this function).
        guacdb: GuacamoleDB instance for database operations.

    Note:
        The output format is:
        users:
          username:
            usergroups:
              - group1
              - group2
    """
    users_and_groups = guacdb.list_users_with_usergroups()
    print("users:")
    for user, groups in users_and_groups.items():
        print(f"  {user}:")
        print("    usergroups:")
        for group in groups:
            print(f"      - {group}")


def handle_user_delete(args: Any, guacdb: GuacamoleDB) -> None:
    """Delete an existing user from the Guacamole database.

    Removes a user and all associated data from the Guacamole database.
    Handles various error conditions including user not found and database errors.

    Args:
        args: Parsed command line arguments containing name of user to delete.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 1 if user deletion fails.
    """
    try:
        guacdb.delete_existing_user(args.name)
        guacdb.debug_print(f"Successfully deleted user '{args.name}'")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error deleting user: {e}")
        sys.exit(1)


def handle_user_exists(args: Any, guacdb: GuacamoleDB) -> None:
    """Check if a user exists in the Guacamole database.

    Performs an existence check for a specified username and exits with
    appropriate status codes for use in shell scripts and automation.

    Args:
        args: Parsed command line arguments containing name of user to check.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Exits with status 0 if user exists, status 1 if user does not exist.

    Example:
        >>> # Use in shell script
        >>> if guacaman user exists --name testuser; then
        >>>     echo "User exists"
        >>> else
        >>>     echo "User does not exist"
        >>> fi
    """
    if guacdb.user_exists(args.name):
        sys.exit(0)
    else:
        sys.exit(1)


def handle_user_modify(args: Any, guacdb: GuacamoleDB) -> None:
    """Modify user properties such as password or custom parameters.

    Supports modifying user passwords and setting custom user parameters.
    If no valid modification options are provided, displays help information
    including all available parameters and their descriptions.

    Args:
        args: Parsed command line arguments containing name, optional password, and set parameters.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 0 for help display or status 1 for errors.

    Note:
        The --set parameter expects format "parameter=value" and supports all
        parameters defined in guacdb.USER_PARAMETERS. If called without valid
        modification options, displays a comprehensive help table.
    """
    if not args.name or (not args.set and not args.password):
        print(
            "Usage: guacaman user modify --name USERNAME [--set PARAMETER=VALUE] [--password NEW_PASSWORD]"
        )
        print("\nAllowed parameters:")
        print("-------------------")
        max_param_len = max(len(param) for param in guacdb.USER_PARAMETERS.keys())
        max_type_len = max(
            len(info["type"]) for info in guacdb.USER_PARAMETERS.values()
        )

        print(
            f"{'PARAMETER':<{max_param_len+2}} {'TYPE':<{max_type_len+2}} {'DEFAULT':<10} DESCRIPTION"
        )
        print(f"{'-'*(max_param_len+2)} {'-'*(max_type_len+2)} {'-'*10} {'-'*40}")

        for param, info in sorted(guacdb.USER_PARAMETERS.items()):
            print(
                f"{param:<{max_param_len+2}} {info['type']:<{max_type_len+2}} {info['default']:<10} {info['description']}"
            )

        print("\nExample usage:")
        print("  guacaman user modify --name john.doe --set disabled=1")
        print(
            '  guacaman user modify --name john.doe --set "organization=Example Corp"'
        )
        sys.exit(0)

    try:
        if not guacdb.user_exists(args.name):
            print(f"Error: User '{args.name}' does not exist")
            sys.exit(1)

        if args.password:
            guacdb.change_user_password(args.name, args.password)
            guacdb.debug_print(f"Successfully changed password for user '{args.name}'")

        if args.set:
            if "=" not in args.set:
                print("Error: --set must be in format 'parameter=value'")
                sys.exit(1)

            param_name, param_value = args.set.split("=", 1)
            param_name = param_name.strip()
            param_value = param_value.strip()

            guacdb.modify_user(args.name, param_name, param_value)
            guacdb.debug_print(
                f"Successfully modified user '{args.name}': {param_name}={param_value}"
            )

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error modifying user: {e}")
        sys.exit(1)
