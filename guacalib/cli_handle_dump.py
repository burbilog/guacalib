def handle_dump_command(guacdb):
    """Handle dump command - fetch and format all Guacamole data in YAML format"""
    # Print user groups using existing list functionality
    from guacalib.cli_handle_usergroup import handle_usergroup_command
    from guacalib.cli_handle_conngroup import handle_conngroup_command
    
    # Create dummy args object for list commands
    class Args:
        def __init__(self):
            self.usergroup_command = 'list'
            self.conngroup_command = 'list'
    
    args = Args()
    
    # Print users using existing list handler
    from guacalib.cli_handle_user import handle_user_list
    handle_user_list(args, guacdb)
    
    # Print user groups
    handle_usergroup_command(args, guacdb)
    
    # Print connections using conn list handler
    from guacalib.cli_handle_conn import handle_conn_list
    handle_conn_list(args, guacdb)
    
    # Print connection groups
    handle_conngroup_command(args, guacdb)
