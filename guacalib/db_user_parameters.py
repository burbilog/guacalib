"""Guacamole user parameter definitions and validation.

This module defines all supported user account parameters for Apache Guacamole
user management, including their data types, descriptions, default values, and
validation rules. These parameters control user account behavior, access restrictions,
and personalization settings.

The parameters are stored in the guacamole_user table and provide fine-grained
control over user accounts including:
- Account status (disabled/expired state)
- Access time windows and validity periods
- Personal information (name, email, organization)
- Timezone and locale preferences

This module serves as the authoritative source for all user parameter
definitions used throughout the Guacamole management system.
"""

from typing import Dict, Any

UserParameters = Dict[str, Dict[str, Any]]

USER_PARAMETERS: UserParameters = {
    """Dictionary defining all supported Guacamole user account parameters.

    Each parameter entry contains the following keys:
        - type: MySQL data type for storing the parameter
        - description: Human-readable description of the parameter's purpose
        - default: Default value when parameter is not specified

    The parameters are organized by functional categories:
    - Account status parameters (disabled, expired)
    - Access control parameters (time windows, validity periods)
    - Personal information parameters (name, email, organization)
    - Localization parameters (timezone, locale settings)
    """
    "disabled": {
        "type": "tinyint",
        "description": "Whether the user is disabled (0=enabled, 1=disabled)",
        "default": "0",
    },
    "expired": {
        "type": "tinyint",
        "description": "Whether the user account is expired (0=active, 1=expired)",
        "default": "0",
    },
    "access_window_start": {
        "type": "time",
        "description": "Start of allowed access time window (HH:MM:SS)",
        "default": "NULL",
    },
    "access_window_end": {
        "type": "time",
        "description": "End of allowed access time window (HH:MM:SS)",
        "default": "NULL",
    },
    "valid_from": {
        "type": "date",
        "description": "Date when account becomes valid (YYYY-MM-DD)",
        "default": "NULL",
    },
    "valid_until": {
        "type": "date",
        "description": "Date when account expires (YYYY-MM-DD)",
        "default": "NULL",
    },
    "timezone": {
        "type": "string",
        "description": 'User\'s timezone (e.g., "America/New_York")',
        "default": "NULL",
    },
    "full_name": {
        "type": "string",
        "description": "User's full name",
        "default": "NULL",
    },
    "email_address": {
        "type": "string",
        "description": "User's email address",
        "default": "NULL",
    },
    "organization": {
        "type": "string",
        "description": "User's organization",
        "default": "NULL",
    },
    "organizational_role": {
        "type": "string",
        "description": "User's role within the organization",
        "default": "NULL",
    },
}
