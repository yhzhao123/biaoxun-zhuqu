-- PostgreSQL 初始化脚本
-- 在容器启动时自动执行

-- 启用 pg_stat_statements 扩展（用于慢查询分析）
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 启用 uuid-ossp 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建应用数据库用户（生产环境建议使用非 superuser）
-- DO $$
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
--         CREATE ROLE app_user WITH LOGIN PASSWORD 'your_secure_password';
--     END IF;
-- END
-- $$;

-- 设置默认字符集和时区
ALTER DATABASE biaoxun SET timezone TO 'Asia/Shanghai';
ALTER DATABASE biaoxun SET client_encoding TO 'UTF8';

-- 设置语句超时（防止长时间运行的查询）
ALTER DATABASE biaoxun SET statement_timeout = '60s';
ALTER DATABASE biaoxun SET idle_in_transaction_session_timeout = '300s';

-- 创建应用 schema
CREATE SCHEMA IF NOT EXISTS app;

-- 注释
COMMENT ON DATABASE biaoxun IS '招标信息爬取与分析系统数据库';
