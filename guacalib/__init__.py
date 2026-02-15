from .db import GuacamoleDB
from .version import VERSION
from .repositories.connection_parameters import CONNECTION_PARAMETERS
from .repositories.user_parameters import USER_PARAMETERS
from .exceptions import (
    GuacalibError,
    DatabaseError,
    EntityNotFoundError,
    ValidationError,
    PermissionError,
    ConfigurationError,
)

__version__ = VERSION
__all__ = [
    "GuacamoleDB",
    "CONNECTION_PARAMETERS",
    "USER_PARAMETERS",
    "GuacalibError",
    "DatabaseError",
    "EntityNotFoundError",
    "ValidationError",
    "PermissionError",
    "ConfigurationError",
]
