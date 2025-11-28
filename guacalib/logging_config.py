"""Logging configuration for guacalib package.

This module provides centralized logging configuration for the guacalib
library and CLI application, with proper handling for duplicate handlers
to support both library usage and CLI invocation scenarios.
"""

import logging
import os
import sys


def setup_logging(debug: bool = False, force_reconfigure: bool = False) -> None:
    """Configure logging for guacalib package with duplicate handler prevention.

    This function sets up logging configuration for the guacalib package.
    It includes guards against duplicate handlers to support repeated
    invocations and library usage scenarios. This function is idempotent
    and can be called multiple times safely.

    Args:
        debug: If True, set logging level to DEBUG; otherwise use WARNING.
               Ignored if GUACALIB_LOG_LEVEL environment variable is set.
        force_reconfigure: If True, remove existing handlers before configuration.
                         Used for testing and special scenarios.

    Note:
        - Function is idempotent - safe to call multiple times
        - Prevents duplicate handlers by checking existing handlers
        - **Important**: Does NOT modify root logger handlers - respects host application configuration
        - Only manages guacalib-specific handlers to avoid interference with embedding applications
        - Configures both guacalib root logger and module-specific loggers
        - Uses stderr for log output to preserve stdout for user-facing data
        - Must be called explicitly - never configured on import
        - **Phase 4**: Supports GUACALIB_LOG_LEVEL and GUACALIB_LOG_FORMAT environment variables

    Environment Variables:
        GUACALIB_LOG_LEVEL: Override logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        GUACALIB_LOG_FORMAT: Override log format string
                            Example: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    Example:
        >>> # CLI usage (called from cli.main after parsing --debug)
        >>> setup_logging(debug=True)
        >>>
        >>> # Library usage with custom configuration
        >>> setup_logging(debug=False)
        >>> logger = logging.getLogger('guacalib.db')
        >>> logger.info("Database operation completed")
        >>>
        >>> # Environment variable usage
        >>> # export GUACALIB_LOG_LEVEL=DEBUG
        >>> # export GUACALIB_LOG_FORMAT='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        >>> setup_logging()
    """
    # Phase 4: Check for environment variable overrides
    env_log_level = os.environ.get("GUACALIB_LOG_LEVEL", "").upper()
    env_log_format = os.environ.get("GUACALIB_LOG_FORMAT", "")

    # Determine logging level with environment variable support
    if env_log_level:
        # Map environment variable to logging level
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if env_log_level in level_mapping:
            level = level_mapping[env_log_level]
        else:
            # Invalid environment variable - fallback to debug parameter
            # and print warning to stderr (since logging isn't configured yet)
            print(
                f"Warning: Invalid GUACALIB_LOG_LEVEL '{env_log_level}'. Using debug={debug} instead.",
                file=sys.stderr,
            )
            level = logging.DEBUG if debug else logging.WARNING
    else:
        # No environment variable override - use debug parameter
        level = logging.DEBUG if debug else logging.WARNING

    # Get the guacalib root logger
    logger = logging.getLogger("guacalib")

    # Check if already configured to avoid duplicate handlers
    if logger.handlers and not force_reconfigure:
        return

    # Remove any existing handlers if forcing reconfiguration
    if force_reconfigure:
        logger.handlers.clear()

    # **Important**: Do NOT remove root logger handlers - respect host application's logging configuration
    # Only manage guacalib-specific handlers to avoid interfering with embedding applications

    logger.setLevel(level)

    # Create handler for stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Phase 4: Create formatter based on environment variables or debug mode
    if env_log_format:
        # Use custom format from environment variable
        try:
            formatter = logging.Formatter(env_log_format)
        except (ValueError, TypeError) as e:
            # Invalid format string - fallback to debug mode
            print(
                f"Warning: Invalid GUACALIB_LOG_FORMAT '{env_log_format}'. Using debug={debug} format instead. Error: {e}",
                file=sys.stderr,
            )
            if debug:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            else:
                formatter = logging.Formatter("%(levelname)s: %(message)s")
    else:
        # Use default format based on debug mode
        if debug:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        else:
            formatter = logging.Formatter("%(levelname)s: %(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplication
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific guacalib module.

    Args:
        name: The module name (e.g., 'db', 'cli', 'cli_handle_user')

    Returns:
        A configured logger instance for the specified module.

    Example:
        >>> logger = get_logger('db')
        >>> logger.debug("Executing SQL query")

    Note:
        This helper function must follow AGENTS.md requirements:
        - Includes proper type hints and Google-style docstrings
        - Uses clear, meaningful function names
        - Handles parameters appropriately
        - Follows single-responsibility principle
    """
    return logging.getLogger(f"guacalib.{name}")
