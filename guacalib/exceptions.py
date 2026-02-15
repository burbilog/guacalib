#!/usr/bin/env python3
"""Custom exceptions for Guacalib library.

This module defines a hierarchy of exceptions for better error handling
and more specific error messages throughout the library.
"""


class GuacalibError(Exception):
    """Base exception for all Guacalib errors."""

    pass


class DatabaseError(GuacalibError):
    """Exception raised for database-related errors."""

    pass


class EntityNotFoundError(GuacalibError):
    """Exception raised when an entity is not found in the database.

    Attributes:
        entity_type: Type of entity (user, usergroup, connection, connection_group)
        identifier: Name or ID that was not found
    """

    def __init__(self, entity_type: str, identifier: str, message: str = None):
        self.entity_type = entity_type
        self.identifier = identifier
        if message is None:
            message = f"{entity_type.capitalize()} '{identifier}' doesn't exist"
        super().__init__(message)


class ValidationError(GuacalibError):
    """Exception raised for validation errors.

    Attributes:
        field: Field that failed validation
        value: Value that was invalid
    """

    def __init__(self, message: str, field: str = None, value: str = None):
        self.field = field
        self.value = value
        super().__init__(message)


class PermissionError(GuacalibError):
    """Exception raised for permission-related errors.

    Attributes:
        username: User involved in the permission operation
        resource_type: Type of resource (connection, connection_group)
        resource_name: Name of the resource
    """

    def __init__(
        self,
        message: str,
        username: str = None,
        resource_type: str = None,
        resource_name: str = None,
    ):
        self.username = username
        self.resource_type = resource_type
        self.resource_name = resource_name
        super().__init__(message)


class ConfigurationError(GuacalibError):
    """Exception raised for configuration-related errors."""

    pass
