# 项目代码评审报告

**评审日期**: 2026-03-26
**评审范围**: backend/apps/crawler/, backend/apps/llm/

---

## 总览

| 模块 | CRITICAL | HIGH | MEDIUM | LOW | 状态 |
|------|----------|------|--------|-----|------|
| crawler | 0 | 3 | 4 | 3 | ⚠️ WARNING |
| llm | 2 | 2 | 3 | 2 | 🛑 BLOCK |

---

## Crawler 模块问题

### HIGH (3个)

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| 1 | CrawlTaskViewSet 使用模拟数据，未连接数据库 | `views/crawl_task.py` | 实现真实数据库查询 |
| 2 | CrawlTask 缺少与 CrawlSource 的外键关联 | `models/crawl_task.py` | 添加 source 外键 |
| 3 | CrawlSource 未注册 Django Admin | `admin.py` | 注册 CrawlSource Admin |

### MEDIUM (4个)

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| 4 | scheduler.py 使用硬编码URL | `scheduler.py` | 使用 settings 或数据库配置 |
| 5 | trigger action 缺少输入验证 | `views/crawl_task.py` | 添加 Serializer 验证 |
| 6 | 模糊去重性能问题 | `services/duplicate.py` | 添加索引和缓存 |
| 7 | 任务重试逻辑异常处理不完整 | `tasks.py` | 重构异常处理 |

### LOW (3个)

| # | 问题 | 文件 |
|---|------|------|
| 8 | status/source_site 缺少数据库索引 | `models/crawl_task.py` |
| 9 | test_base.py 拼写错误 | `tests/test_base.py:81` |
| 10 | 状态转换缺少验证 | `views/crawl_source.py` |

---

## LLM 模块问题

### CRITICAL (2个) - 必须修复

| # | 问题 | 文件 | 修复方案 |
|---|------|------|----------|
| 1 | OpenAI SDK 超时参数类型错误 | `services.py:39` | 使用 `httpx.Timeout` 而非 `requests.Timeout` |
| 2 | Anthropic SDK 超时参数类型错误 | `services.py:49` | 使用 `httpx.Timeout` |

```python
# 修复示例
from httpx import Timeout

self._openai_client = openai.OpenAI(
    api_key=self.api_key,
    base_url=self.base_url or None,
    timeout=Timeout(getattr(self.config, 'timeout_seconds', 120))
)
```

### HIGH (2个)

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| 3 | DEBUG模式绕过认证存在安全风险 | `views.py:30-33` | 使用更严格的环境检测 |
| 4 | 聊天方法缺少错误处理 | `services.py` | 添加 try-except 和自定义异常 |

### MEDIUM (3个)

| # | 问题 | 文件 |
|---|------|------|
| 5 | 缺少API重试机制 | `services.py` |
| 6 | 匿名用户数据隔离不完整 | `views.py` |
| 7 | JSONField 直接修改 | `models.py:115` |

### LOW (2个)

| # | 问题 | 文件 |
|---|------|------|
| 8 | LLMConfig 缺少 timeout_seconds 字段 | `models.py` |
| 9 | health端点暴露服务URL | `views.py` |

---

## 代码亮点

### Crawler 模块
- ✅ 良好的模块划分（base, spiders, services）
- ✅ 完善的 Celery 任务设计（自动重试、状态管理）
- ✅ DynamicSpider 设计优秀，可配置性强
- ✅ 去重服务功能完整（精确+模糊）

### LLM 模块
- ✅ 官方SDK集成正确
- ✅ 测试覆盖率高（90%）
- ✅ 类型注解完整
- ✅ 多提供商支持设计良好

---

## 修复优先级

### 第一优先级（立即修复）
1. LLM: OpenAI/Anthropic SDK 超时参数类型错误 (CRITICAL)
2. Crawler: CrawlTaskViewSet 实现真实数据库查询 (HIGH)

### 第二优先级（本次迭代）
3. Crawler: CrawlTask 添加 source 外键
4. LLM: 添加 API 重试机制
5. Crawler: CrawlSource 注册 Admin

### 第三优先级（后续优化）
6. 性能优化（索引、缓存）
7. 安全加固
8. 测试补充

---

## 下一步行动

1. 修复 CRITICAL 问题
2. 创建修复分支
3. 逐项修复 HIGH 问题
4. 运行测试验证
5. 提交代码审查