# Task 033: Filter Search Implementation (Multi-condition Filtering)

## Task Header
| Field | Value |
|-------|-------|
| ID | 033 |
| Name | 筛选搜索实现 |
| Type | impl |
| Depends-on | 032 |

## Description

Implement multi-condition filtering for bidding search supporting region, industry, budget range, and date range filters. Build a flexible query builder that combines filters with AND logic and supports multiple values per filter with OR logic.

## Files to Create/Modify

### New Files
- `src/modules/search/services/filter-search.service.ts` - Filter search business logic
- `src/modules/search/dto/filter-query.dto.ts` - Filter request DTO with validation
- `src/modules/search/interfaces/filter-options.interface.ts` - Filter options type definitions
- `src/modules/search/enums/region.enum.ts` - Region constants
- `src/modules/search/enums/industry.enum.ts` - Industry constants

### Modify Files
- `src/modules/search/search.controller.ts` - Add POST /filter endpoint
- `src/modules/search/search.module.ts` - Register FilterSearchService

## Implementation Steps

1. **Enum Definitions**
   - Create Region enum with provinces and major cities
   - Create Industry enum with standard industry classifications
   - Use string enums for readable API values

2. **FilterQueryDto**
   - `@IsOptional()` `@IsEnum(Region, { each: true })` regions: Region[]
   - `@IsOptional()` `@IsEnum(Industry, { each: true })` industries: Industry[]
   - `@IsOptional()` `@IsNumber()` `@Min(0)` budgetMin: number
   - `@IsOptional()` `@IsNumber()` `@Min(0)` budgetMax: number
   - `@IsOptional()` `@IsDateString()` publishDateFrom: string
   - `@IsOptional()` `@IsDateString()` publishDateTo: string
   - Include pagination: page, limit with defaults and max limits
   - Add `@ValidateIf()` to ensure budgetMin <= budgetMax

3. **FilterOptions Interface**
   - Define TypeScript interfaces for type safety
   - Support single values and arrays for each filter
   - Include pagination metadata interface

4. **FilterSearchService**
   - Create `buildWhereClause(filters: FilterQueryDto)` private method
   - Implement dynamic query building with TypeORM QueryBuilder
   - Handle array filters with `WHERE IN` clauses
   - Handle range filters with `BETWEEN` or `>=` / `<=`
   - Add `searchWithFilters()` method returning paginated results
   - Support combining text search + filters (reuse Task 031)

5. **Query Builder Logic**
   ```typescript
   const qb = this.biddingRepo.createQueryBuilder('b');
   if (regions?.length) qb.andWhere('b.region IN (:...regions)', { regions });
   if (industries?.length) qb.andWhere('b.industry IN (:...industries)', { industries });
   if (budgetMin !== undefined) qb.andWhere('b.budget >= :budgetMin', { budgetMin });
   if (budgetMax !== undefined) qb.andWhere('b.budget <= :budgetMax', { budgetMax });
   if (publishDateFrom) qb.andWhere('b.publishDate >= :publishDateFrom', { publishDateFrom });
   ```

6. **Controller Endpoint**
   - `@Post('filter')` with `@Body() filters: FilterQueryDto`
   - Return standardized response with items, total, page info
   - Add Swagger documentation with @ApiBody, @ApiResponse

7. **Validation & Error Handling**
   - Global ValidationPipe with whitelist: true
   - Custom validation for date range consistency
   - Transform empty arrays to undefined to avoid SQL errors

## Verification Steps

1. Test each filter individually via API
2. Test combination filters: region + industry + budget
3. Verify SQL injection prevention with malicious input
4. Test pagination with various page sizes
5. Verify performance with Explain Analyze on complex queries
6. Check filter validation errors return 400 with clear messages

## Git Commit Message

```
feat(search): implement multi-condition filter search

- Add FilterSearchService with dynamic query builder
- Create Region and Industry enums for standardized values
- Implement FilterQueryDto with comprehensive validation
- Support AND logic between filter types, OR within arrays
- Add budget range and date range filtering
- Create POST /api/search/filter endpoint
- Include Swagger documentation for filter API

Refs: #033
```
