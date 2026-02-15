"""CLI validation utilities."""

import sys
from argparse import Namespace


def validate_selector(args: Namespace, entity_type: str = "connection") -> None:
    """Validate exactly one of name or id is provided and validate ID format.

    Args:
        args: Parsed command line arguments
        entity_type: Type of entity for error messages (e.g., 'connection', 'usergroup')
    """
    has_name = hasattr(args, "name") and args.name is not None
    has_id = hasattr(args, "id") and args.id is not None

    if not (has_name ^ has_id):
        print(
            f"Error: Exactly one of --name or --id must be provided for {entity_type}"
        )
        sys.exit(1)

    # Validate ID format if ID is provided
    if has_id and args.id <= 0:
        print(
            f"Error: {entity_type.capitalize()} ID must be a positive integer greater than 0"
        )
        sys.exit(1)
