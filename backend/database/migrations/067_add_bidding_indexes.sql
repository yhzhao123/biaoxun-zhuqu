-- Task 067: Database Optimization Migration
-- 创建时间: 2026-03-25
-- 描述: 招标系统数据库性能优化索引

-- =====================================================
-- 1. 基础索引优化
-- =====================================================

-- 确保基础字段索引存在
CREATE INDEX IF NOT EXISTS idx_tender_notices_notice_id ON tender_notices(notice_id);
CREATE INDEX IF NOT EXISTS idx_tender_notices_publish_date ON tender_notices(publish_date DESC);
CREATE INDEX IF NOT EXISTS idx_tender_notices_status ON tender_notices(status);
CREATE INDEX IF NOT EXISTS idx_tender_notices_budget_amount ON tender_notices(budget_amount);
CREATE INDEX IF NOT EXISTS idx_tender_notices_region_code ON tender_notices(region_code);
CREATE INDEX IF NOT EXISTS idx_tender_notices_industry_code ON tender_notices(industry_code);
CREATE INDEX IF NOT EXISTS idx_tender_notices_crawl_batch ON tender_notices(crawl_batch_id);

-- =====================================================
-- 2. 复合索引优化
-- =====================================================

-- 复合索引：标题 + 发布日期（用于列表查询和排序）
CREATE INDEX IF NOT EXISTS idx_tender_title_pub ON tender_notices(title, publish_date DESC);

-- 复合索引：招标人 + 状态（用于按招标人筛选）
CREATE INDEX IF NOT EXISTS idx_tender_tenderer_status ON tender_notices(tenderer, status);

-- 复合索引：地区 + 行业（用于分类筛选）
CREATE INDEX IF NOT EXISTS idx_tender_region_industry ON tender_notices(region, industry);

-- 复合索引：地区编码 + 行业编码（用于编码筛选）
CREATE INDEX IF NOT EXISTS idx_tender_region_codes ON tender_notices(region_code, industry_code);

-- 复合索引：爬虫批次 + 创建时间（用于批次查询）
CREATE INDEX IF NOT EXISTS idx_tender_crawl_batch ON tender_notices(crawl_batch_id, created_at DESC);

-- 复合索引：公告类型 + 发布日期（用于类型筛选）
CREATE INDEX IF NOT EXISTS idx_tender_notice_type_date ON tender_notices(notice_type, publish_date DESC);

-- 复合索引：状态 + 发布日期（用于状态筛选）
CREATE INDEX IF NOT EXISTS idx_tender_status_date ON tender_notices(status, publish_date DESC);

-- 复合索引：招标人 + 发布日期（用于招标人历史查询）
CREATE INDEX IF NOT EXISTS idx_tender_tenderer_date ON tender_notices(tenderer, publish_date DESC);

-- =====================================================
-- 3. 覆盖索引（Include Index）- PostgreSQL 11+
-- =====================================================

-- 覆盖索引：公告ID + 发布日期 + 状态（覆盖常见列表查询字段）
CREATE INDEX IF NOT EXISTS idx_tender_cover_list
ON tender_notices(notice_id, publish_date, status)
INCLUDE (title, tenderer, budget_amount, region, industry);

-- 覆盖索引：招标人查询（包含常用字段）
CREATE INDEX IF NOT EXISTS idx_tender_cover_tenderer
ON tender_notices(tenderer)
INCLUDE (title, publish_date, status, budget_amount, winner);

-- =====================================================
-- 4. 部分索引（Partial Index）
-- =====================================================

-- 部分索引：仅索引活跃状态的招标（提高活跃查询效率）
CREATE INDEX IF NOT EXISTS idx_tender_active_only
ON tender_notices(publish_date DESC, budget_amount)
WHERE status = 'active';

-- 部分索引：仅索引招标类型公告（排除中标公告）
CREATE INDEX IF NOT EXISTS idx_tender_bidding_only
ON tender_notices(publish_date DESC)
WHERE notice_type = 'bidding';

-- =====================================================
-- 5. 降序索引（Descending Index）- PostgreSQL 9.3+
-- =====================================================

-- 按金额排序的索引（用于金额排序查询）
CREATE INDEX IF NOT EXISTS idx_tender_budget_desc
ON tender_notices(budget_amount DESC NULLS LAST);

-- 按发布时间排序的索引（用于最新招标查询）
CREATE INDEX IF NOT EXISTS idx_tender_date_desc
ON tender_notices(publish_date DESC NULLS LAST);

-- =====================================================
-- 6. 索引验证
-- =====================================================

-- 验证索引创建成功
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'tender_notices'
ORDER BY indexname;

-- 查看索引大小统计
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes
JOIN pg_stat_user_indexes USING (indexrelname)
WHERE tablename = 'tender_notices'
ORDER BY pg_relation_size(indexrelid) DESC;
