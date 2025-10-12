import sys
from typing import Any

from guacalib.db import GuacamoleDB
from .logging_config import get_logger


def is_terminal() -> bool:
    """Check if stdout is a terminal (not piped or redirected).

    Utility function to determine if output is being displayed directly
    to a user in a terminal or being piped/redirected. Used to decide
    whether to use colored output or plain text.

    Returns:
        True if stdout is connected to a terminal, False if piped or redirected.
    """
    return sys.stdout.isatty()


# Initialize colors based on terminal
if is_terminal():
    VAR_COLOR = "\033[1;36m"  # Bright cyan
    RESET = "\033[0m"  # Reset color
else:
    VAR_COLOR = ""
    RESET = ""


def handle_conn_command(args: Any, guacdb: GuacamoleDB) -> None:
    """Route connection management commands to appropriate handler functions.

    This function serves as the main dispatcher for all connection-related CLI commands,
    mapping command names to their corresponding handler functions and providing
    error handling for unknown commands.

    Args:
        args: Parsed command line arguments containing conn_command attribute.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 1 if an unknown command is provided.
    """
    logger = get_logger('cli_handle_conn')

    command_handlers = {
        "new": handle_conn_new,
        "list": handle_conn_list,
        "del": handle_conn_delete,
        "exists": handle_conn_exists,
        "modify": handle_conn_modify,
    }

    handler = command_handlers.get(args.conn_command)
    if handler:
        logger.debug(f"Dispatching connection command: {args.conn_command}")
        handler(args, guacdb)
    else:
        logger.error(f"Unknown connection command: {args.conn_command}")
        print(f"Error: Unknown connection command: {args.conn_command}")
        sys.exit(1)


"""
def handle_conn_list(args, guacdb):
    # Get connections with both groups and parent group info
    connections = guacdb.list_connections_with_conngroups_and_parents()
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
"""


def handle_conn_list(args: Any, guacdb: GuacamoleDB) -> None:
    """List connections with detailed information including groups and permissions.

    Displays all connections or a specific connection by ID, showing protocol,
    hostname, port, parent group, associated groups, and individual user
    permissions in a hierarchical YAML-like format.

    Args:
        args: Parsed command line arguments containing optional ID for specific connection.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 1 if a specific connection ID is not found.

    Note:
        Output format includes connection ID, type, hostname, port, parent group,
        group memberships, and individual user permissions. Supports both
        listing all connections and displaying a specific connection by ID.
    """
    # Check if specific ID is requested
    if hasattr(args, "id") and args.id:
        # Get specific connection by ID
        connection = guacdb.get_connection_by_id(args.id)
        if not connection:
            print(f"Connection with ID {args.id} not found")
            sys.exit(1)
        connections = [connection]
    else:
        # Get all connections
        connections = guacdb.list_connections_with_conngroups_and_parents()

    print("connections:")
    for conn in connections:
        # Unpack connection info (now includes connection_id)
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
            if group:  # Skip empty group names
                print(f"      - {group}")

        # Add this section to show individual user permissions
        if user_permissions:
            print("    permissions:")
            for user in user_permissions:
                print(f"      - {user}")


def handle_conn_new(args: Any, guacdb: GuacamoleDB) -> None:
    """Create a new connection with optional group permissions.

    Creates a new Guacamole connection with the specified protocol, name,
    hostname, port, and optional password. Can also grant access to specified
    user groups during creation.

    Args:
        args: Parsed command line arguments containing type, name, hostname, port,
              optional password, and optional usergroup list.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 1 if connection creation fails.
        RuntimeError: Raised if connection creation succeeds but group permission
                     assignment partially fails.

    Note:
        Supports VNC, RDP, and SSH protocols. If user groups are specified,
        attempts to grant connection access to all listed groups. Partial failures
        in group assignment will raise an exception but the connection will still be created.
    """
    logger = get_logger('cli_handle_conn')

    logger.debug(f"Creating new connection: {args.name} (type: {args.type})")
    try:
        connection_id = None

        connection_id = guacdb.create_connection(
            args.type, args.name, args.hostname, args.port, args.password
        )
        logger.info(f"Connection '{args.name}' created successfully with ID: {connection_id}")
        guacdb.debug_print(f"Successfully created connection '{args.name}'")

        if connection_id and args.usergroup:
            groups = [g.strip() for g in args.usergroup.split(",")]
            logger.debug(f"Granting access to groups: {', '.join(groups)}")
            success = True

            for group in groups:
                try:
                    guacdb.grant_connection_permission(
                        group,  # Direct group name
                        "USER_GROUP",
                        connection_id,
                        group_path=None,  # No path nesting
                    )
                    logger.debug(f"Granted access to group '{group}' for connection '{args.name}'")
                    guacdb.debug_print(f"Granted access to group '{group}'")
                except Exception as e:
                    logger.error(f"Failed to grant access to group '{group}' for connection '{args.name}': {e}")
                    print(f"[-] Failed to grant access to group '{group}': {e}")
                    success = False

            if success:
                logger.info(f"Connection '{args.name}' granted access to groups: {', '.join(groups)}")
            else:
                logger.warning(f"Connection '{args.name}' created but some group permissions failed")
                raise RuntimeError("Failed to grant access to one or more groups")

    except Exception as e:
        logger.error(f"Failed to create connection '{args.name}': {e}")
        print(f"Error creating connection: {e}")
        sys.exit(1)


