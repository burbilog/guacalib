import sys

def handle_user_command(args, guacdb):
    if args.user_command == 'new':
        # Check if user exists first
        if guacdb.user_exists(args.name):
            print(f"Error: User '{args.name}' already exists")
            sys.exit(1)
            
        # Create new user
        guacdb.create_user(args.name, args.password)

        # Handle group memberships
        groups = []
        if args.group:
            groups = [g.strip() for g in args.group.split(',')]
            success = True
            
            for group in groups:
                try:
                    guacdb.add_user_to_group(args.name, group)
                    guacdb.debug_print(f"Added user '{args.name}' to group '{group}'")
                except Exception as e:
                    print(f"[-] Failed to add to group '{group}': {e}")
                    success = False
            
            if not success:
                raise RuntimeError("Failed to add to one or more groups")

        guacdb.debug_print(f"Successfully created user '{args.name}'")
        if groups:
            guacdb.debug_print(f"Group memberships: {', '.join(groups)}")
            
    elif args.user_command == 'list':
        users_and_groups = guacdb.list_users_with_groups()
        print("users:")
        for user, groups in users_and_groups.items():
            print(f"  {user}:")
            print("    groups:")
            for group in groups:
                print(f"      - {group}")

    elif args.user_command == 'del':
        try:
            guacdb.delete_existing_user(args.name)
            guacdb.debug_print(f"Successfully deleted user '{args.name}'")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error deleting user: {e}")
            sys.exit(1)

    elif args.user_command == 'exists':
        if guacdb.user_exists(args.name):
            sys.exit(0)
        else:
            sys.exit(1)
            
    elif args.user_command == 'modify':
        if not args.name or not args.set:
            print("Usage: guacaman user modify --name USERNAME --set PARAMETER=VALUE")
            print("\nAllowed parameters:")
            print("-------------------")
            max_param_len = max(len(param) for param in guacdb.USER_PARAMETERS.keys())
            max_type_len = max(len(info['type']) for info in guacdb.USER_PARAMETERS.values())
            
            # Print header
            print(f"{'PARAMETER':<{max_param_len+2}} {'TYPE':<{max_type_len+2}} {'DEFAULT':<10} DESCRIPTION")
            print(f"{'-'*(max_param_len+2)} {'-'*(max_type_len+2)} {'-'*10} {'-'*40}")
            
            # Print each parameter
            for param, info in sorted(guacdb.USER_PARAMETERS.items()):
                print(f"{param:<{max_param_len+2}} {info['type']:<{max_type_len+2}} {info['default']:<10} {info['description']}")
            
            print("\nExample usage:")
            print("  guacaman user modify --name john.doe --set disabled=1")
            print("  guacaman user modify --name john.doe --set \"organization=Example Corp\"")
            sys.exit(0)
        
        try:
            # Parse the parameter and value
            if '=' not in args.set:
                print("Error: --set must be in format 'parameter=value'")
                sys.exit(1)
                
            param_name, param_value = args.set.split('=', 1)
            param_name = param_name.strip()
            param_value = param_value.strip()
            
            # Check if user exists
            if not guacdb.user_exists(args.name):
                print(f"Error: User '{args.name}' does not exist")
                sys.exit(1)
            
            # Modify the user parameter
            guacdb.modify_user(args.name, param_name, param_value)
            guacdb.debug_print(f"Successfully modified user '{args.name}': {param_name}={param_value}")
            
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error modifying user: {e}")
            sys.exit(1)
