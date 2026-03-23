# Task 051: Data Isolation Implementation

## Task Header

| Field | Value |
|-------|-------|
| ID | 051 |
| Name | Data Isolation Implementation |
| Type | impl |
| Dependencies | 050 (Data Isolation Tests) |
| Status | pending |

## Description

Implement data isolation features for the bidding system including regional data isolation and multi-tenant support. Ensure users can only access data within their authorized region and tenant scope, with proper enforcement at the database and API layers.

## Files to Create/Modify

### New Files
1. `src/isolation/types.ts` - TypeScript types for data isolation
2. `src/isolation/regional/regional-context.ts` - Regional context management
3. `src/isolation/regional/regional-service.ts` - Regional data service
4. `src/isolation/tenant/tenant-context.ts` - Tenant context management
5. `src/isolation/tenant/tenant-service.ts` - Tenant data service
6. `src/isolation/middleware/scope-middleware.ts` - Scope enforcement middleware
7. `src/isolation/filters/query-filter.ts` - Database query filters
8. `src/isolation/index.ts` - Module exports

### Modified Files
9. `src/database/models/project.ts` - Add region/tenant columns
10. `src/database/models/bid.ts` - Add region/tenant columns
11. `src/database/models/user.ts` - Add region/tenant assignments
12. `src/database/migrations/005_add_isolation.ts` - Database migration
13. `src/auth/middleware/auth.ts` - Integrate isolation context
14. `src/api/routes/*.ts` - Apply isolation to routes

## Implementation Steps

### Step 1: Define Isolation Types

Create `src/isolation/types.ts`:

```typescript
export interface Region {
  id: string;
  name: string;
  code: string;
  countries: string[];
  timezone: string;
}

export interface Tenant {
  id: string;
  name: string;
  domain: string;
  settings: TenantSettings;
  createdAt: Date;
  status: 'active' | 'suspended' | 'deleted';
}

export interface TenantSettings {
  maxUsers: number;
  maxProjects: number;
  features: string[];
  branding?: TenantBranding;
}

export interface TenantBranding {
  logo?: string;
  primaryColor?: string;
  favicon?: string;
}

export interface DataScope {
  regionId?: string;
  tenantId?: string;
  userId?: string;
}

export interface IsolationContext {
  region?: Region;
  tenant?: Tenant;
  userScope: DataScope;
  isSuperAdmin: boolean;
}

export interface IsolatedQueryOptions {
  scope?: DataScope;
  bypassIsolation?: boolean;
  includeDeleted?: boolean;
}
```

### Step 2: Implement Regional Context Management

Create `src/isolation/regional/regional-context.ts`:

```typescript
import { Region, DataScope } from '../types';
import { AsyncLocalStorage } from 'async_hooks';

const regionalContext = new AsyncLocalStorage<DataScope>();

export class RegionalContext {
  static runWithScope<T>(scope: DataScope, callback: () => T): T {
    return regionalContext.run(scope, callback);
  }

  static getCurrentScope(): DataScope | undefined {
    return regionalContext.getStore();
  }

  static setRegion(regionId: string): void {
    const current = this.getCurrentScope() || {};
    regionalContext.enterWith({ ...current, regionId });
  }

  static clear(): void {
    regionalContext.disable();
  }
}

export function getRegionalScope(): DataScope | undefined {
  return RegionalContext.getCurrentScope();
}
```

### Step 3: Implement Regional Service

Create `src/isolation/regional/regional-service.ts`:

```typescript
import { Region, DataScope } from '../types';
import { Database } from '../../database';
import { RegionalContext } from './regional-context';

export class RegionalService {
  private db: Database;

  constructor(database: Database) {
    this.db = database;
  }

  async getRegionById(regionId: string): Promise<Region | null> {
    // Implementation
  }

  async getUserRegions(userId: string): Promise<Region[]> {
    // Implementation
  }

  async assignUserToRegion(userId: string, regionId: string): Promise<void> {
    // Implementation
  }

  async removeUserFromRegion(userId: string, regionId: string): Promise<void> {
    // Implementation
  }

  async validateRegionalAccess(userId: string, regionId: string): Promise<boolean> {
    // Implementation
  }

  async getAllRegions(): Promise<Region[]> {
    // Implementation
  }

  withRegionalScope<T>(regionId: string, callback: () => Promise<T>): Promise<T> {
    return RegionalContext.runWithScope({ regionId }, callback);
  }
}
```