def handle_conn_delete(args: Any, guacdb: GuacamoleDB) -> None:
    """Delete an existing connection from the Guacamole database.

    Removes a connection and all associated data from the Guacamole database.
    Supports deletion by either name or ID, with validation to ensure exactly
    one selector is provided.

    Args:
        args: Parsed command line arguments containing either name or id of connection to delete.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 1 if connection deletion fails or validation errors occur.
    """
    logger = get_logger('cli_handle_conn')

    # Validate exactly one selector provided
    from .cli import validate_selector

    validate_selector(args, "connection")

    # Get connection name for logging
    if hasattr(args, "id") and args.id is not None:
        connection_identifier = f"ID {args.id}"
        logger.debug(f"Deleting connection by {connection_identifier}")
    else:
        connection_identifier = f"name '{args.name}'"
        logger.debug(f"Deleting connection by {connection_identifier}")

    try:
        if hasattr(args, "id") and args.id is not None:
            # Delete by ID using resolver
            connection_name = guacdb.get_connection_name_by_id(args.id)
            guacdb.delete_existing_connection(connection_id=args.id)
            logger.info(f"Connection '{connection_name}' (ID {args.id}) deleted successfully")
        else:
            # Delete by name using resolver
            guacdb.delete_existing_connection(connection_name=args.name)
            logger.info(f"Connection '{args.name}' deleted successfully")
    except ValueError as e:
        logger.error(f"Failed to delete connection {connection_identifier}: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error deleting connection {connection_identifier}: {e}")
        print(f"Error deleting connection: {e}")
        sys.exit(1)


def handle_conn_exists(args: Any, guacdb: GuacamoleDB) -> None:
    """Check if a connection exists in the Guacamole database.

    Performs an existence check for a specified connection by name or ID and exits
    with appropriate status codes for use in shell scripts and automation.

    Args:
        args: Parsed command line arguments containing either name or id of connection to check.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Exits with status 0 if connection exists, status 1 if connection does not exist
                   or if validation/database errors occur.

    Example:
        >>> # Use in shell script
        >>> if guacaman conn exists --name myserver; then
        >>>     echo "Connection exists"
        >>> else
        >>>     echo "Connection does not exist"
        >>> fi
    """
    # Validate exactly one selector provided
    from .cli import validate_selector

    validate_selector(args, "connection")

    try:
        if hasattr(args, "id") and args.id is not None:
            # Check existence by ID using resolver
            if guacdb.connection_exists(connection_id=args.id):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            # Check existence by name using resolver
            if guacdb.connection_exists(connection_name=args.name):
                sys.exit(0)
            else:
                sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error checking connection existence: {e}")
        sys.exit(1)


