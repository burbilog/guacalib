# Phase 11.1 Analysis - Remaining SQL Functions Inventory

**Status**: ✅ **COMPLETED** - Complete SQL Function Identification and Categorization
**Date**: 2025-11-11
**Scope**: Identify all remaining embedded SQL functions in facade for extraction

---

## Executive Summary

Phase 11.1 analysis identified **19 remaining functions with embedded SQL queries** in the GuacamoleDB facade, totaling approximately **980 lines of SQL code**. While Phases 5-9 successfully extracted basic CRUD operations to repositories, significant embedded SQL remains in four distinct domains:

1. **Complex Permissions Logic** (4 functions, ~300 lines)
2. **Advanced ID Resolution** (3 functions, ~93 lines)
3. **Cross-Domain Reporting** (6 functions, ~345 lines)
4. **Specialized Operations** (6 functions, ~242 lines)

This analysis provides the foundation for Phase 11 execution with a prioritized extraction roadmap.

---

## Complete Inventory of Remaining SQL Functions

### **Permissions Domain (High Priority)**

#### 1. `grant_connection_group_permission_to_user(username, conngroup_name)`
**Location**: Lines 1869-1968 (~100 lines)
**Description**: Grant connection group permission to a user by name
**Current State**: Contains complex validation logic + embedded SQL
**Target**: Extract to `permissions_repo.py`

#### 2. `revoke_connection_group_permission_from_user(username, conngroup_name)`
**Location**: Lines 1970-1986 (~17 lines)
**Description**: Revoke connection group permission from user by name
**Current State**: Delegates to repository but has validation logic with SQL
**Target**: Extract to `permissions_repo.py`

#### 3. `grant_connection_group_permission_to_user_by_id(username, conngroup_id)`
**Location**: Lines 1999-2102 (~104 lines)
**Description**: Grant connection group permission to a user by ID
**Current State**: Nearly identical to name-based version but with ID-based SQL
**Target**: Extract to `permissions_repo.py`

#### 4. `revoke_connection_group_permission_from_user_by_id(username, conngroup_id)`
**Location**: Lines 2104-2181 (~78 lines)
**Description**: Revoke connection group permission from user by ID
**Current State**: ID-based version of revocation with complex validation
**Target**: Extract to `permissions_repo.py`

---

### **Advanced ID Resolution Domain (High Priority)**

#### 5. `get_usergroup_id(group_name)`
**Location**: Lines 463-501 (~39 lines)
**Description**: Get database ID for a user group by name
**Current State**: SQL queries mixed with facade logic
**Target**: Extract to `db_utils.py` with other resolvers

#### 6. `get_connection_group_id_by_name(group_name)`
**Location**: Lines 530-570 (~41 lines)
**Description**: Get connection group ID by name, handles empty names
**Current State**: SQL logic should be centralized with other resolvers
**Target**: Extract to `db_utils.py`

#### 7. `usergroup_exists_by_id(group_id)`
**Location**: Lines 1689-1701 (~13 lines)
**Description**: Check if user group exists by ID
**Current State**: Simple existence check that belongs in utilities
**Target**: Extract to `db_utils.py`

---

### **Cross-Domain Reporting Domain (Medium Priority)**

#### 8. `list_users_with_usergroups()`
**Location**: Lines 1127-1174 (~48 lines)
**Description**: List all users with their associated user group memberships
**Current State**: Complex JOIN query across user, group, and membership tables
**Target**: Extract to `reporting_repo.py` OR keep in facade

#### 9. `list_connections_with_conngroups_and_parents()`
**Location**: Lines 1176-1249 (~74 lines)
**Description**: List all connections with groups, parent group, and user permissions
**Current State**: Very complex multi-table JOIN with aggregations
**Target**: Extract to `reporting_repo.py` OR keep in facade

#### 10. `list_usergroups_with_users_and_connections()`
**Location**: Lines 1316-1395 (~80 lines)
**Description**: List all user groups with associated users and connections
**Current State**: Extremely complex cross-domain reporting with multiple JOINs
**Target**: Extract to `reporting_repo.py` OR keep in facade

#### 11. `get_connection_by_id(connection_id)`
**Location**: Lines 1251-1314 (~64 lines)
**Description**: Get specific connection by ID with permissions
**Current State**: Complex reporting query similar to list_connections
**Target**: Extract to `reporting_repo.py` OR keep in facade

#### 12. `list_connection_groups()`
**Location**: Lines 1542-1577 (~36 lines)
**Description**: List all connection groups with connections and parent groups
**Current State**: Hierarchical reporting with parent-child relationships
**Target**: Extract to `reporting_repo.py` OR keep in facade

#### 13. `get_connection_group_by_id(group_id)`
**Location**: Lines 1579-1620 (~42 lines)
**Description**: Get specific connection group by ID with connections
**Current State**: Single group reporting with connections
**Target**: Extract to `reporting_repo.py` OR keep in facade

---

### **Specialized Functions Domain (Low Priority)**

#### 14. `debug_connection_permissions(connection_name)`
**Location**: Lines 1773-1867 (~95 lines)
**Description**: Debug function to check and display permissions for a connection
**Current State**: Complex permission analysis for troubleshooting
**Target**: Keep in facade (debugging utility) OR extract to `reporting_repo.py`

