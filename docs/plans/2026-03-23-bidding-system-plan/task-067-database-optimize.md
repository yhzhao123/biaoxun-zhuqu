# Task 067: Database Optimization (数据库优化)

## Task Header

| Field | Value |
|-------|-------|
| Task ID | 067 |
| Name | Database Optimization |
| Type | config |
| Dependencies | None (can run in parallel with other optimization tasks) |
| Created | 2026-03-23 |
| Estimated Effort | 8-12 hours |

## Description

Optimize the database layer for the bidding system to handle high-concurrency auction scenarios. This includes creating proper indexes, implementing table partitioning for large datasets, and tuning slow queries. The bidding system requires fast read/write operations for real-time price updates and concurrent bid submissions.

## Files to Create/Modify

### Create
- `database/migrations/067_add_bidding_indexes.sql`
- `database/scripts/analyze_slow_queries.sql`
- `database/config/partitioning_config.sql`
- `docs/database/optimization_report.md`

### Modify
- `src/models/Bid.ts` - Add query hints if needed
- `src/models/Auction.ts` - Optimize query patterns
- `config/database.ts` - Adjust connection pool and timeout settings
- `docker-compose.yml` - Update MySQL/PostgreSQL configuration for performance

## Implementation Steps

### Step 1: Analyze Current Query Performance
- [ ] Run slow query log analysis
- [ ] Identify queries with execution time > 100ms
- [ ] Document query patterns for bidding operations
- [ ] Check current index usage with EXPLAIN ANALYZE

### Step 2: Create Indexes for Bidding System

```sql
-- Indexes for bid table
CREATE INDEX idx_bids_auction_id_created_at ON bids(auction_id, created_at DESC);
CREATE INDEX idx_bids_user_id_created_at ON bids(user_id, created_at DESC);
CREATE INDEX idx_bids_amount_auction_id ON bids(auction_id, amount DESC);

-- Composite index for auction queries
CREATE INDEX idx_auctions_status_end_time ON auctions(status, end_time) WHERE status IN ('active', 'pending');
CREATE INDEX idx_auctions_category_status ON auctions(category_id, status);

-- Partial index for active bids
CREATE INDEX idx_active_bids ON bids(auction_id, amount DESC) WHERE auction_id IN (SELECT id FROM auctions WHERE status = 'active');
```

### Step 3: Implement Table Partitioning
- [ ] Partition `bids` table by range (created_at) - monthly partitions
- [ ] Partition `auctions` table by status for faster lookups
- [ ] Create partition maintenance scripts
- [ ] Document partition pruning strategies

```sql
-- Example partition setup for bids table
CREATE TABLE bids_partitioned (
    id BIGINT PRIMARY KEY,
    auction_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL
) PARTITION BY RANGE (EXTRACT(YEAR_MONTH FROM created_at));

-- Create monthly partitions
CREATE TABLE bids_202603 PARTITION OF bids_partitioned
    FOR VALUES FROM (202603) TO (202604);
```

### Step 4: Query Tuning
- [ ] Rewrite N+1 queries for bid retrieval
- [ ] Optimize auction listing queries with proper JOIN order
- [ ] Add query hints for complex bidding aggregations
- [ ] Implement materialized views for bid statistics if needed

### Step 5: Connection Pool Configuration

```typescript
// config/database.ts
export const databaseConfig = {
  pool: {
    min: 10,
    max: 50,
    acquireTimeoutMillis: 30000,
    idleTimeoutMillis: 10000,
  },
  queryTimeout: 30000,
  statementTimeout: 60000,
};
```

### Step 6: Database Configuration Tuning

Update database server configuration:
- Increase `innodb_buffer_pool_size` to 70% of available memory
- Tune `max_connections` based on application server count
- Enable `slow_query_log` for ongoing monitoring
- Configure `query_cache_size` if using MySQL

## Verification Steps

### Performance Benchmarks
- [ ] Run load test with 1000 concurrent bid operations
- [ ] Verify bid insertion latency < 50ms (p95)
- [ ] Verify auction query latency < 30ms (p95)
- [ ] Confirm no deadlocks during concurrent bidding

### Index Verification
```sql
-- Verify indexes are being used
EXPLAIN ANALYZE
SELECT * FROM bids
WHERE auction_id = 12345
ORDER BY created_at DESC
LIMIT 50;

-- Check index usage statistics
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE tablename IN ('bids', 'auctions')
ORDER BY idx_scan DESC;
```

### Partition Verification
- [ ] Confirm partition pruning is working (check query plans)
- [ ] Verify partition auto-creation script functions
- [ ] Test query performance on partitioned tables

### Monitoring Setup
- [ ] Configure slow query alerting (> 500ms)
- [ ] Set up connection pool monitoring
- [ ] Document DBA runbook for partition maintenance

## Rollback Plan

1. Keep old indexes until new ones are verified
2. Create database backup before migration
3. Script to drop new indexes if issues arise
4. Document rollback commands in runbook

## Git Commit Message

```
config(db): optimize bidding system database performance

- Add composite indexes for auction_id + created_at queries
- Implement monthly partitioning for bids table
- Create status-based indexes for active auction lookups
- Tune connection pool settings (min: 10, max: 50)
- Configure query timeout and statement timeout
- Add partition maintenance scripts
- Document optimization strategies and monitoring

Task: 067
```

## Notes

- Coordinate with Task 068 (Cache Strategy) to avoid redundant caching of indexed data
- Test partitioning on staging with production-like data volume
- Consider read replicas for bid history queries if volume exceeds 10M records