### Step 4: Implement Tenant Context Management

Create `src/isolation/tenant/tenant-context.ts`:

```typescript
import { Tenant, DataScope } from '../types';
import { AsyncLocalStorage } from 'async_hooks';

const tenantContext = new AsyncLocalStorage<DataScope>();

export class TenantContext {
  static runWithScope<T>(scope: DataScope, callback: () => T): T {
    return tenantContext.run(scope, callback);
  }

  static getCurrentScope(): DataScope | undefined {
    return tenantContext.getStore();
  }

  static setTenant(tenantId: string): void {
    const current = this.getCurrentScope() || {};
    tenantContext.enterWith({ ...current, tenantId });
  }

  static clear(): void {
    tenantContext.disable();
  }
}

export function getTenantScope(): DataScope | undefined {
  return TenantContext.getCurrentScope();
}
```

### Step 5: Implement Tenant Service

Create `src/isolation/tenant/tenant-service.ts`:

```typescript
import { Tenant, TenantSettings, DataScope } from '../types';
import { Database } from '../../database';
import { TenantContext } from './tenant-context';

export class TenantService {
  private db: Database;

  constructor(database: Database) {
    this.db = database;
  }

  async createTenant(name: string, domain: string, settings?: TenantSettings): Promise<Tenant> {
    // Implementation
  }

  async getTenantById(tenantId: string): Promise<Tenant | null> {
    // Implementation
  }

  async getTenantByDomain(domain: string): Promise<Tenant | null> {
    // Implementation
  }

  async updateTenant(tenantId: string, updates: Partial<Tenant>): Promise<Tenant> {
    // Implementation
  }

  async deleteTenant(tenantId: string): Promise<void> {
    // Implementation
  }

  async getTenantUsers(tenantId: string): Promise<string[]> {
    // Implementation
  }

  async assignUserToTenant(userId: string, tenantId: string, isAdmin?: boolean): Promise<void> {
    // Implementation
  }

  async removeUserFromTenant(userId: string, tenantId: string): Promise<void> {
    // Implementation
  }

  async validateTenantAccess(userId: string, tenantId: string): Promise<boolean> {
    // Implementation
  }

  async isTenantAdmin(userId: string, tenantId: string): Promise<boolean> {
    // Implementation
  }

  withTenantScope<T>(tenantId: string, callback: () => Promise<T>): Promise<T> {
    return TenantContext.runWithScope({ tenantId }, callback);
  }
}
```

### Step 6: Implement Query Filters

Create `src/isolation/filters/query-filter.ts`:

```typescript
import { DataScope, IsolatedQueryOptions } from '../types';
import { Knex } from 'knex';

export class IsolationQueryFilter {
  static apply<T extends Knex.QueryBuilder>(
    queryBuilder: T,
    scope: DataScope,
    options: IsolatedQueryOptions = {}
  ): T {
    if (options.bypassIsolation) {
      return queryBuilder;
    }

    let filteredQuery = queryBuilder;

    // Apply region filter
    if (scope.regionId) {
      filteredQuery = filteredQuery.where('region_id', scope.regionId);
    }

    // Apply tenant filter
    if (scope.tenantId) {
      filteredQuery = filteredQuery.where('tenant_id', scope.tenantId);
    }

    // Apply user filter for ownership-based resources
    if (scope.userId && !options.bypassIsolation) {
      filteredQuery = filteredQuery.where(function() {
        this.where('created_by', scope.userId)
            .orWhere('assigned_to', scope.userId);
      });
    }

    return filteredQuery;
  }

  static applyToAggregation<T extends Knex.QueryBuilder>(
    queryBuilder: T,
    scope: DataScope
  ): T {
    // Ensure aggregation queries also respect isolation
    return this.apply(queryBuilder, scope);
  }
}

export function withIsolation<T extends Knex.QueryBuilder>(
  queryBuilder: T,
  scope: DataScope
): T {
  return IsolationQueryFilter.apply(queryBuilder, scope);
}
```

