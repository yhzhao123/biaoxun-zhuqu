# Task 031: 全文搜索实现 (Full-text Search Implementation)

## Task Header
| Field | Value |
|-------|-------|
| ID | 031 |
| Name | 全文搜索实现 |
| Type | impl |
| Depends-on | 030 |

## Description

Implement full-text search functionality for the bidding system using PostgreSQL's tsvector and trigram search capabilities. This enables efficient keyword searching across bidding titles, descriptions, and content with relevance ranking.

## Files to Create/Modify

### New Files
- `src/modules/search/services/fulltext-search.service.ts` - Full-text search service with PostgreSQL tsvector
- `src/modules/search/repositories/search.repository.ts` - Search repository layer
- `src/modules/search/dto/search-query.dto.ts` - Search request DTO
- `src/modules/search/dto/search-result.dto.ts` - Search response DTO
- `src/database/migrations/[timestamp]_add_fulltext_search_indexes.ts` - Migration for tsvector columns and GIN indexes

### Modify Files
- `src/modules/search/search.module.ts` - Register new services and exports
- `src/modules/bidding/entities/bidding.entity.ts` - Add tsvector columns for search

## Implementation Steps

1. **Database Migration**
   - Add `title_tsv` and `content_tsv` generated columns using `to_tsvector('chinese', column_name)`
   - Create GIN indexes on tsvector columns for fast querying
   - Add pg_trgm extension for trigram similarity search
   - Create combined GIN index for multi-column search

2. **Entity Updates**
   - Add `@Index()` decorators for GIN indexes in BiddingEntity
   - Add tsvector column definitions with `@Column()` decorators

3. **Search Repository**
   - Implement `searchByKeywords(query: string, options: SearchOptions)` method
   - Use `ts_rank_cd()` for relevance scoring
   - Support `plainto_tsquery()` for natural language queries
   - Implement `websearch_to_tsquery()` for advanced query syntax
   - Add pagination support with LIMIT/OFFSET

4. **Full-text Search Service**
   - Create `search()` method accepting SearchQueryDto
   - Implement query parsing and validation
   - Handle Chinese text segmentation (if needed, use zhparser or simple mode)
   - Return results sorted by relevance score
   - Support highlighting with `ts_headline()`

5. **DTOs**
   - SearchQueryDto: keywords, page, limit, sortBy, sortOrder
   - SearchResultDto: items[], totalCount, page, totalPages, query

## Verification Steps

1. Run migration: `npm run migration:run`
2. Verify indexes exist: Check PostgreSQL with `\d bidding_table`
3. Test search endpoint: `GET /api/search?q=采购项目`
4. Verify relevance ranking: Results should be ordered by ts_rank_cd score
5. Test pagination: Confirm correct total count and page navigation
6. Test edge cases: Empty query, special characters, long keywords
7. Performance test: Query should complete < 100ms for 10k records

## Git Commit Message

```
feat(search): implement full-text search with PostgreSQL tsvector

- Add title_tsv and content_tsv generated columns
- Create GIN indexes for fast full-text querying
- Implement FulltextSearchService with ts_rank_cd ranking
- Add trigram similarity search for fuzzy matching
- Create SearchRepository with pagination support
- Include ts_headline for result highlighting preparation

Refs: #031
```
