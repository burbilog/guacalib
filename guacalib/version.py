"""Guacamole library version information.

This module defines the version string for the Guacamole management library
(guacalib). The version follows semantic versioning conventions and is used
throughout the library for identification, compatibility checks, and user-facing
displays.

The version number is incremented according to the following rules:
- MAJOR version: Incompatible API changes
- MINOR version: Backward-compatible functionality additions
- PATCH version: Backward-compatible bug fixes

This constant is imported by other modules to provide version information
in CLI help text, logging, and error messages.
"""

from typing import Final

VERSION: Final[str] = "0.22"
"""Current version of the Guacamole management library.

This string represents the current version of guacalib in the format
"MAJOR.MINOR.PATCH" according to semantic versioning conventions.

The version string is used throughout the library for:
- CLI help text and version command output
- Package metadata and distribution
- Compatibility checking and debugging
- User-facing error messages and logging

Example:
    >>> from guacalib import VERSION
    >>> print(f"Guacamole Library Version: {VERSION}")
    Guacamole Library Version: 0.21
"""