def handle_conn_modify(args: Any, guacdb: GuacamoleDB) -> None:
    """Modify connection parameters, parent group, or user permissions.

    Supports comprehensive connection modification including parameter updates,
    parent group assignment/removal, and user permission management.
    If no modification options are provided, displays detailed help information
    about available parameters and usage examples.

    Args:
        args: Parsed command line arguments containing name/id, optional set parameters,
              parent group, and permission modification options.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 0 for help display or status 1 for errors.

    Note:
        - Supports modification by either name or ID (exactly one required)
        - --set parameter format: "parameter=value"
        - --parent accepts empty string to remove parent group
        - --permit and --deny modify individual user permissions
        - Displays comprehensive help including all available connection parameters
    """
    logger = get_logger('cli_handle_conn')

    # Check if no modification options provided - show help
    if not args.set and args.parent is None and not args.permit and not args.deny:
        logger.debug("Displaying connection modify help (no valid options provided)")
        # Print help information about modifiable parameters
        print(
            "Usage: guacaman conn modify {--name <connection_name> | --id <connection_id>} [--set <param=value> ...] [--parent CONNGROUP] [--permit USERNAME] [--deny USERNAME]"
        )
        print("\nModification options:")
        print(f"  {VAR_COLOR}--set{RESET}: Modify connection parameters")
        print(
            f"  {VAR_COLOR}--parent{RESET}: Set parent connection group (use empty string to remove group)"
        )
        print("\nModifiable connection parameters:")
        for param, info in sorted(guacdb.CONNECTION_PARAMETERS.items()):
            if info["table"] == "connection":
                desc = f"  {VAR_COLOR}{param}{RESET}: {info['description']} (type: {info['type']}, default: {info['default']})"
                if "ref" in info:
                    if is_terminal():
                        desc += f"\n    Reference: \033[4m{info['ref']}\033[0m"
                    else:
                        desc += f"\n    Reference: {info['ref']}"
                print(desc)

        print("\nParameters in guacamole_connection_parameter table:")
        for param, info in sorted(guacdb.CONNECTION_PARAMETERS.items()):
            if info["table"] == "parameter":
                desc = f"  {VAR_COLOR}{param}{RESET}: {info['description']} (type: {info['type']}, default: {info['default']})"
                if "ref" in info:
                    if is_terminal():
                        desc += f"\n    Reference: \033[4m{info['ref']}\033[0m"
                    else:
                        desc += f"\n    Reference: {info['ref']}"
                print(desc)

        sys.exit(1)

    # Validate exactly one selector provided
    from .cli import validate_selector

    validate_selector(args, "connection")

    try:
        # Get connection name for display purposes (resolvers handle the actual lookup)
        if hasattr(args, "id") and args.id is not None:
            # For ID-based operations, get name for display
            connection_name = guacdb.get_connection_name_by_id(args.id)
            if not connection_name:
                logger.error(f"Connection with ID {args.id} not found")
                print(f"Error: Connection with ID {args.id} not found")
                sys.exit(1)
        else:
            connection_name = args.name

        logger.debug(f"Modifying connection: {connection_name}")
        guacdb.debug_connection_permissions(connection_name)

        modified_operations = []

        # Handle permission modifications (these methods expect connection_name)
        if args.permit:
            logger.debug(f"Granting permission to user '{args.permit}' for connection '{connection_name}'")
            guacdb.grant_connection_permission_to_user(args.permit, connection_name)
            logger.info(f"Granted permission to user '{args.permit}' for connection '{connection_name}'")
            modified_operations.append(f"permit:{args.permit}")
            print(
                f"Successfully granted permission to user '{args.permit}' for connection '{connection_name}'"
            )
            guacdb.debug_connection_permissions(connection_name)

        if args.deny:
            logger.debug(f"Revoking permission from user '{args.deny}' for connection '{connection_name}'")
            guacdb.revoke_connection_permission_from_user(args.deny, connection_name)
            logger.info(f"Revoked permission from user '{args.deny}' for connection '{connection_name}'")
            modified_operations.append(f"deny:{args.deny}")
            print(
                f"Successfully revoked permission from user '{args.deny}' for connection '{connection_name}'"
            )

        # Handle parent group modification using resolver
        if args.parent is not None:
            try:
                # Convert empty string to None to unset parent group
                parent_group = args.parent if args.parent != "" else None
                logger.debug(f"Setting parent group to '{parent_group}' for connection '{connection_name}'")
                if hasattr(args, "id") and args.id is not None:
                    guacdb.modify_connection_parent_group(
                        connection_id=args.id, group_name=parent_group
                    )
                else:
                    guacdb.modify_connection_parent_group(
                        connection_name=args.name, group_name=parent_group
                    )
                logger.info(f"Parent group set to '{args.parent}' for connection '{connection_name}'")
                modified_operations.append(f"parent:{args.parent}")
                print(
                    f"Successfully set parent group to '{args.parent}' for connection '{connection_name}'"
                )
            except Exception as e:
                logger.error(f"Failed to set parent group for connection '{connection_name}': {e}")
                print(f"Error setting parent group: {e}")
                sys.exit(1)

        # Process each --set argument (if any) using resolver
        for param_value in args.set or []:
            if "=" not in param_value:
                logger.error(f"Invalid --set format: {param_value}")
                print(
                    f"Error: Invalid format for --set. Must be param=value, got: {param_value}"
                )
                sys.exit(1)

            param, value = param_value.split("=", 1)
            logger.debug(f"Setting parameter '{param}={value}' for connection '{connection_name}'")
            guacdb.debug_print(
                f"Modifying connection '{connection_name}': setting {param}={value}"
            )

            try:
                if hasattr(args, "id") and args.id is not None:
                    guacdb.modify_connection(
                        connection_id=args.id, param_name=param, param_value=value
                    )
                else:
                    guacdb.modify_connection(
                        connection_name=args.name, param_name=param, param_value=value
                    )
                logger.info(f"Parameter '{param}' updated to '{value}' for connection '{connection_name}'")
                modified_operations.append(f"{param}={value}")
                print(
                    f"Successfully updated {param} for connection '{connection_name}'"
                )
            except ValueError as e:
                logger.error(f"Failed to set parameter '{param}' for connection '{connection_name}': {e}")
                print(f"Error: {str(e)}")
                sys.exit(1)

        if modified_operations:
            logger.info(f"Connection '{connection_name}' modified successfully: {', '.join(modified_operations)}")

    except ValueError as e:
        logger.error(f"Failed to modify connection '{connection_name}': {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error modifying connection '{connection_name}': {e}")
        print(f"Error modifying connection: {e}")
        sys.exit(1)
