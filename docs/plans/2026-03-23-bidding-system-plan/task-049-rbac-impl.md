# Task 049: Role-Based Access Control (RBAC) Implementation

## Task Header

| Field | Value |
|-------|-------|
| ID | 049 |
| Name | RBAC Implementation |
| Type | impl |
| Dependencies | 048 (RBAC Tests) |
| Status | pending |

## Description

Implement the Role-Based Access Control (RBAC) module for the bidding system. This includes role definitions, permission management, role assignment to users, and middleware for enforcing access control on API endpoints.

## Files to Create/Modify

### New Files
1. `src/auth/rbac/types.ts` - TypeScript types for RBAC
2. `src/auth/rbac/roles.ts` - Role definitions and constants
3. `src/auth/rbac/permissions.ts` - Permission definitions
4. `src/auth/rbac/role-service.ts` - Role management service
5. `src/auth/rbac/permission-service.ts` - Permission checking service
6. `src/auth/rbac/rbac-middleware.ts` - Express/Fastify middleware
7. `src/auth/rbac/index.ts` - Module exports

### Modified Files
8. `src/auth/models/user.ts` - Add role fields to user model
9. `src/database/migrations/004_add_roles.ts` - Database migration for roles
10. `src/auth/routes.ts` - Add role management endpoints

## Implementation Steps

### Step 1: Define Types and Constants

Create `src/auth/rbac/types.ts`:

```typescript
export enum Role {
  ADMIN = 'admin',
  MANAGER = 'manager',
  BIDDER = 'bidder',
  VIEWER = 'viewer'
}

export enum Permission {
  // User management
  USER_READ = 'user:read',
  USER_CREATE = 'user:create',
  USER_UPDATE = 'user:update',
  USER_DELETE = 'user:delete',

  // Project/Bid management
  PROJECT_READ = 'project:read',
  PROJECT_CREATE = 'project:create',
  PROJECT_UPDATE = 'project:update',
  PROJECT_DELETE = 'project:delete',

  // Bid operations
  BID_READ = 'bid:read',
  BID_CREATE = 'bid:create',
  BID_UPDATE = 'bid:update',
  BID_DELETE = 'bid:delete',

  // Reporting
  REPORT_READ = 'report:read',
  REPORT_CREATE = 'report:create',

  // System
  SYSTEM_ADMIN = 'system:admin'
}

export interface UserRole {
  userId: string;
  role: Role;
  assignedAt: Date;
  assignedBy: string;
}

export interface RolePermissions {
  role: Role;
  permissions: Permission[];
}

export interface AccessCheckResult {
  granted: boolean;
  reason?: string;
  requiredPermission?: Permission;
}
```

### Step 2: Define Role-Permission Mappings

Create `src/auth/rbac/permissions.ts`:

```typescript
import { Role, Permission } from './types';

export const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  [Role.ADMIN]: [
    Permission.SYSTEM_ADMIN,
    Permission.USER_READ,
    Permission.USER_CREATE,
    Permission.USER_UPDATE,
    Permission.USER_DELETE,
    Permission.PROJECT_READ,
    Permission.PROJECT_CREATE,
    Permission.PROJECT_UPDATE,
    Permission.PROJECT_DELETE,
    Permission.BID_READ,
    Permission.BID_CREATE,
    Permission.BID_UPDATE,
    Permission.BID_DELETE,
    Permission.REPORT_READ,
    Permission.REPORT_CREATE
  ],
  [Role.MANAGER]: [
    Permission.USER_READ,
    Permission.PROJECT_READ,
    Permission.PROJECT_CREATE,
    Permission.PROJECT_UPDATE,
    Permission.BID_READ,
    Permission.BID_UPDATE,
    Permission.REPORT_READ,
    Permission.REPORT_CREATE
  ],
  [Role.BIDDER]: [
    Permission.PROJECT_READ,
    Permission.BID_READ,
    Permission.BID_CREATE,
    Permission.BID_UPDATE
  ],
  [Role.VIEWER]: [
    Permission.PROJECT_READ,
    Permission.BID_READ,
    Permission.REPORT_READ
  ]
};

export function getPermissionsForRole(role: Role): Permission[] {
  return ROLE_PERMISSIONS[role] || [];
}

export function hasPermission(role: Role, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}
```

