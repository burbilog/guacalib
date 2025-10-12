# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.22] - 2025-10-12

### Added
- Comprehensive Google-style docstrings across entire codebase with Args, Returns, and Raises sections
- Complete API documentation generation with pdoc integration
- Type hints throughout the library for improved code maintainability
- Clickable IP address detection in documentation server (make docs-serve)
- Enhanced code formatting with Black integration

### Improved
- Developer experience with automatic documentation generation
- Code readability and IDE support with comprehensive type hints
- Documentation accessibility with live server and clickable URLs
- Code consistency with automated formatting tools

## [0.21] - 2025-10-11

### Fixed
- Fixed cleanup script regex pattern to properly remove orphaned temp_del_* usergroups
- Corrected test cleanup to handle both test_* and temp_del_* timestamp patterns
- Resolved issue where usergroups with id: None were not being cleaned up

## [0.20] - 2025-10-11

### Fixed
- Major documentation updates to align README with actual codebase capabilities
- Corrected SSH connection implementation status from "not fully implemented" to "basic support available"
- Fixed connection parameter count documentation (100+ → 50+ parameters)
- Added comprehensive --id parameter support documentation for all entity types
- Enhanced connection group permission management documentation
- Documented advanced validation features and cycle detection
- Added missing library methods and debug utilities documentation

### Improved
- README now accurately reflects ~95% of actual functionality
- Better organized documentation sections with clear examples
- Enhanced technical accuracy of feature descriptions
- Comprehensive coverage of atomic operations and transaction safety

## [0.19] - 2025-10-10

### Added
- Connection group permission management with --permit and --deny flags
- Connection and connection group operations by ID using --id parameter
- User group ID support for exists, delete, and modify commands
- Connection group connection management with --addconn-by-name/--addconn-by-id and --rmconn-by-name/--rmconn-by-id
- Enhanced test runner with comprehensive output and statistics
- Unified cleanup system with suppressible error messages
- Extended debug_permissions.py for connection group analysis

### Fixed
- ValidationError and parameter parsing improvements
- Enhanced cleanup and error handling in test workflows
- ID format validation for connections and connection groups

## [v0.18] - 2025-05-20

### Fixed
- License configuration in packaging metadata

## [v0.17] - 2025-05-20

### Fixed
- License configuration in project files

## [v0.15] - 2025-05-06

### Fixed
- Connection parameter discrepancies and descriptions
- Parameter validation fixes for various connection protocols
- Minor fixes in Guacamole parameter definitions

## [v0.14] - 2025-04-28

### Fixed
- Additional connection parameter fixes
- Enhancements to parameter handling in connection modification

## [v0.13] - 2025-04-24

### Added
- Significant expansion of supported Guacamole connection parameters
- Additional connection variables for modify command
- Support for resize-method, disable-auth, enable-full-window-drag parameters
- Missing sftp-host-key parameter support
- RULES.md file with guidelines for LLMs

### Fixed
- Connection parameter definitions and descriptions
- Parameter validation for various connection types

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
