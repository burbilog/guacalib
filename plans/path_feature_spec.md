# Hierarchical Path Feature Implementation Plan

## Goal
Allow unique identification of connections and connection groups using hierarchical paths (e.g. `ROOT/GroupA/SubGroup/ConnectionName`) to resolve naming conflicts in different hierarchies.

## Phases

### Phase 1: Test Infrastructure [PRE-WORK]
- [ ] Create test cases with duplicate names in different hierarchies:
  - Connections with same name in different groups
  - Connection groups with same name under different parents
  - 3-level nested structures
- [ ] Add validation tests for path syntax:
  - Empty path components
  - Invalid characters
  - Non-existent path components
- [ ] Verify current commands fail these tests (red teaming)

### Phase 2: List Command Enhancements
- [ ] Update connection listing to show full hierarchical paths:
  - Modify `list_connections_with_conngroups_and_parents()` to build paths
  - Add path construction logic during result processing
- [ ] Update connection group listing to show full hierarchies:
  - Enhance `list_connection_groups()` with recursive parent resolution
  - Format output as indented trees
- [ ] Modify CLI list commands to support:
  - `--show-paths` flag for hierarchical output
  - `--raw` flag to preserve original flat format

### Phase 3: Core Path Resolution
- [ ] Implement `get_connection_id_by_path(full_path)` helper:
  - Split path into components
  - Resolve parent group chain
  - Find connection by name+parent_group_id 
- [ ] Enhance `get_connection_group_id()` for multi-level paths:
  - Handle `/`-delimited paths
  - Add `ROOT` keyword support for absolute paths
- [ ] Create path validation helpers:
  - Reject empty path segments
  - Normalize leading/trailing slashes
  - Validate maximum path depth

### Phase 4: Command Argument Handling
- [ ] Add `--path` argument to all connection-related commands:
  - `conn new/delete/modify/exists`
  - `conngroup new/delete/modify/exists`
- [ ] Maintain `--name` argument as deprecated alias:
  - Show warnings when using `--name`
  - Auto-translate to equivalent path search in current context
- [ ] Update error messages:
  - Show available paths when name conflicts exist
  - Suggest nearest valid path when path not found

### Phase 5: Documentation & Validation
- [ ] Update README with new path-based examples:
  - Connection creation in specific hierarchies
  - Moving connections between groups via path
  - Complex group nesting examples
- [ ] Add developer docs for path resolution API
- [ ] Create troubleshooting guide for path issues:
  - Permission requirements for paths
  - Special character escaping
  - Maximum path length limits