### Step 3: Implement Role Service

Create `src/auth/rbac/role-service.ts`:

```typescript
import { Role, UserRole } from './types';
import { Database } from '../../database';

export class RoleService {
  private db: Database;

  constructor(database: Database) {
    this.db = database;
  }

  async assignRole(userId: string, role: Role, assignedBy: string): Promise<UserRole> {
    // Implementation
  }

  async removeRole(userId: string, role: Role): Promise<void> {
    // Implementation
  }

  async getUserRoles(userId: string): Promise<Role[]> {
    // Implementation
  }

  async hasRole(userId: string, role: Role): Promise<boolean> {
    // Implementation
  }

  async getUsersWithRole(role: Role): Promise<string[]> {
    // Implementation
  }
}
```

### Step 4: Implement Permission Service

Create `src/auth/rbac/permission-service.ts`:

```typescript
import { Role, Permission, AccessCheckResult } from './types';
import { hasPermission, getPermissionsForRole } from './permissions';

export class PermissionService {
  async checkPermission(
    userRoles: Role[],
    requiredPermission: Permission
  ): Promise<AccessCheckResult> {
    // Implementation with role hierarchy support
  }

  async checkAnyPermission(
    userRoles: Role[],
    requiredPermissions: Permission[]
  ): Promise<AccessCheckResult> {
    // Implementation
  }

  async checkAllPermissions(
    userRoles: Role[],
    requiredPermissions: Permission[]
  ): Promise<AccessCheckResult> {
    // Implementation
  }

  getUserPermissions(roles: Role[]): Permission[] {
    // Implementation with caching
  }
}
```

### Step 5: Implement RBAC Middleware

Create `src/auth/rbac/rbac-middleware.ts`:

```typescript
import { Request, Response, NextFunction } from 'express';
import { Permission } from './types';
import { PermissionService } from './permission-service';

export function requirePermission(permission: Permission) {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Implementation
  };
}

export function requireAnyPermission(permissions: Permission[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Implementation
  };
}

export function requireAllPermissions(permissions: Permission[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Implementation
  };
}

export function requireRole(role: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Implementation
  };
}
```

### Step 6: Update User Model

Modify `src/auth/models/user.ts`:
- Add `roles` field to user model
- Add methods for role management

### Step 7: Create Database Migration

Create `src/database/migrations/004_add_roles.ts`:
- Create `user_roles` table
- Add indexes for performance
- Add default roles data

### Step 8: Add Role Management Endpoints

Modify `src/auth/routes.ts`:
- POST `/auth/users/:id/roles` - Assign role
- DELETE `/auth/users/:id/roles/:role` - Remove role
- GET `/auth/users/:id/roles` - Get user roles
- GET `/auth/roles` - List all roles
- GET `/auth/permissions` - List all permissions

## Verification Steps

1. Run all RBAC tests: `npm run test -- rbac`
2. Verify all tests pass
3. Test role assignment via API
4. Test permission checks via middleware
5. Test access denied scenarios (should return 403)
6. Verify role hierarchy works correctly
7. Run security review on RBAC implementation
8. Check for proper error handling

## Acceptance Criteria

- [ ] All RBAC types defined with proper TypeScript types
- [ ] Role-permission mappings are complete and accurate
- [ ] Role service implements all CRUD operations
- [ ] Permission service implements check functions
- [ ] Middleware integrates with authentication
- [ ] Database migration creates required tables
- [ ] API endpoints for role management are functional
- [ ] All tests pass (from Task 048)
- [ ] Code review completed
- [ ] Documentation updated

## Git Commit Message

```
feat(auth): implement role-based access control (RBAC)

- Add RBAC types and enums (Role, Permission)
- Define role-permission mappings for admin, manager, bidder, viewer
- Implement RoleService for user role management
- Implement PermissionService for permission checking
- Add RBAC middleware (requirePermission, requireRole)
- Create database migration for user_roles table
- Add role management API endpoints
- Integrate RBAC with authentication system
- Support role hierarchy and permission inheritance

Implements: Task 049
Closes: #<issue_number>
```
