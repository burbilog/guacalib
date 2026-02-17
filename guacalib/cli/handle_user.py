import re
import sys
from argparse import Namespace
from typing import NoReturn

from guacalib import GuacamoleDB
from guacalib.exceptions import GuacalibError

# Guacamole entity name constraints (from schema: varchar(128) NOT NULL)
USERNAME_MAX_LENGTH = 128
# Allow alphanumeric, underscore, hyphen, period, and @ (common in email-style usernames)
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.@-]+$")


def validate_username(username: str) -> None:
    """Validate username according to Guacamole constraints.

    Args:
        username: Username to validate

    Raises:
        SystemExit: If validation fails
    """
    if not username or not isinstance(username, str):
        print("Error: Username must be a non-empty string")
        sys.exit(1)

    username = username.strip()
    if not username:
        print("Error: Username cannot be empty or whitespace only")
        sys.exit(1)

    if len(username) > USERNAME_MAX_LENGTH:
        print(
            f"Error: Username exceeds maximum length of {USERNAME_MAX_LENGTH} characters"
        )
        sys.exit(1)

    if not USERNAME_PATTERN.match(username):
        print(
            "Error: Username can only contain letters, numbers, underscore (_), hyphen (-), period (.), and @"
        )
        sys.exit(1)


def handle_user_command(args: Namespace, guacdb: GuacamoleDB) -> None:
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


def handle_user_new(args: Namespace, guacdb: GuacamoleDB) -> None:
    validate_username(args.name)

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
            except GuacalibError as e:
                print(f"[-] Failed to add to group '{group}': {e}")
                success = False

        if not success:
            raise RuntimeError("Failed to add to one or more groups")

    guacdb.debug_print(f"Successfully created user '{args.name}'")
    if groups:
        guacdb.debug_print(f"Group memberships: {', '.join(groups)}")


def handle_user_list(args: Namespace, guacdb: GuacamoleDB) -> None:
    users_and_groups = guacdb.list_users_with_usergroups()
    print("users:")
    for user, groups in users_and_groups.items():
        print(f"  {user}:")
        print("    usergroups:")
        for group in groups:
            print(f"      - {group}")


def handle_user_delete(args: Namespace, guacdb: GuacamoleDB) -> None:
    validate_username(args.name)

    try:
        guacdb.delete_existing_user(args.name)
        guacdb.debug_print(f"Successfully deleted user '{args.name}'")
    except GuacalibError as e:
        print(f"Error: {e}")
        sys.exit(1)


def handle_user_exists(args: Namespace, guacdb: GuacamoleDB) -> NoReturn:
    validate_username(args.name)

    if guacdb.user_exists(args.name):
        sys.exit(0)
    else:
        sys.exit(1)


def handle_user_modify(args: Namespace, guacdb: GuacamoleDB) -> None:
    # Show usage if no arguments provided
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

    validate_username(args.name)

    try:
        if not guacdb.user_exists(args.name):
            print(f"Error: User '{args.name}' doesn't exist")
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

    except GuacalibError as e:
        print(f"Error: {e}")
        sys.exit(1)
