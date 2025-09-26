# Connection Group Permissions — Implementation Plan

- [ ] **Stage 1: Define Failing Tests (TDD)**
  - [ ] Add CLI-level tests verifying new `conngroup` subcommands:
    - [ ] `conngroup permissions list --name GROUP` shows users/user groups with READ access.
    - [ ] `conngroup permissions grant --name GROUP --user USERNAME` inserts permission rows.
    - [ ] `conngroup permissions grant --name GROUP --group GROUPNAME` inserts permission rows.
    - [ ] `conngroup permissions revoke --name GROUP --user USERNAME` deletes permission rows.
    - [ ] `conngroup permissions revoke --name GROUP --group GROUPNAME` deletes permission rows.
  - [ ] Add CLI tests covering `conngroup modify --permit-user/--deny-user/--permit-group/--deny-group`.
  - [ ] Add DB-layer tests covering helpers that list/grant/revoke connection-group permissions.
  - [ ] Add tests ensuring `conngroup list` includes granted users/groups in its output.

- [ ] **Stage 2: Library Enhancements**
  - [ ] Implement `GuacamoleDB` helpers to grant, revoke, and list connection-group permissions for users and user groups.
  - [ ] Ensure helpers validate entity existence and avoid duplicate inserts.
  - [ ] Update connection-group listing logic to include user and group permissions.

- [ ] **Stage 3: CLI Updates**
  - [ ] Extend parser to include new `conngroup permissions` subcommands:
    - `list` (read-only view)
    - `grant` with `--user`/`--group`
    - `revoke` with `--user`/`--group`
  - [ ] Extend `conngroup modify` to accept `--permit-user`, `--deny-user`, `--permit-group`, `--deny-group`.
  - [ ] Validate entity existence in CLI handlers and surface clear error messages.
  - [ ] Update `conngroup list` output to display current user and group permissions.

- [ ] **Stage 4: Documentation & UX**
  - [ ] Update README/usage docs with instructions on using `conngroup permissions` subcommands and modify flags.
  - [ ] Provide CLI help text updates that describe the new options and expected behaviors.
