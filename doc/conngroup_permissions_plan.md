# Connection Group Permissions — Implementation Plan

- [ ] **Stage 1: Define Failing Tests (TDD)**
  - [ ] Add CLI-level tests verifying `conngroup modify` can grant/revoke group permissions for users and user groups.
  - [ ] Add DB-layer tests covering new helper methods for reading/granting/revoking connection-group permissions.
  - [ ] Add tests ensuring `conngroup list` shows the granted users/groups.

- [ ] **Stage 2: Library Enhancements**
  - [ ] Implement `GuacamoleDB` helpers to grant, revoke, and list connection-group permissions for users and user groups.
  - [ ] Update connection-group listing logic to include the new permission details.

- [ ] **Stage 3: CLI Updates**
  - [ ] Extend `conngroup modify` to accept `--permit-user`, `--deny-user`, `--permit-group`, and `--deny-group`.
  - [ ] Validate entity existence in CLI handlers and surface clear error messages.
  - [ ] Update `conngroup list` output to display current user and group permissions.

- [ ] **Stage 4: Documentation & UX**
  - [ ] Update README/usage docs with instructions on managing connection-group permissions.
  - [ ] Provide CLI help text updates that describe the new options.