#### 15. `modify_connection_parent_group()`
**Location**: Lines 572-639 (~68 lines)
**Description**: Set parent connection group for a connection with validation
**Current State**: Cross-domain operation (connections + groups) with SQL
**Target**: Extract to appropriate domain repository

#### 16. `modify_connection_group_parent()`
**Location**: Lines 1483-1540 (~58 lines)
**Description**: Set parent connection group with cycle detection
**Current State**: Cross-domain operation with validation and SQL
**Target**: Extract to appropriate domain repository

#### 17. `get_connection_group_id(group_path)`
**Location**: Lines 953-1018 (~66 lines)
**Description**: Resolve nested connection group path to connection group ID
**Current State**: Hierarchical path resolution with embedded SQL
**Target**: Extract to `db_utils.py` (advanced resolver)

#### 18. `delete_existing_usergroup_by_id(group_id)`
**Location**: Lines 771-830 (~60 lines)
**Description**: Delete a usergroup by ID and all associated data
**Current State**: Cascade delete by ID with complex SQL
**Target**: Extract to `usergroups_repo.py`

#### 19. `list_groups_with_users()`
**Location**: Lines 1727-1771 (~45 lines)
**Description**: List all user groups with associated users (simplified)
**Current State**: Cross-domain reporting but simpler than complex version
**Target**: Extract to `reporting_repo.py` OR keep in facade

---

## Extraction Priority Matrix

### **HIGH PRIORITY - Phase 11.2 & 11.3**

| Domain | Functions | Lines | Target Module | Justification |
|--------|------------|--------|----------------|---------------|
| **Permissions** | 4 | ~300 | `permissions_repo.py` | Completes permission domain consolidation |
| **ID Resolution** | 3 | ~93 | `db_utils.py` | Centralizes all resolver utilities |
| **High Priority Total** | **7** | **~393** | **40% of remaining SQL** |

**Risk Level**: 🟢 **Very Low** - Follows established repository patterns

---

### **MEDIUM PRIORITY - Phase 11.4**

| Domain | Functions | Lines | Target Options | Decision Required |
|--------|------------|--------|----------------|------------------|
| **Cross-Domain Reporting** | 6 | ~345 | Create `reporting_repo.py` OR keep in facade | Architecture decision point |
| **Medium Priority Total** | **6** | **~345** | **35% of remaining SQL** |

**Risk Level**: 🟡 **Medium** - Requires architectural decision on reporting functions

---

### **LOW PRIORITY - Phase 11.5**

| Domain | Functions | Lines | Target Module | Considerations |
|--------|------------|--------|----------------|----------------|
| **Specialized Operations** | 6 | ~242 | Domain-specific repositories or facade | Function-specific analysis required |
| **Low Priority Total** | **6** | **~242** | **25% of remaining SQL** |

**Risk Level**: 🟡 **Low to Medium** - Depends on individual function complexity

---

## Statistical Summary

| Category | Function Count | Line Count | Percentage |
|-----------|---------------|-------------|-------------|
| **Permission Functions** | 4 | ~300 | 31% |
| **ID Resolution Functions** | 3 | ~93 | 9% |
| **Cross-Domain Reporting** | 6 | ~345 | 35% |
| **Specialized Operations** | 6 | ~242 | 25% |
| **TOTALS** | **19** | **~980** | **100%** |

---

## Architectural Implications

### **Repository Enhancement Targets**
1. **`permissions_repo.py`**: Add ~300 lines of complex permission functions
2. **`db_utils.py`**: Add ~93 lines of advanced ID resolvers
3. **`reporting_repo.py`**: (NEW) Potentially ~345 lines of cross-domain queries

### **Decision Points for Phase 11.4**
- **Create new `reporting_repo.py`** vs **keep reporting functions in facade**
- Reporting functions are complex but serve orchestration purposes
- Arguments for new module: Clear separation, stateless repository pattern
- Arguments for facade: Orchestration coordination, complex business logic

### **Success Criteria**
✅ Complete inventory: **19 functions identified**
✅ Domain classification: **Permissions, Resolution, Reporting, Specialized**
✅ Priority matrix: **High/Medium/Low with clear criteria**
✅ Line count estimates: **~980 lines of embedded SQL**
✅ Extraction roadmap: **Phases 11.2-11.5 defined**

---

## Next Steps (Phase 11.2)

**Target**: Extract remaining permission functions to `permissions_repo.py`
- `grant_connection_group_permission_to_user()` (100 lines)
- `grant_connection_group_permission_to_user_by_id()` (104 lines)
- `revoke_connection_group_permission_from_user()` (17 lines)
- `revoke_connection_group_permission_from_user_by_id()` (78 lines)

**Expected Outcome**:
- Enhanced `permissions_repo.py` with complete permission domain
- Thin delegation wrappers in facade (~16 lines total)
- 300 lines removed from facade to repository

**Risk Level**: 🟢 **Very Low** - Follows established Phase 9 pattern

---

*Phase 11.1 Analysis Complete*