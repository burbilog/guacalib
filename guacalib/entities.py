#!/usr/bin/env python3
"""Entity type constants for Guacamole database."""

from enum import Enum


class EntityType(Enum):
    """Entity types in Guacamole database.

    These correspond to the 'type' column in the guacamole_entity table.
    """

    USER = "USER"
    USER_GROUP = "USER_GROUP"


# Convenience constants for direct string access
ENTITY_TYPE_USER = EntityType.USER.value
ENTITY_TYPE_USER_GROUP = EntityType.USER_GROUP.value
