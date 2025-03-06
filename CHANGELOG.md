# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.12] - 2025-03-01

### Added
- Connection group cycle detection with new helper method
- Enhanced tests for group creation/modification scenarios
- Improved debug logging for group operations
- Added more Guacamole connection variables to the available parameters that can be modified via command-line interface

### Fixed
- Potential cycle creation in group hierarchies
- Error handling for invalid group operations

## [v0.11] - 2025-02-28

### Added
- Initial changelog file

## [v0.10] - 2025-02-28

### Added
- Connection group management commands
- Enhanced permission debugging tools
- YAML dump functionality for database state
- Colorized output for connection modify command
- Private-key support in connection parameters

### Fixed
- Connection permission handling bugs
- User group membership validation
- Test fixes for permission revocation

## [v0.9] - 2025-02-27

### Added
- More settable variables for connection options
- User and connection parameters moved to separate files
- Reference URL display for connection parameters
- Color initialization at module level

### Fixed
- Parameter display format standardization
- Documentation improvements

## [v0.8] - 2025-02-26

### Added
- Connection permission management with permit/deny flags
- Username parameter to connection schema
- Password change functionality
- Comprehensive connection modify tests

### Fixed
- Documentation formatting and clarity
- Connection group management fixes

## [v0.7] - 2025-02-23

### Added
- Centralized user parameter management
- User modify subcommand
- Renamed vconn to conn with connection type option

### Fixed
- Publishing fixes and version management

## [v0.6] - 2025-02-23

### Added
- Version section and single source version management
- Makefile with publishing commands

### Fixed
- Documentation fixes

## [v0.5] - 2025-02-23

### Added
- PyPI publishing support
- Comprehensive .gitignore

### Fixed
- Config file permission checks
- Security documentation updates

## [v0.4] - 2025-02-23

### Added
- Version command and documentation
- BATS test suite
- Debug mode with --debug flag

### Fixed
- User and connection existence checks
- Group management improvements

## [v0.3] - 2025-02-23

### Added
- Dump command for YAML output
- List commands output as YAML
- Multiple group support in user creation

### Fixed
- Password hashing implementation
- SQL query improvements

## [v0.2] - 2025-02-23

### Added
- Connection group support
- VNC connection management
- User deletion functionality

### Fixed
- Database transaction handling
- Error handling improvements

## [v0.1] - 2025-02-22

### Added
- Initial release with basic user/group management
- CLI interface with subcommands
- Database configuration support
- README documentation

### Fixed
- Initial bug fixes and stability improvements
