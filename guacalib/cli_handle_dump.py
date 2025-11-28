from guacalib.db import GuacamoleDB
from .logging_config import get_logger


def handle_dump_command(guacdb: GuacamoleDB) -> None:
    """Export all Guacamole data in YAML format.

    Retrieves and displays comprehensive information about all users, user groups,
    connections, and connection groups in the Guacamole database. Formats the output
    as structured YAML for easy consumption by other tools or for backup purposes.

    Args:
        guacdb: GuacamoleDB instance for database operations.

    Note:
        This function serves as a unified interface that calls the respective
        list handlers for each entity type (users, user groups, connections,
        and connection groups) to provide a complete database dump in YAML format.
        The output includes hierarchical relationships and permissions.
    """
    logger = get_logger("cli_handle_dump")

    logger.debug("Starting database dump operation")

    # Print user groups using existing list functionality
    from guacalib.cli_handle_usergroup import handle_usergroup_command
    from guacalib.cli_handle_conngroup import handle_conngroup_command

    # Create dummy args object for list commands
    class Args:
        def __init__(self):
            self.usergroup_command = "list"
            self.conngroup_command = "list"

    args = Args()

    try:
        logger.debug("Collecting users for dump")
        # Print users using existing list handler
        from guacalib.cli_handle_user import handle_user_list

        handle_user_list(args, guacdb)

        logger.debug("Collecting user groups for dump")
        # Print user groups
        handle_usergroup_command(args, guacdb)

        logger.debug("Collecting connections for dump")
        # Print connections using conn list handler
        from guacalib.cli_handle_conn import handle_conn_list

        handle_conn_list(args, guacdb)

        logger.debug("Collecting connection groups for dump")
        # Print connection groups
        handle_conngroup_command(args, guacdb)

        logger.info("Database dump completed successfully")

    except Exception as e:
        logger.error(f"Database dump failed: {e}")
        # Re-raise the exception to maintain existing error handling behavior
        raise