### Step 7: Implement Scope Middleware

Create `src/isolation/middleware/scope-middleware.ts`:

```typescript
import { Request, Response, NextFunction } from 'express';
import { RegionalService } from '../regional/regional-service';
import { TenantService } from '../tenant/tenant-service';
import { RegionalContext } from '../regional/regional-context';
import { TenantContext } from '../tenant/tenant-context';
import { IsolationContext } from '../types';

export function scopeMiddleware(
  regionalService: RegionalService,
  tenantService: TenantService
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const userId = req.user?.id;
      const isSuperAdmin = req.user?.roles?.includes('admin');

      if (!userId) {
        return res.status(401).json({ error: 'Unauthorized' });
      }

      // Extract region from request (header, query, or user default)
      const regionId = req.headers['x-region-id'] as string ||
                      req.query.region as string ||
                      req.user?.defaultRegion;

      // Extract tenant from request (header, subdomain, or user default)
      const tenantId = req.headers['x-tenant-id'] as string ||
                      extractTenantFromDomain(req) ||
                      req.user?.defaultTenant;

      // Validate user has access to requested region/tenant
      if (regionId && !isSuperAdmin) {
        const hasAccess = await regionalService.validateRegionalAccess(userId, regionId);
        if (!hasAccess) {
          return res.status(403).json({ error: 'Access denied for region' });
        }
      }

      if (tenantId && !isSuperAdmin) {
        const hasAccess = await tenantService.validateTenantAccess(userId, tenantId);
        if (!hasAccess) {
          return res.status(403).json({ error: 'Access denied for tenant' });
        }
      }

      // Set isolation context
      const isolationContext: IsolationContext = {
        userScope: {
          regionId,
          tenantId,
          userId
        },
        isSuperAdmin
      };

      // Run request within isolation context
      await RegionalContext.runWithScope(
        { regionId },
        async () => {
          await TenantContext.runWithScope(
            { tenantId },
            async () => {
              req.isolationContext = isolationContext;
              next();
            }
          );
        }
      );
    } catch (error) {
      next(error);
    }
  };
}

function extractTenantFromDomain(req: Request): string | undefined {
  const host = req.headers.host;
  if (!host) return undefined;

  const parts = host.split('.');
  if (parts.length > 2) {
    // subdomain.example.com -> extract subdomain as tenant hint
    return parts[0];
  }
  return undefined;
}
```

### Step 8: Update Database Models

Modify `src/database/models/project.ts`:
- Add `region_id` column
- Add `tenant_id` column
- Add indexes for performance

Modify `src/database/models/bid.ts`:
- Add `region_id` column
- Add `tenant_id` column

Modify `src/database/models/user.ts`:
- Add `default_region_id` column
- Add `default_tenant_id` column

### Step 9: Create Database Migration

Create `src/database/migrations/005_add_isolation.ts`:

