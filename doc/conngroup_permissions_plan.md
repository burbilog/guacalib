# Connection Group Permissions — Implementation Plan

- [ ] **Stage 1: Define Failing Tests (TDD)**
  - [ ] Add CLI-level tests verifying new `conngroup` subcommands:
    - [ ] `conngroup permissions list --name GROUP` shows users/user groups with READ access.
    - [ ] `conngroup permissions grant --name GROUP --user USERNAME` inserts permission rows.
    - [ ] `conngroup permissions grant --name GROUP --group GROUPNAME` inserts permission rows.
    - [ ] `conngroup permissions revoke --name GROUP --user USERNAME` deletes permission rows.
    - [ ] `conngroup permissions revoke --name GROUP --group GROUPNAME` deletes permission rows.
  - [ ] Add DB-layer tests covering helpers that list/grant/revoke connection-group permissions:
    - [ ] `GuacamoleDB.list_connection_group_permissions(group_name: str) -> dict`
    - [ ] `GuacamoleDB.grant_connection_group_permission(entity_name: str, entity_type: str, group_name: str) -> None`
    - [ ] `GuacamoleDB.revoke_connection_group_permission(entity_name: str, entity_type: str, group_name: str) -> None`
  - [ ] Add tests ensuring `conngroup list` includes granted users/groups in its output (e.g., `permissions: [users, groups]`).

- [ ] **Stage 2: Library Enhancements**
  - [ ] Implement `GuacamoleDB.list_connection_group_permissions(group_name: str)` returning `{"users": [...], "groups": [...]}` with READ permissions.
  - [ ] Implement `GuacamoleDB.grant_connection_group_permission(entity_name: str, entity_type: Literal['USER', 'USER_GROUP'], group_name: str)` to insert `READ` permission (idempotent).
  - [ ] Implement `GuacamoleDB.revoke_connection_group_permission(entity_name: str, entity_type: Literal['USER', 'USER_GROUP'], group_name: str)` to delete `READ` permission.
  - [ ] Add private helper `_get_connection_group_entity_id(group_name: str) -> int` and reuse existing entity lookups for validation/error messaging.
  - [ ] Update existing connection-group listing routines to fetch permissions via `list_connection_group_permissions`.

- [ ] **Stage 3: CLI Updates**
  - [ ] Extend parser with nested subparsers under `conngroup permissions`:
    - `list` requires `--name`, optional `--format json|yaml` (default human-readable list).
    - `grant` requires `--name` plus exactly one of `--user` or `--group`.
    - `revoke` requires `--name` plus exactly one of `--user` or `--group`.
  - [ ] Implement `handle_conngroup_permissions_list(args, guacdb)` to call `list_connection_group_permissions` and print results.
  - [ ] Implement `handle_conngroup_permissions_grant(args, guacdb)` and `handle_conngroup_permissions_revoke(args, guacdb)` to dispatch to `GuacamoleDB` helpers with inferred `entity_type`.
  - [ ] Modify `handle_conngroup_command` to route `permissions` subcommands via a dedicated dispatcher (e.g., `handle_conngroup_permissions_command`).
  - [ ] Enhance `conngroup list` output to show `permissions:` section with `users:` / `groups:` lists.

- [ ] **Stage 4: Documentation & UX**
  - [ ] Update README/usage docs with examples for:
    - Listing connection-group permissions.
    - Granting/revoking permissions for both users and groups.
  - [ ] Add CLI help text describing new options and constraints (e.g., mutually-exclusive flags).
  - [ ] Mention TDD approach in contributing guidelines (optional) or note expected failing tests before implementation.
