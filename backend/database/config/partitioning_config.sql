-- Task 067: PostgreSQL 表分区配置
-- 注意: Django ORM 不直接支持分区表，需要使用原生 SQL 管理

-- =====================================================
-- 1. 按发布时间范围分区（ RANGE 分区）
-- =====================================================

-- 创建分区表（仅作为参考，实际使用需要数据迁移）
/*
CREATE TABLE tender_notices_partitioned (
    id BIGINT PRIMARY KEY,
    notice_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    tenderer VARCHAR(200) NOT NULL,
    winner VARCHAR(200),
    project_name VARCHAR(300),
    notice_type VARCHAR(20) NOT NULL,
    budget DECIMAL(15, 2),
    budget_amount DECIMAL(15, 2),
    currency VARCHAR(3) DEFAULT 'CNY',
    publish_date TIMESTAMP NOT NULL,
    deadline_date TIMESTAMP,
    region VARCHAR(100),
    region_code VARCHAR(10),
    region_name VARCHAR(100),
    industry VARCHAR(100),
    industry_code VARCHAR(10),
    industry_name VARCHAR(100),
    source_url VARCHAR(500),
    source_site VARCHAR(100),
    status VARCHAR(20) NOT NULL,
    ai_summary TEXT,
    ai_keywords VARCHAR(500),
    ai_category VARCHAR(100),
    relevance_score FLOAT,
    crawl_batch_id VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by_id BIGINT REFERENCES users_user(id),
    is_public BOOLEAN DEFAULT TRUE,
    tenant_id VARCHAR(100)
) PARTITION BY RANGE (publish_date);
*/

-- =====================================================
-- 2. 分区维护脚本
-- =====================================================

-- 创建自动创建新分区的函数
CREATE OR REPLACE FUNCTION create_monthly_partition(
    p_year INT,
    p_month INT
) RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_name := 'tender_notices_' || p_year || LPAD(p_month::TEXT, 2, '0');
    start_date := MAKE_DATE(p_year, p_month, 1);
    end_date := start_date + INTERVAL '1 month';

    -- 检查分区是否已存在
    IF EXISTS (
        SELECT 1 FROM pg_tables
        WHERE tablename = partition_name
    ) THEN
        RETURN 'Partition ' || partition_name || ' already exists';
    END IF;

    -- 创建分区
    EXECUTE format(
        'CREATE TABLE %I PARTITION OF tender_notices_partitioned
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    -- 为新分区创建索引
    EXECUTE format(
        'CREATE INDEX %I ON %I (notice_id)',
        partition_name || '_notice_id_idx', partition_name
    );

    EXECUTE format(
        'CREATE INDEX %I ON %I (publish_date DESC)',
        partition_name || '_publish_date_idx', partition_name
    );

    EXECUTE format(
        'CREATE INDEX %I ON %I (tenderer, status)',
        partition_name || '_tenderer_status_idx', partition_name
    );

    RETURN 'Created partition: ' || partition_name;
END;
$$;

-- 创建未来分区的函数
CREATE OR REPLACE FUNCTION create_future_partitions(
    months_ahead INT DEFAULT 3
) RETURNS TABLE(partition_name TEXT, result TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    current_date_val DATE := CURRENT_DATE;
    target_date DATE;
    i INT;
    year_val INT;
    month_val INT;
BEGIN
    FOR i IN 0..months_ahead LOOP
        target_date := current_date_val + (i || ' months')::INTERVAL;
        year_val := EXTRACT(YEAR FROM target_date)::INT;
        month_val := EXTRACT(MONTH FROM target_date)::INT;

        partition_name := 'tender_notices_' || year_val || LPAD(month_val::TEXT, 2, '0');
        result := create_monthly_partition(year_val, month_val);

        RETURN NEXT;
    END LOOP;
END;
$$;

-- 创建删除旧分区的函数（归档后使用）
CREATE OR REPLACE FUNCTION archive_old_partition(
    p_year INT,
    p_month INT
) RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    partition_name TEXT;
    archive_table_name TEXT;
BEGIN
    partition_name := 'tender_notices_' || p_year || LPAD(p_month::TEXT, 2, '0');
    archive_table_name := 'archived_tender_notices_' || p_year || LPAD(p_month::TEXT, 2, '0');

    -- 检查分区是否存在
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables
        WHERE tablename = partition_name
    ) THEN
        RETURN 'Partition ' || partition_name || ' does not exist';
    END IF;

    -- 将分区从分区表中分离
    EXECUTE format(
        'ALTER TABLE tender_notices_partitioned DETACH PARTITION %I',
        partition_name
    );

    -- 重命名为归档表
    EXECUTE format(
        'ALTER TABLE %I RENAME TO %I',
        partition_name, archive_table_name
    );

    RETURN 'Archived partition: ' || partition_name || ' to ' || archive_table_name;
END;
$$;

-- =====================================================
-- 3. 分区查询优化
-- =====================================================

-- 分区裁剪验证查询
EXPLAIN (ANALYZE, VERBOSE)
SELECT *
FROM tender_notices_partitioned
WHERE publish_date >= '2026-03-01'
  AND publish_date < '2026-04-01';

-- 应该只扫描 tender_notices_202603 分区

-- =====================================================
-- 4. 分区监控
-- =====================================================

-- 查看所有分区
SELECT
    parent.relname AS parent_table,
    child.relname AS partition_name,
    pg_get_expr(child.relpartbound, child.oid) AS partition_constraint,
    pg_size_pretty(pg_relation_size(child.oid)) AS partition_size
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
WHERE parent.relname = 'tender_notices_partitioned'
ORDER BY child.relname;

-- 查看分区表统计
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS table_size
FROM pg_tables
WHERE tablename LIKE 'tender_notices_2%'
ORDER BY tablename;

-- =====================================================
-- 5. 分区管理调度（配合 cron/pg_cron 使用）
-- =====================================================

-- 手动执行：创建未来3个月的分区
-- SELECT * FROM create_future_partitions(3);

-- 手动执行：归档6个月前的分区
-- SELECT archive_old_partition(2025, 9);

-- =====================================================
-- 6. 备选方案：列表分区（按状态分区）
-- =====================================================

/*
-- 按状态分区（适合数据分布不均匀的场景）
CREATE TABLE tender_notices_by_status (
    -- 相同列定义
) PARTITION BY LIST (status);

-- 创建状态分区
CREATE TABLE tender_notices_active PARTITION OF tender_notices_by_status
    FOR VALUES IN ('active');

CREATE TABLE tender_notices_closed PARTITION OF tender_notices_by_status
    FOR VALUES IN ('closed');

CREATE TABLE tender_notices_other PARTITION OF tender_notices_by_status
    FOR VALUES IN ('pending', 'expired');
*/

-- =====================================================
-- 7. 分区表维护命令
-- =====================================================

-- 分析所有分区
-- ANALYZE tender_notices_partitioned;

-- 重新索引所有分区
-- REINDEX TABLE CONCURRENTLY tender_notices_partitioned;

-- 检查分区约束
-- SELECT * FROM pg_partitioned_table WHERE partrelid = 'tender_notices_partitioned'::regclass;
