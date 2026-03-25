-- Task 067: 慢查询分析脚本
-- 用于识别和分析性能瓶颈

-- =====================================================
-- 1. 查找长时间运行的查询
-- =====================================================

-- 查看当前正在运行的查询（需要 pg_stat_activity 权限）
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    backend_start,
    query_start,
    state,
    EXTRACT(EPOCH FROM (NOW() - query_start))::INTEGER AS query_duration_seconds,
    LEFT(query, 200) AS query_preview
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '1 minute'
ORDER BY query_start;

-- =====================================================
-- 2. 查找最慢的查询（需要 pg_stat_statements 扩展）
-- =====================================================

-- 检查 pg_stat_statements 是否可用
SELECT * FROM pg_extension WHERE extname = 'pg_stat_statements';

-- 平均执行时间最长的查询（如果扩展已启用）
-- SELECT
--     query,
--     calls,
--     round(total_exec_time::numeric, 2) AS total_time_ms,
--     round(mean_exec_time::numeric, 2) AS avg_time_ms,
--     rows
-- FROM pg_stat_statements
-- WHERE query LIKE '%tender_notices%'
-- ORDER BY mean_exec_time DESC
-- LIMIT 20;

-- =====================================================
-- 3. 索引使用情况分析
-- =====================================================

-- 查看 tender_notices 表的索引使用统计
SELECT
    schemaname,
    tablename,
    indexrelname AS index_name,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE tablename = 'tender_notices'
ORDER BY idx_scan DESC;

-- 查找从未被使用的索引
SELECT
    schemaname,
    tablename,
    indexrelname,
    pg_size_pretty(pg_relation_size(index_relid)) AS index_size
FROM pg_stat_user_indexes
WHERE tablename = 'tender_notices'
  AND idx_scan = 0;

-- =====================================================
-- 4. 表扫描分析
-- =====================================================

-- 查看表的顺序扫描 vs 索引扫描比例
SELECT
    schemaname,
    relname AS table_name,
    seq_scan AS sequential_scans,
    seq_tup_read AS seq_tuples_read,
    idx_scan AS index_scans,
    idx_tup_fetch AS idx_tuples_fetched,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes
FROM pg_stat_user_tables
WHERE relname = 'tender_notices';

-- 如果 seq_scan 远高于 idx_scan，可能需要添加更多索引

-- =====================================================
-- 5. 查询执行计划分析模板
-- =====================================================

-- 分析招标公告按发布日期查询
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT *
FROM tender_notices
WHERE publish_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY publish_date DESC
LIMIT 50;

-- 分析招标人查询
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT *
FROM tender_notices
WHERE tenderer LIKE '%某招标人%'
ORDER BY publish_date DESC
LIMIT 20;

-- 分析地区行业组合查询
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT *
FROM tender_notices
WHERE region_code = 'BJ'
  AND industry_code = 'IT01'
  AND status = 'active'
ORDER BY publish_date DESC
LIMIT 50;

-- 分析状态筛选查询
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT COUNT(*)
FROM tender_notices
WHERE status = 'active'
  AND notice_type = 'bidding';

-- 分析金额范围查询
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT *
FROM tender_notices
WHERE budget_amount BETWEEN 100000 AND 500000
ORDER BY budget_amount DESC
LIMIT 50;

-- =====================================================
-- 6. 锁等待分析
-- =====================================================

-- 查看锁等待情况
SELECT
    pl.pid,
    pl.mode,
    pl.locktype,
    pl.relation::regclass,
    pl.page,
    pl.tuple,
    pl.granted,
    psa.query
FROM pg_locks pl
JOIN pg_stat_activity psa ON pl.pid = psa.pid
WHERE pl.relation = 'tender_notices'::regclass
  AND NOT pl.granted;

-- =====================================================
-- 7. 连接和事务分析
-- =====================================================

-- 查看当前连接数
SELECT
    datname AS database,
    usename AS username,
    application_name,
    client_addr,
    state,
    COUNT(*)
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY datname, usename, application_name, client_addr, state;

-- 查看长时间运行的事务
SELECT
    pid,
    usename,
    application_name,
    xact_start,
    NOW() - xact_start AS transaction_duration,
    state,
    LEFT(query, 100) AS query_preview
FROM pg_stat_activity
WHERE xact_start < NOW() - INTERVAL '5 minutes'
  AND state != 'idle'
ORDER BY xact_start;

-- =====================================================
-- 8. 表和索引大小分析
-- =====================================================

-- 查看表和索引大小
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_size_pretty(pg_indexes_size(relid)) AS indexes_size
FROM pg_stat_user_tables
WHERE relname = 'tender_notices';

-- 查看索引膨胀情况
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS scans
FROM pg_stat_user_indexes
WHERE tablename = 'tender_notices'
ORDER BY pg_relation_size(indexrelid) DESC;
