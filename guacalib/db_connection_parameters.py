
CONNECTION_PARAMETERS = {
    # Parameters in guacamole_connection table
    'protocol': {
        'type': 'string',
        'description': 'The protocol to use with this connection.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/jdbc-auth.html#connections-and-parameters',
        'table': 'connection'
    },
    'max_connections': {
        'type': 'int',
        'description': 'Maximum number of connections allowed to this connection',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/jdbc-auth.html#connections-and-parameters',
        'table': 'connection'
    },
    'max_connections_per_user': {
        'type': 'int',
        'description': 'Maximum number of connections allowed per user',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/jdbc-auth.html#connections-and-parameters',
        'table': 'connection'
    },
    'proxy_hostname': {
        'type': 'string',
        'description': 'The hostname or IP address of the Guacamole proxy.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/jdbc-auth.html#connections-and-parameters',
        'table': 'connection'
    },
    'proxy_port': {
        'type': 'int',
        'description': 'The TCP port number of the Guacamole proxy daemon.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/jdbc-auth.html#connections-and-parameters',
        'table': 'connection'
    },
    'connection_weight': {
        'type': 'int',
        'description': 'The weight for a connection.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/jdbc-auth.html#connections-and-parameters',
        'table': 'connection'
    },
    'failover_only': {
        'type': 'int',
        'description': 'Whether this connection should be used for failover situations only.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/jdbc-auth.html#connections-and-parameters',
        'table': 'connection'
    },
    # Parameters in guacamole_connection_parameter table
    'username': {
        'type': 'string',
        'description': 'The username to use to authenticate, if any.',
        'default': 'NULL',
        'table': 'parameter'
    },
    'private-key': {
        'type': 'string',
        'description': 'The entire contents of the private key to use for public key authentication.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#ssh-authentication',
        'table': 'parameter'
    },
    'listen-timeout': {
        'type': 'int',
        'description': 'If reverse connection is in use, the maximum amount of time to wait.',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#reverse-vnc-connections',
        'default': 'NULL',
        'table': 'parameter'
    },
    'reverse-connect': {
        'type': 'boolean',
        'description': 'Whether reverse connection should be used. ',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#reverse-vnc-connections',
        'default': 'NULL',
        'table': 'parameter'
    },
    'host-key': {
        'type': 'string',
        'description': 'The known hosts entry for the SSH server.',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#ssh-network-parameters',
        'default': 'NULL',
        'table': 'parameter'
    },
    'server-alive-interval': {
        'type': 'int',
        'description': 'Configure the the server keepalive interval. The minimum value is 2.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#ssh-network-parameters',
        'table': 'parameter'
    },
    'passphrase': {
        'type': 'string',
        'description': 'The passphrase to use to decrypt the private key for use in public key authentication.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#ssh-authentication',
        'table': 'parameter'
    },
    'enable-audio': {
        'type': 'boolean',
        'description': 'If set to “true”, audio support will be enabled.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#audio-support-via-pulseaudio',
        'table': 'parameter'
    },
    'audio-servername': {
        'type': 'string',
        'description': 'The name of the PulseAudio server to connect to.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#audio-support-via-pulseaudio',
        'table': 'parameter'
    },
    'clipboard-encoding': {
        'type': 'string',
        'description': 'The encoding to assume for the VNC clipboard',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#clipboard-encoding',
        'table': 'parameter'
    },
    'enable-sftp': {
        'type': 'string',
        'description': 'Whether file transfer should be enabled.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-root-directory': {
        'type': 'string',
        'description': 'The directory to expose to connected users via Guacamole’s file browser.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-disable-download': {
        'type': 'string',
        'description': 'If set to true downloads from the remote system to the client (browser) will be disabled.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-disable-upload': {
        'type': 'string',
        'description': 'If set to true uploads from the client (browser) to the remote system will be disabled.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'timezone': {
        'type': 'string',
        'description': 'This parameter allows you to control the timezone..',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#internationalization-locale-settings',
        'table': 'parameter'
    },
    'locale': {
        'type': 'string',
        'description': 'The specific locale to request for the SSH session.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#internationalization-locale-settings',
        'table': 'parameter'
    },
    'command': {
        'type': 'string',
        'description': 'The command to execute over the SSH session, if any.',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#running-a-command-instead-of-a-shell',
        'default': 'NULL',
        'table': 'parameter'
    },
    'terminal-type': {
        'type': 'string',
        'description': 'This parameter sets the terminal emulator type string that is passed to the server.', 
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#controlling-terminal-behavior',
        'table': 'parameter'
    },
    'color-scheme': {
        'type': 'string',
        'description': 'The color scheme to use for the terminal session.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#terminal-display-settings',
        'table': 'parameter'
    },
    'backspace': {
        'type': 'string',
        'description': 'This parameter controls the ASCII code that the backspace key sends to the remote system.',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#controlling-terminal-behavior',
        'default': 'NULL',
        'table': 'parameter'
    },
    'hostname': {
        'type': 'string',
        'description': 'The hostname or IP address of the server Guacamole should connect to.',
        'default': 'NULL',
        'table': 'parameter'
    },
    'port': {
        'type': 'string',
        'description': 'Port of the remote server, usually 22 for SSH, 3389 for RDP and 5900 for VNC',
        'default': 'NULL',
        'table': 'parameter'
    },
    'password': {
        'type': 'string',
        'description': 'Password for the connection (VNC password, SSH password, etc.)',
        'default': 'NULL',
        'table': 'parameter'
    },
    'dest-host': {
        'type': 'string',
        'description': 'The destination host to request when connecting to a VNC proxy.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#vnc-repeater',
        'table': 'parameter'
    },
    'dest-port': {
        'type': 'string',
        'description': 'The destination port to request when connecting to a VNC proxy.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#vnc-repeater',
        'table': 'parameter'
    },
    'disable-upload': {
        'type': 'boolean',
        'description': 'If set to true, uploads from the client (browser) to the remote server location will be disabled. ',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'disable-download': {
        'type': 'boolean',
        'description': 'If set to true downloads from the remote server to client (browser) will be disabled.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'static-channels': {
        'type': 'string',
        'description': 'A comma-separated list of static channel names to open and expose as pipes. ',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'console-audio': {
        'type': 'boolean',
        'description': 'If set to “true”, audio will be explicitly enabled in the console (admin) session of the RDP server.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'create-drive-path': {
        'type': 'boolean',
        'description': 'If set to “true”, and file transfer is enabled, the directory specified by the drive-path parameter will automatically be created if it does not yet exist.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'drive-path': {
        'type': 'string',
        'description': 'The directory on the Guacamole server in which transferred files should be stored.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'drive-name': {
        'type': 'string',
        'description': 'The name of the filesystem used when passed through to the RDP session.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'enable-drive': {
        'type': 'boolean',
        'description': 'Enable file transfer support by setting this parameter to "true".',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'printer-name': {
        'type': 'string',
        'description': 'The name of the redirected printer device that is passed through to the RDP session.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'enable-printing': {
        'type': 'boolean',
        'description': 'Enable printing by setting this parameter to "true".',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'enable-touch': {
        'type': 'boolean',
        'description': 'If set to "true", support for multi-touch events will be enabled',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'enable-audio-input': {
        'type': 'boolean',
        'description': 'If set to “true”, audio input support (microphone) will be enabled',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'disable-audio': {
        'type': 'boolean',
        'description': 'Disable sound by setting this parameter to "true"',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#device-redirection',
        'table': 'parameter'
    },
    'force-lossless': {
        'type': 'boolean',
        'description': 'Only use lossless compression for graphical updates.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#display-settings',
        'table': 'parameter'
    },
    'read-only': {
        'type': 'boolean',
        'description': 'Whether the connection is read-only (true/false)',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#display-settings',
        'table': 'parameter'
    },
    'encodings': {
        'type': 'string',
        'description': 'A space-delimited list of VNC encodings to use.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#display-settings',
        'table': 'parameter'
    },
    'cursor': {
        'type': 'string',
        'description': 'If set to “remote”, the mouse pointer will be rendered remotely,',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#display-settings',
        'table': 'parameter'
    },
    'swap-red-blue': {
        'type': 'string',
        'description': 'The red and blue components of each color are swapped.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#display-settings',
        'table': 'parameter'
    },
    'force-lossless': {
        'type': 'boolean',
        'description': 'Whether this connection should only use lossless compression for graphical updates. ',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#rdp-display-settings',
        'table': 'parameter'
    },  
    'resize-method': {
        'type': 'string',
        'description': 'The method to use to update the RDP server when the width or height of the client display changes. ',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#rdp-display-settings',
        'table': 'parameter'
    },  
    'dpi': {
        'type': 'int',
        'description': 'The desired effective resolution of the client display, in DPI.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#rdp-display-settings',
        'table': 'parameter'
    },  
    'height': {
        'type': 'int',
        'description': 'The height of the display to request, in pixels.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#rdp-display-settings',
        'table': 'parameter'
    },  
    'width': {
        'type': 'int',
        'description': 'The width of the display to request, in pixels.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#rdp-display-settings',
        'table': 'parameter'
    },  
    'color-depth': {
        'type': 'int',
        'description': 'The color depth to request, in bits-per-pixel.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#display-settings',
        'table': 'parameter'
    },  
    'server-layout': {
        'type': 'string',
        'description': 'The server-side keyboard layout.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#session-settings',
        'table': 'parameter'
    },
    'initial-program': {
        'type': 'string',
        'description': 'The full path to the program to run immediately upon connecting.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#session-settings',
        'table': 'parameter'
    },
    'console': {
        'type': 'boolean',
        'description': 'If set to “true”, you will be connected to the console (admin) session of the RDP server.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#session-settings',
        'table': 'parameter'
    },
    'client-name': {
        'type': 'string',
        'description': 'If this parameter is specified, Guacamole will use its value as hostname.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#session-settings',
        'table': 'parameter'
    },
    'normalize-clipboard': {
        'type': 'string',
        'description': 'The type of line ending normalization to apply to text within the clipboard, if any.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#clipboard-normalization',
        'table': 'parameter'
    },
    'disable-auth': {
        'type': 'string',
        'description': 'If set to “true”, authentication will be disabled.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#authentication-and-security',
        'table': 'parameter'
    },
    'ignore-cert': {
        'type': 'string',
        'description': 'If set to “true”, the certificate returned by the server will be ignored.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#authentication-and-security',
        'table': 'parameter'
    },
    'security': {
        'type': 'string',
        'description': 'The security mode to use for the RDP connection: any|nla|nla-ext|tls|vmconnect|rdp',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#authentication-and-security',
        'table': 'parameter'
    },
    'domain': {
        'type': 'string',
        'description': 'The domain to use when attempting authentication, if any. This parameter is optional',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#authentication-and-security',
        'table': 'parameter'
    }
}
