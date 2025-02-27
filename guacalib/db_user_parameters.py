USER_PARAMETERS = {
    'disabled': {
        'type': 'tinyint',
        'description': 'Whether the user is disabled (0=enabled, 1=disabled)',
        'default': '0'
    },
    'expired': {
        'type': 'tinyint',
        'description': 'Whether the user account is expired (0=active, 1=expired)',
        'default': '0'
    },
    'access_window_start': {
        'type': 'time',
        'description': 'Start of allowed access time window (HH:MM:SS)',
        'default': 'NULL'
    },
    'access_window_end': {
        'type': 'time',
        'description': 'End of allowed access time window (HH:MM:SS)',
        'default': 'NULL'
    },
    'valid_from': {
        'type': 'date',
        'description': 'Date when account becomes valid (YYYY-MM-DD)',
        'default': 'NULL'
    },
    'valid_until': {
        'type': 'date',
        'description': 'Date when account expires (YYYY-MM-DD)',
        'default': 'NULL'
    },
    'timezone': {
        'type': 'string',
        'description': 'User\'s timezone (e.g., "America/New_York")',
        'default': 'NULL'
    },
    'full_name': {
        'type': 'string',
        'description': 'User\'s full name',
        'default': 'NULL'
    },
    'email_address': {
        'type': 'string',
        'description': 'User\'s email address',
        'default': 'NULL'
    },
    'organization': {
        'type': 'string',
        'description': 'User\'s organization',
        'default': 'NULL'
    },
    'organizational_role': {
        'type': 'string',
        'description': 'User\'s role within the organization',
        'default': 'NULL'
    }
}
