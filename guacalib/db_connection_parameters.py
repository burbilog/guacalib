
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
    'autoretry': {
        'type': 'int',
        'description': 'Seconds to wait before retrying connection on failure.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#network-parameters',
        'table': 'parameter'
    },
    'enable-sftp': {
        'type': 'string',
        'description': 'Whether file transfer should be enabled.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-hostname': {
        'type': 'string',
        'description': 'Hostname of the SFTP server.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-port': {
        'type': 'int',
        'description': 'Port of the SFTP server.',
        'default': '22',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-host-key': {
        'type': 'string',
        'description': 'The known hosts entry for the SFTP server.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-username': {
        'type': 'string',
        'description': 'Username for SFTP authentication.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-password': {
        'type': 'string',
        'description': 'Password for SFTP authentication.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-private-key': {
        'type': 'string',
        'description': 'Private key for SFTP authentication.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-passphrase': {
        'type': 'string',
        'description': 'Passphrase for SFTP private key.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'sftp-directory': {
        'type': 'string',
        'description': 'Directory to expose via SFTP.',
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
    'font-name': {
        'type': 'string',
        'description': 'Font to use for SSH terminal.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#terminal-display-settings',
        'table': 'parameter'
    },
    'font-size': {
        'type': 'int',
        'description': 'Font size in points for SSH terminal.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#terminal-display-settings',
        'table': 'parameter'
    },
    'scrollback': {
        'type': 'int',
        'description': 'Number of lines in SSH terminal scrollback buffer.',
        'default': '1000',
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
        'default': 'NULL',
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
        'type': 'boolean',
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
    },
    'gateway-hostname': {
        'type': 'string',
        'description': 'Hostname of the RD Gateway server.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#remote-desktop-gateway',
        'table': 'parameter'
    },
    'gateway-port': {
        'type': 'int',
        'description': 'Port of the RD Gateway server.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#remote-desktop-gateway',
        'table': 'parameter'
    },
    'gateway-username': {
        'type': 'string',
        'description': 'Username for RD Gateway authentication.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#remote-desktop-gateway',
        'table': 'parameter'
    },
    'gateway-password': {
        'type': 'string',
        'description': 'Password for RD Gateway authentication.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#remote-desktop-gateway',
        'table': 'parameter'
    },
    'gateway-domain': {
        'type': 'string',
        'description': 'Domain for RD Gateway authentication.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#remote-desktop-gateway',
        'table': 'parameter'
    },
    'preconnection-id': {
        'type': 'int',
        'description': 'Integer ID for preconnection PDU.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#preconnection-pdu-hyper-v-vmconnect',
        'table': 'parameter'
    },
    'preconnection-blob': {
        'type': 'string',
        'description': 'String blob for preconnection PDU.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#preconnection-pdu-hyper-v-vmconnect',
        'table': 'parameter'
    },
    'remote-app': {
        'type': 'string',
        'description': 'RemoteApp program alias to launch.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#remoteapp',
        'table': 'parameter'
    },
    'remote-app-dir': {
        'type': 'string',
        'description': 'Working directory for the RemoteApp.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#remoteapp',
        'table': 'parameter'
    },
    'remote-app-args': {
        'type': 'string',
        'description': 'Arguments for the RemoteApp.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#remoteapp',
        'table': 'parameter'
    },
    'enable-wallpaper': {
        'type': 'boolean',
        'description': 'Enable desktop wallpaper in RDP session.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'enable-theming': {
        'type': 'boolean',
        'description': 'Enable theming of windows and controls.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'enable-font-smoothing': {
        'type': 'boolean',
        'description': 'Enable font smoothing (ClearType).',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'enable-full-window-drag': {
        'type': 'boolean',
        'description': 'Enable full window drag (show contents while dragging).',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'enable-desktop-composition': {
        'type': 'boolean',
        'description': 'Enable desktop composition (Aero).',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'enable-menu-animations': {
        'type': 'boolean',
        'description': 'Enable menu animations.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'username-regex': {
        'type': 'string',
        'description': 'Regular expression for detecting username prompt in telnet.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#telnet-authentication',
        'table': 'parameter'
    },
    'password-regex': {
        'type': 'string',
        'description': 'Regular expression for detecting password prompt in telnet.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#telnet-authentication',
        'table': 'parameter'
    },
    'login-success-regex': {
        'type': 'string',
        'description': 'Regular expression for detecting successful login in telnet.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#telnet-authentication',
        'table': 'parameter'
    },
    'login-failure-regex': {
        'type': 'string',
        'description': 'Regular expression for detecting failed login in telnet.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#telnet-authentication',
        'table': 'parameter'
    },
    'load-balance-info': {
        'type': 'string',
        'description': 'Load balancing information for RDP connection brokers.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#load-balancing-and-rdp-connection-brokers',
        'table': 'parameter'
    },
    'disable-bitmap-caching': {
        'type': 'boolean',
        'description': 'Disable RDP bitmap caching functionality.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'disable-offscreen-caching': {
        'type': 'boolean',
        'description': 'Disable caching of offscreen regions.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'disable-glyph-caching': {
        'type': 'boolean',
        'description': 'Disable caching of frequently used symbols/fonts. DISABLED, see GUACAMOLE-1191.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#performance-flags',
        'table': 'parameter'
    },
    'container': {
        'type': 'string',
        'description': 'Name of Kubernetes container to attach to.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#network-container-parameters',
        'table': 'parameter'
    },
    'exec-command': {
        'type': 'string',
        'description': 'Command to run in Kubernetes container.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#network-container-parameters',
        'table': 'parameter'
    },
    'namespace': {
        'type': 'string',
        'description': 'Kubernetes namespace of the pod.',
        'default': 'default',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#network-container-parameters',
        'table': 'parameter'
    },
    'sftp-server-alive-interval': {
        'type': 'int',
        'description': 'Interval in seconds to send keepalive packets to SFTP server.',
        'default': '0',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#sftp',
        'table': 'parameter'
    },
    'wol-send-packet': {
        'type': 'boolean',
        'description': 'Send Wake-on-LAN packet before connecting.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#wake-on-lan',
        'table': 'parameter'
    },
    'wol-mac-addr': {
        'type': 'string',
        'description': 'MAC address for Wake-on-LAN packet.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#wake-on-lan',
        'table': 'parameter'
    },
    'wol-broadcast-addr': {
        'type': 'string',
        'description': 'Broadcast address for Wake-on-LAN packet.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#wake-on-lan',
        'table': 'parameter'
    },
    'wol-udp-port': {
        'type': 'int',
        'description': 'UDP port for Wake-on-LAN packet.',
        'default': '9',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#wake-on-lan',
        'table': 'parameter'
    },
    'wol-wait-time': {
        'type': 'int',
        'description': 'Seconds to wait after sending Wake-on-LAN packet.',
        'default': '0',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#wake-on-lan',
        'table': 'parameter'
    },
    # Session recording (typescript)
    'typescript-path': {
        'type': 'string',
        'description': 'Directory in which typescript files should be created.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#text-session-recording-typescripts',
        'table': 'parameter'
    },
    'create-typescript-path': {
        'type': 'boolean',
        'description': 'If true, automatically create the typescript-path directory if it does not exist.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#text-session-recording-typescripts',
        'table': 'parameter'
    },
    'typescript-name': {
        'type': 'string',
        'description': 'Base filename for typescript data and timing files.',
        'default': 'typescript',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#text-session-recording-typescripts',
        'table': 'parameter'
    },
    # Session recording (graphical)
    'recording-path': {
        'type': 'string',
        'description': 'Directory in which screen recording files should be created.',
        'default': 'NULL',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#graphical-session-recording',
        'table': 'parameter'
    },
    'create-recording-path': {
        'type': 'boolean',
        'description': 'If true, automatically create the recording-path directory if it does not exist.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#graphical-session-recording',
        'table': 'parameter'
    },
    'recording-name': {
        'type': 'string',
        'description': 'Filename to use for created recordings.',
        'default': 'recording',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#graphical-session-recording',
        'table': 'parameter'
    },
    'recording-exclude-output': {
        'type': 'boolean',
        'description': 'If true, exclude graphical output from the recording.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#graphical-session-recording',
        'table': 'parameter'
    },
    'recording-exclude-mouse': {
        'type': 'boolean',
        'description': 'If true, exclude mouse events from the recording.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#graphical-session-recording',
        'table': 'parameter'
    },
    'recording-include-keys': {
        'type': 'boolean',
        'description': 'If true, include key events in the recording.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#graphical-session-recording',
        'table': 'parameter'
    },

    # Common options
    'disable-copy': {
        'type': 'boolean',
        'description': 'If set to true, disables copying from the remote clipboard to the client.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#disabling-clipboard-access',
        'table': 'parameter'
    },
    'disable-paste': {
        'type': 'boolean',
        'description': 'If set to true, disables pasting from the client clipboard to the remote session.',
        'default': 'false',
        'ref': 'https://guacamole.apache.org/doc/gug/configuring-guacamole.html#disabling-clipboard-access',
        'table': 'parameter'
    }
}
