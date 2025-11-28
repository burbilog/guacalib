import sys
import mysql.connector
from typing import Any

from guacalib.db import GuacamoleDB
from guacalib.logging_config import get_logger
from guacalib import conngroups_repo


def handle_conngroup_command(args: Any, guacdb: GuacamoleDB) -> None:
    """Handle all connection group management subcommands.

    This function processes all connection group-related operations including creating,
    listing, checking existence, deleting, and modifying connection groups. Supports
    both name-based and ID-based identification and includes comprehensive error
    handling with transaction management.

    Args:
        args: Parsed command line arguments containing conngroup_command and
              relevant parameters for the specific operation.
        guacdb: GuacamoleDB instance for database operations.

    Raises:
        SystemExit: Always exits with status 0 for success, status 1 for errors,
                   or status 2 for validation errors.

    Note:
        Supported subcommands:
        - new: Create a new connection group (requires --name, optional --parent)
        - list: List all connection groups (optional --id for specific group)
        - exists: Check if connection group exists (requires exactly one of --name or --id)
        - del: Delete connection group (requires exactly one of --name or --id)
        - modify: Comprehensive modification support including:
                 * Parent group assignment (--parent)
                 * Connection management (--addconn-*, --rmconn-*)
                 * User permissions (--permit, --deny)
                 * Supports both name and ID-based identification
    """
    logger = get_logger('cli_handle_conngroup')
    if args.conngroup_command == "new":
        try:
            # Check if group already exists
            logger.debug(f"Creating new connection group: {args.name}")
            groups = guacdb.list_connection_groups()
            if args.name in groups:
                logger.error(f"Connection group '{args.name}' already exists")
                print(f"Error: Connection group '{args.name}' already exists")
                sys.exit(1)

            guacdb.create_connection_group(args.name, args.parent)
            # Explicitly commit the transaction
            guacdb.conn.commit()
            logger.info(f"Successfully created connection group: {args.name}")
            print(f"Successfully created connection group: {args.name}")
            sys.exit(0)
        except Exception as e:
            # Rollback on error
            logger.error(f"Error creating connection group: {e}")
            guacdb.conn.rollback()
            print(f"Error creating connection group: {e}")
            sys.exit(1)

    elif args.conngroup_command == "list":
        logger.debug("Listing connection groups")
        # Validate --id if provided
        if hasattr(args, "id") and args.id is not None:
            if args.id <= 0:
                logger.error("Connection group ID must be a positive integer greater than 0")
                print(
                    "Error: Connection group ID must be a positive integer greater than 0"
                )
                sys.exit(1)
            # Get specific connection group by ID
            logger.debug(f"Getting connection group by ID: {args.id}")
            groups_result = guacdb.get_connection_group_by_id(args.id)
            if groups_result is None:
                logger.warning(f"Connection group with ID {args.id} not found")
                print(f"Connection group with ID {args.id} not found")
                sys.exit(1)
        else:
            # Get all connection groups
            logger.debug("Getting all connection groups")
            groups = guacdb.list_connection_groups()

        # Use the appropriate groups variable
        if hasattr(args, "id") and args.id is not None:
            groups = groups_result if 'groups_result' in locals() else groups  # Use specific result if available

        logger.info(f"Retrieved {len(groups)} connection groups")
        print("conngroups:")
        for group_name, data in groups.items():
            print(f"  {group_name}:")
            print(f"    id: {data['id']}")
            print(f"    parent: {data['parent']}")
            print("    connections:")
            connections = data["connections"]
            # Ensure connections is iterable (it should be a list of strings)
            if isinstance(connections, list):
                for conn in connections:
                    if conn:  # Skip empty strings
                        print(f"      - {conn}")
            else:
                # If it's not a list (unlikely but for type safety), convert to string
                if connections:
                    print(f"      - {connections}")
        sys.exit(0)

    elif args.conngroup_command == "exists":
        try:
            # Rely on database layer validation via resolvers
            if hasattr(args, "id") and args.id is not None:
                # Check if connection group exists by ID using resolver
                logger.debug(f"Checking if connection group exists by ID: {args.id}")
                if guacdb.connection_group_exists(group_id=args.id):
                    logger.info(f"Connection group with ID '{args.id}' exists")
                    guacdb.debug_print(f"Connection group with ID '{args.id}' exists")
                    sys.exit(0)
                else:
                    logger.info(f"Connection group with ID '{args.id}' does not exist")
                    guacdb.debug_print(
                        f"Connection group with ID '{args.id}' does not exist"
                    )
                    sys.exit(1)
            else:
                # Use name-based lookup
                logger.debug(f"Checking if connection group exists: {args.name}")
                if guacdb.connection_group_exists(group_name=args.name):
                    logger.info(f"Connection group '{args.name}' exists")
                    guacdb.debug_print(f"Connection group '{args.name}' exists")
                    sys.exit(0)
                else:
                    logger.info(f"Connection group '{args.name}' does not exist")
                    guacdb.debug_print(f"Connection group '{args.name}' does not exist")
                    sys.exit(1)
        except ValueError as e:
            logger.error(f"Error checking connection group existence: {e}")
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error checking connection group existence: {e}")
            print(f"Error checking connection group existence: {e}")
            sys.exit(1)

    elif args.conngroup_command == "del":
        try:
            # Rely on database layer validation via resolvers
            if hasattr(args, "id") and args.id is not None:
                # Delete by ID using resolver
                group_name_display = guacdb.get_connection_group_name_by_id(args.id)
                logger.debug(f"Deleting connection group '{group_name_display}' by ID: {args.id}")
                guacdb.delete_connection_group(group_id=args.id)
                logger.info(f"Successfully deleted connection group '{group_name_display}'")
                print(f"Successfully deleted connection group '{group_name_display}'")
            else:
                # Delete by name using resolver
                logger.debug(f"Deleting connection group: {args.name}")
                guacdb.delete_connection_group(group_name=args.name)
                logger.info(f"Successfully deleted connection group '{args.name}'")
                print(f"Successfully deleted connection group '{args.name}'")
            sys.exit(0)
        except ValueError as e:
            logger.error(f"Error deleting connection group: {e}")
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error deleting connection group: {e}")
            print(f"Error deleting connection group: {e}")
            sys.exit(1)

    elif args.conngroup_command == "modify":
        try:
            # Validate argument combinations before processing
            permit_args = getattr(args, "permit", None)
            deny_args = getattr(args, "deny", None)

            # Filter out None values from append action
            permit_list = [p for p in permit_args] if permit_args else []
            deny_list = [d for d in deny_args] if deny_args else []

            if permit_list and deny_list:
                print(
                    "Error: Cannot specify both --permit and --deny in the same command"
                )
                sys.exit(1)

            if len(permit_list) > 1:
                print("Error: Only one user can be specified for --permit operation")
                sys.exit(1)

            if len(deny_list) > 1:
                print("Error: Only one user can be specified for --deny operation")
                sys.exit(1)

            # Validate that exactly one target selector is provided
            has_name_selector = hasattr(args, "name") and args.name is not None
            has_id_selector = hasattr(args, "id") and args.id is not None
            if not has_name_selector and not has_id_selector:
                print(
                    "Error: Must specify either --name or --id to identify the connection group"
                )
                sys.exit(1)
            if has_name_selector and has_id_selector:
                print("Error: Cannot specify both --name and --id simultaneously")
                sys.exit(1)

            # Validate ID format if provided
            if has_id_selector and args.id <= 0:
                print(
                    "Error: Connection group ID must be a positive integer greater than 0"
                )
                sys.exit(1)

            # Validate name format if provided
            if has_name_selector and not args.name.strip():
                print("Error: Connection group name cannot be empty")
                sys.exit(1)

            # Rely on database layer validation via resolvers
            # Get group name for display purposes (resolvers handle the actual lookup)
            if hasattr(args, "id") and args.id is not None:
                # For ID-based operations, get name for display
                group_name_result = guacdb.get_connection_group_name_by_id(args.id)
                if group_name_result is None:
                    print(f"Error: Connection group with ID {args.id} not found")
                    sys.exit(1)
                group_name = group_name_result
            else:
                group_name = args.name

            # Handle parent modification
            if args.parent is not None:
                logger.debug(f"Setting parent connection group: {args.parent}")
                guacdb.debug_print(f"Setting parent connection group: {args.parent}")
                if hasattr(args, "id") and args.id is not None:
                    conngroups_repo.modify_connection_group_parent(
                        cursor=guacdb.cursor, group_name=group_name, new_parent_name=args.parent
                    )
                else:
                    guacdb.modify_connection_group_parent(
                        group_name=args.name, new_parent_name=args.parent
                    )
                guacdb.conn.commit()  # Explicitly commit the transaction
                logger.info(f"Successfully set parent group for '{group_name}' to '{args.parent}'")
                print(
                    f"Successfully set parent group for '{group_name}' to '{args.parent}'"
                )

            # Handle connection addition/removal
            connection_modified = False

            if hasattr(args, "addconn_by_name") and args.addconn_by_name is not None:
                logger.debug(f"Adding connection by name: {args.addconn_by_name}")
                guacdb.debug_print(f"Adding connection by name: {args.addconn_by_name}")
                guacdb.modify_connection_parent_group(
                    connection_name=args.addconn_by_name, group_name=group_name
                )
                connection_modified = True
                logger.info(f"Added connection '{args.addconn_by_name}' to group '{group_name}'")
                print(
                    f"Added connection '{args.addconn_by_name}' to group '{group_name}'"
                )

            elif hasattr(args, "addconn_by_id") and args.addconn_by_id is not None:
                logger.debug(f"Adding connection by ID: {args.addconn_by_id}")
                guacdb.debug_print(f"Adding connection by ID: {args.addconn_by_id}")
                # Get connection name for display
                conn_name = guacdb.get_connection_name_by_id(args.addconn_by_id)
                if not conn_name:
                    logger.error(f"Connection with ID {args.addconn_by_id} not found")
                    print(f"Error: Connection with ID {args.addconn_by_id} not found")
                    sys.exit(1)
                guacdb.modify_connection_parent_group(
                    connection_id=args.addconn_by_id, group_name=group_name
                )
                connection_modified = True
                logger.info(f"Added connection '{conn_name}' to group '{group_name}'")
                print(f"Added connection '{conn_name}' to group '{group_name}'")

            elif hasattr(args, "rmconn_by_name") and args.rmconn_by_name is not None:
                logger.debug(f"Removing connection by name: {args.rmconn_by_name}")
                guacdb.debug_print(
                    f"Removing connection by name: {args.rmconn_by_name}"
                )
                guacdb.modify_connection_parent_group(
                    connection_name=args.rmconn_by_name, group_name=None
                )
                connection_modified = True
                logger.info(f"Removed connection '{args.rmconn_by_name}' from group '{group_name}'")
                print(
                    f"Removed connection '{args.rmconn_by_name}' from group '{group_name}'"
                )

            elif hasattr(args, "rmconn_by_id") and args.rmconn_by_id is not None:
                logger.debug(f"Removing connection by ID: {args.rmconn_by_id}")
                guacdb.debug_print(f"Removing connection by ID: {args.rmconn_by_id}")
                # Get connection name for display
                conn_name = guacdb.get_connection_name_by_id(args.rmconn_by_id)
                if not conn_name:
                    logger.error(f"Connection with ID {args.rmconn_by_id} not found")
                    print(f"Error: Connection with ID {args.rmconn_by_id} not found")
                    sys.exit(1)
                guacdb.modify_connection_parent_group(
                    connection_id=args.rmconn_by_id, group_name=None
                )
                connection_modified = True
                logger.info(f"Removed connection '{conn_name}' from group '{group_name}'")
                print(f"Removed connection '{conn_name}' from group '{group_name}'")

            # Handle permission grant/revoke
            permission_modified = False

            if permit_list:
                username = permit_list[0]

                # Validate username format
                if not username or not isinstance(username, str):
                    print("Error: Username must be a non-empty string")
                    sys.exit(1)

                logger.debug(f"Granting permission to user: {username}")
                guacdb.debug_print(f"Granting permission to user: {username}")
                try:
                    if hasattr(args, "id") and args.id is not None:
                        guacdb.grant_connection_group_permission_to_user_by_id(
                            username, args.id
                        )
                        logger.info(f"Successfully granted permission to user '{username}' for connection group ID '{args.id}'")
                        print(
                            f"Successfully granted permission to user '{username}' for connection group ID '{args.id}'"
                        )
                    else:
                        guacdb.grant_connection_group_permission_to_user(
                            username, args.name
                        )
                        logger.info(f"Successfully granted permission to user '{username}' for connection group '{group_name}'")
                        print(
                            f"Successfully granted permission to user '{username}' for connection group '{group_name}'"
                        )
                    permission_modified = True
                except ValueError as e:
                    # Provide more specific error guidance
                    error_msg = str(e)
                    if "not found" in error_msg:
                        if "User" in error_msg:
                            print(
                                f"Error: User '{username}' does not exist. Use 'guacaman user list' to see available users."
                            )
                        elif "Connection group" in error_msg and "ID" in error_msg:
                            print(
                                f"Error: Connection group ID '{args.id}' does not exist"
                            )
                        elif "Connection group" in error_msg:
                            print(
                                f"Error: Connection group '{args.name}' does not exist"
                            )
                        else:
                            print(f"Error: {error_msg}")
                        raise  # Re-raise to be caught by outer handler
                    elif "already has permission" in error_msg:
                        print(f"Permission already exists. No changes made.")
                        permission_modified = True  # Consider this successful since permission already exists
                        # Continue without error - permission already exists
                    else:
                        print(f"Error: {error_msg}")
                        raise  # Re-raise to be caught by outer handler

            elif deny_list:
                username = deny_list[0]

                # Validate username format
                if not username or not isinstance(username, str):
                    print("Error: Username must be a non-empty string")
                    sys.exit(1)

                logger.debug(f"Revoking permission from user: {username}")
                guacdb.debug_print(f"Revoking permission from user: {username}")
                try:
                    if hasattr(args, "id") and args.id is not None:
                        guacdb.revoke_connection_group_permission_from_user_by_id(
                            username, args.id
                        )
                        logger.info(f"Successfully revoked permission from user '{username}' for connection group ID '{args.id}'")
                        print(
                            f"Successfully revoked permission from user '{username}' for connection group ID '{args.id}'"
                        )
                    else:
                        guacdb.revoke_connection_group_permission_from_user(
                            username, args.name
                        )
                        logger.info(f"Successfully revoked permission from user '{username}' for connection group '{group_name}'")
                        print(
                            f"Successfully revoked permission from user '{username}' for connection group '{group_name}'"
                        )
                    permission_modified = True
                except ValueError as e:
                    # Provide more specific error guidance
                    error_msg = str(e)
                    if "not found" in error_msg:
                        if "User" in error_msg:
                            print(
                                f"Error: User '{username}' does not exist. Use 'guacaman user list' to see available users."
                            )
                        elif "Connection group" in error_msg and "ID" in error_msg:
                            print(
                                f"Error: Connection group ID '{args.id}' does not exist"
                            )
                        elif "Connection group" in error_msg:
                            print(
                                f"Error: Connection group '{args.name}' does not exist"
                            )
                        else:
                            print(f"Error: {error_msg}")
                    elif "has no permission" in error_msg:
                        # Match exact format expected by tests
                        print(
                            f"Error: Permission for user '{username}' on connection group '{group_name}' does not exist"
                        )
                        sys.exit(1)
                    else:
                        print(f"Error: {error_msg}")
                    sys.exit(1)

            # Validate that either parent, connection, or permission operation was specified
            if (
                args.parent is None
                and not connection_modified
                and not permission_modified
            ):
                print(
                    "Error: No modification specified. Use --parent, --addconn-*, --rmconn-*, --permit, or --deny"
                )
                sys.exit(2)

            # Commit all operations atomically
            if connection_modified or permission_modified:
                try:
                    guacdb.debug_print("Committing all transaction operations...")
                    guacdb.conn.commit()
                    guacdb.debug_print(
                        f"Successfully committed transaction for connection group '{group_name}' operations"
                    )
                except Exception as commit_error:
                    error_msg = f"Failed to commit transaction: {commit_error}"
                    guacdb.debug_print(error_msg)
                    print(
                        "Error: Failed to save changes. No modifications were applied."
                    )
                    sys.exit(1)

            sys.exit(0)
        except ValueError as e:
            # Handle validation and logical errors
            print(f"Error: {e}")
            if guacdb.conn:
                try:
                    guacdb.conn.rollback()
                except Exception as rollback_error:
                    guacdb.debug_print(f"Rollback failed: {rollback_error}")
            sys.exit(1)
        except mysql.connector.Error as e:
            # Handle database-specific errors
            error_msg = f"Database error modifying connection group: {e}"
            guacdb.debug_print(error_msg)
            if guacdb.conn:
                try:
                    guacdb.conn.rollback()
                except Exception as rollback_error:
                    guacdb.debug_print(f"Rollback failed: {rollback_error}")
            print(
                f"Error: Database operation failed. Please check your data and try again."
            )
            sys.exit(1)
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected error modifying connection group: {e}"
            guacdb.debug_print(error_msg)
            if guacdb.conn:
                try:
                    guacdb.conn.rollback()
                except Exception as rollback_error:
                    guacdb.debug_print(f"Rollback failed: {rollback_error}")
            print(
                f"Error: An unexpected error occurred. Please check the logs and try again."
            )
            sys.exit(1)
