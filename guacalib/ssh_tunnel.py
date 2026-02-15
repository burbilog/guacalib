#!/usr/bin/env python3
"""SSH tunnel management for Guacamole database connections."""

# SSH tunnel support
try:
    from sshtunnel import SSHTunnelForwarder

    SSH_TUNNEL_AVAILABLE = True
except ImportError:
    SSH_TUNNEL_AVAILABLE = False
    SSHTunnelForwarder = None


def create_ssh_tunnel(ssh_tunnel_config, db_config, debug_print=None):
    """Create and start SSH tunnel for database connection.

    Args:
        ssh_tunnel_config: SSH tunnel configuration dictionary with keys:
            - host: SSH gateway hostname
            - port: SSH port
            - user: SSH username
            - password: SSH password (optional, if using key)
            - private_key: Path to SSH private key (optional, if using password)
            - private_key_passphrase: Passphrase for encrypted key (optional)
        db_config: Database configuration dictionary (will be modified)
        debug_print: Optional debug print function

    Returns:
        tuple: (SSHTunnelForwarder object, modified db_config)

    Raises:
        ImportError: If sshtunnel package is not installed
        RuntimeError: If SSH tunnel creation fails
    """
    if not SSH_TUNNEL_AVAILABLE:
        raise ImportError(
            "sshtunnel package is required for SSH tunnel support. "
            "Install it with: pip install sshtunnel"
        )

    db_config = db_config.copy()

    # Build SSH tunnel configuration
    tunnel_config = {
        "ssh_address_or_host": (
            ssh_tunnel_config["host"],
            ssh_tunnel_config["port"],
        ),
        "ssh_username": ssh_tunnel_config["user"],
        "remote_bind_address": (db_config["host"], 3306),
    }

    # Add authentication method
    if ssh_tunnel_config.get("private_key"):
        tunnel_config["ssh_pkey"] = ssh_tunnel_config["private_key"]
        if ssh_tunnel_config.get("private_key_passphrase"):
            tunnel_config["ssh_pkey_password"] = ssh_tunnel_config[
                "private_key_passphrase"
            ]
    elif ssh_tunnel_config.get("password"):
        tunnel_config["ssh_password"] = ssh_tunnel_config["password"]

    try:
        if debug_print:
            debug_print(f"Creating SSH tunnel to {ssh_tunnel_config['host']}")
        ssh_tunnel = SSHTunnelForwarder(**tunnel_config)
        ssh_tunnel.start()

        # Update MySQL config to use tunnel
        db_config["host"] = "127.0.0.1"
        db_config["port"] = ssh_tunnel.local_bind_port

        if debug_print:
            debug_print(f"SSH tunnel established on port {ssh_tunnel.local_bind_port}")

        return ssh_tunnel, db_config
    except Exception as e:
        raise RuntimeError(f"Failed to create SSH tunnel: {e}") from e


def close_ssh_tunnel(ssh_tunnel, debug_print=None):
    """Close SSH tunnel safely.

    Args:
        ssh_tunnel: SSHTunnelForwarder object to close
        debug_print: Optional debug print function
    """
    if ssh_tunnel:
        try:
            ssh_tunnel.stop()
            if debug_print:
                debug_print("SSH tunnel closed")
        except Exception:
            pass