```typescript
import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  // Create regions table
  await knex.schema.createTable('regions', (table) => {
    table.uuid('id').primary().defaultTo(knex.fn.uuid());
    table.string('name').notNullable();
    table.string('code').notNullable().unique();
    table.jsonb('countries').defaultTo('[]');
    table.string('timezone').defaultTo('UTC');
    table.timestamps(true, true);
  });

  // Create tenants table
  await knex.schema.createTable('tenants', (table) => {
    table.uuid('id').primary().defaultTo(knex.fn.uuid());
    table.string('name').notNullable();
    table.string('domain').notNullable().unique();
    table.jsonb('settings').defaultTo('{}');
    table.enum('status', ['active', 'suspended', 'deleted']).defaultTo('active');
    table.timestamps(true, true);
  });

  // Create user_regions junction table
  await knex.schema.createTable('user_regions', (table) => {
    table.uuid('user_id').references('id').inTable('users').onDelete('CASCADE');
    table.uuid('region_id').references('id').inTable('regions').onDelete('CASCADE');
    table.string('role').defaultTo('member');
    table.timestamps(true, true);
    table.primary(['user_id', 'region_id']);
  });

  // Create user_tenants junction table
  await knex.schema.createTable('user_tenants', (table) => {
    table.uuid('user_id').references('id').inTable('users').onDelete('CASCADE');
    table.uuid('tenant_id').references('id').inTable('tenants').onDelete('CASCADE');
    table.boolean('is_admin').defaultTo(false);
    table.timestamps(true, true);
    table.primary(['user_id', 'tenant_id']);
  });

  // Add region/tenant columns to projects
  await knex.schema.alterTable('projects', (table) => {
    table.uuid('region_id').references('id').inTable('regions');
    table.uuid('tenant_id').references('id').inTable('tenants');
    table.index('region_id');
    table.index('tenant_id');
  });

  // Add region/tenant columns to bids
  await knex.schema.alterTable('bids', (table) => {
    table.uuid('region_id').references('id').inTable('regions');
    table.uuid('tenant_id').references('id').inTable('tenants');
    table.index('region_id');
    table.index('tenant_id');
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.alterTable('bids', (table) => {
    table.dropColumn('region_id');
    table.dropColumn('tenant_id');
  });

  await knex.schema.alterTable('projects', (table) => {
    table.dropColumn('region_id');
    table.dropColumn('tenant_id');
  });

  await knex.schema.dropTableIfExists('user_tenants');
  await knex.schema.dropTableIfExists('user_regions');
  await knex.schema.dropTableIfExists('tenants');
  await knex.schema.dropTableIfExists('regions');
}
```

### Step 10: Apply Isolation to Routes

Modify `src/api/routes/projects.ts`:
- Apply scope middleware
- Use isolation filters in queries

Modify `src/api/routes/bids.ts`:
- Apply scope middleware
- Use isolation filters in queries

## Verification Steps

1. Run all data isolation tests: `npm run test -- isolation`
2. Verify all tests pass
3. Test regional data access restrictions via API
4. Test tenant data isolation via API
5. Verify super admin can access cross-region/tenant data
6. Test performance of isolated queries
7. Run security review on isolation implementation
8. Verify audit logs capture scope context

## Acceptance Criteria

- [ ] Regional isolation is enforced at database layer
- [ ] Tenant isolation is enforced at database layer
- [ ] Scope middleware validates access on each request
- [ ] Query filters automatically apply isolation scope
- [ ] Database migration creates all required tables/columns
- [ ] API endpoints enforce isolation rules
- [ ] Super admin can bypass isolation when needed
- [ ] Audit logs include isolation context
- [ ] All tests pass (from Task 050)
- [ ] Performance impact is acceptable
- [ ] Code review completed
- [ ] Documentation updated

## Security Considerations

- Verify no SQL injection in dynamic filters
- Test scope cannot be bypassed via API parameters
- Ensure tenant/subdomain validation is strict
- Validate region codes against whitelist
- Log all cross-scope access attempts
- Implement rate limiting per tenant

## Git Commit Message

```
feat(isolation): implement regional and tenant data isolation

- Add isolation types and context management
- Implement RegionalService for region-based access control
- Implement TenantService for multi-tenant data separation
- Create isolation query filters for database layer
- Add scope middleware for request-level isolation
- Create database migration for regions, tenants, and junction tables
- Add region_id and tenant_id to projects and bids tables
- Integrate isolation with existing API routes
- Support super admin bypass for cross-scope access
- Add audit logging for isolation context

Implements: Task 051
Closes: #<issue_number>
```
