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
    
    print("usergroups:")
    handle_usergroup_command(args, guacdb)
    
    print("\nconnection groups:")
    handle_conngroup_command(args, guacdb)
