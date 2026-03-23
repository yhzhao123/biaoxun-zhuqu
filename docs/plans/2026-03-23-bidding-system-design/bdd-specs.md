# BDD Specifications - 招标信息系统

> 行为驱动开发规范文档

## 概述

本文档使用 Gherkin 语法描述招标信息系统的行为场景，作为可执行的规格说明。

---

## Feature: 招标信息爬取

### Scenario: 成功爬取政府采购网信息
```gherkin
Given 爬虫任务"政府采购网-每日更新"已配置
And 目标URL为"http://www.ccgp.gov.cn/"
When 爬虫在每日凌晨2:00启动
Then 应在4小时内完成爬取
And 成功提取的招标信息数量应大于0
And 所有提取的数据应包含title、notice_id、tenderer字段
```

### Scenario: 处理重复招标信息
```gherkin
Given 数据库中已存在招标编号"ZB202403001"
When 爬虫再次抓取到相同编号的招标信息
Then 应更新现有记录而非创建新记录
And 应记录更新时间和来源
```

### Scenario: 爬取失败重试机制
```gherkin
Given 爬虫任务"政府采购网-每日更新"启动
When 目标网站返回503错误
Then 应在60秒后自动重试
And 最多重试3次
And 3次失败后应记录错误日志并标记任务为失败
```

### Scenario: 验证码拦截处理
```gherkin
Given 爬虫访问需要验证码的页面
When 检测到验证码挑战
Then 应调用验证码识别服务
And 识别成功率应大于80%
And 识别失败后应切换IP代理重试
```

---

## Feature: NLP实体提取

### Scenario: 提取招标人信息
```gherkin
Given 招标文本内容：
  """
  某市人民医院医疗设备采购项目招标公告
  招标人：某市人民医院
  招标代理机构：某招标代理有限公司
  """
When 系统执行NLP实体提取
Then 应识别出招标人为"某市人民医院"
And 置信度应大于0.85
```

### Scenario: 提取金额信息
```gherkin
Given 招标文本内容包含"项目预算：人民币壹佰万元整（¥1,000,000.00）"
When 系统执行NLP实体提取
Then 应识别出金额为1000000
And 应识别出币种为CNY
And 应标准化为数字格式
```

### Scenario: 处理模糊实体
```gherkin
Given 招标文本中招标人信息不明确
When 系统执行NLP实体提取
Then 应将置信度标记为低于0.6
And 应标记为需要人工审核
And 不应写入正式字段
```

---

## Feature: 智能分类

### Scenario: 按行业自动分类
```gherkin
Given 招标信息标题为"智慧校园信息化建设项目"
And 描述包含"服务器、网络设备、软件系统"
When 系统执行自动分类
Then 应分类到"信息技术"行业
And 应分类到"教育"领域
And 置信度应大于0.75
```

### Scenario: 按地区自动分类
```gherkin
Given 招标信息包含"采购单位：广东省某市政府"
When 系统执行地区分类
Then 应分类到"广东省"
And 应分类到"华南"区域
```

### Scenario: 招标人聚类
```gherkin
Given 存在多个招标记录，招标人分别为：
  - "某市人民医院"
  - "某市第一人民医院"
  - "某市人民医院采购中心"
When 系统执行招标人聚类
Then 应将上述记录归为一组
And 应标识为同一实体"某市人民医院"
```

---

## Feature: 商机分析与推荐

### Scenario: 生成商机评分
```gherkin
Given 用户关注关键词为"医疗设备、信息化"
And 招标信息为"某县人民医院智慧医疗系统建设项目"
And 预算金额为500万
And 距离截止还有30天
When 系统计算商机评分
Then 评分应大于70分
And 应标记为"高优先级商机"
```

### Scenario: 竞品中标分析
```gherkin
Given 用户关注"医疗设备"品类
And 历史数据中竞争对手"A公司"在该品类中标率为30%
When 系统分析竞争态势
Then 应生成竞品中标趋势图表
And 应提示"竞争激烈，建议差异化策略"
```

### Scenario: 个性化推荐
```gherkin
Given 用户历史浏览了10个"IT设备"类招标
And 用户所在企业主营业务为"计算机硬件"
When 系统生成推荐列表
Then 前5条推荐中IT设备类招标应不少于3条
And 推荐排序应按商机评分降序
```

### Scenario: 商机预警通知
```gherkin
Given 用户订阅了关键词"人工智能"
And 用户设置了通知方式为"邮件+站内信"
When 系统爬取到包含"AI智能平台"的新招标
Then 应在15分钟内发送邮件通知
And 应在站内生成消息提醒
And 通知应包含招标标题、预算、截止时间
```

---

## Feature: 搜索与查询

### Scenario: 关键词全文搜索
```gherkin
Given 数据库中有10000条招标记录
When 用户搜索关键词"云计算"
Then 应在1秒内返回结果
And 结果应包含标题或描述中包含"云计算"的记录
And 应按相关性排序
```

### Scenario: 多条件组合筛选
```gherkin
Given 用户设置了筛选条件：
  - 地区：广东省
  - 行业：信息技术
  - 预算范围：100万-500万
  - 发布时间：近30天
When 用户执行搜索
Then 应返回满足所有条件的记录
And 结果数量应显示在页面上
And 应支持分页浏览
```

### Scenario: 搜索结果高亮
```gherkin
Given 用户搜索关键词"智慧医院"
When 系统返回搜索结果
Then 关键词应在标题中高亮显示
And 关键词应在描述摘要中高亮显示
And 应显示匹配内容的上下文摘要
```

---

## Feature: 数据可视化

### Scenario: 展示招标趋势图表
```gherkin
Given 用户进入仪表盘页面
When 页面加载完成
Then 应显示最近12个月的招标数量趋势图
And 图表应支持按行业筛选
And 悬停应显示具体数值
```

### Scenario: 招标人画像分析
```gherkin
Given 用户选择查看招标人"某市人民医院"
When 用户进入详情页面
Then 应显示该招标人的历史招标数量
And 应显示历史采购金额趋势
And 应显示常用供应商Top5
And 应显示采购品类分布饼图
```

### Scenario: 数据导出
```gherkin
Given 用户搜索到500条招标记录
When 用户点击"导出Excel"
Then 应在10秒内生成Excel文件
And 文件应包含所有搜索结果的完整字段
And 应提供下载链接
```

---

## Feature: 用户权限管理

### Scenario: 角色权限控制
```gherkin
Given 用户角色为"销售/业务人员"
When 用户访问系统功能
Then 应可以查看所有招标信息
And 应可以设置个人订阅
And 不应可以访问爬虫配置
And 不应可以管理其他用户
```

### Scenario: 数据权限隔离
```gherkin
Given 用户A属于"华南区"
Given 用户B属于"华北区"
When 系统管理员配置了区域数据隔离
Then 用户A只能看到广东省、广西省的招标
And 用户B只能看到北京市、天津市的招标
```

---

## Feature: 系统监控

### Scenario: 爬虫任务监控
```gherkin
Given 管理员进入系统监控页面
When 页面加载完成
Then 应显示今日所有爬虫任务状态
And 应显示成功/失败/运行中任务数量
And 失败任务应显示错误信息
And 应显示平均爬取时长
```

### Scenario: 系统性能监控
```gherkin
Given 系统运行中
When 管理员查看性能监控
Then 应显示API响应时间(P95)
And 应显示数据库连接数
And 应显示Celery队列长度
And 应显示内存和CPU使用率
```

---

## Feature: 订阅管理

### Scenario: 创建订阅规则
```gherkin
Given 用户进入订阅管理页面
When 用户创建新订阅：
  - 关键词：人工智能、AI、大模型
  - 地区：全国
  - 行业：信息技术
  - 最小金额：100万
Then 应保存订阅规则
And 系统应在有新匹配招标时发送通知
```

### Scenario: 订阅关键词匹配
```gherkin
Given 用户订阅了关键词"智慧医疗"
When 系统爬取到新招标"某医院智慧医疗信息化项目"
Then 应判定为匹配成功
And 应触发通知流程
```

---

## Testing Strategy

### 单元测试
- 每个Service类应有对应的单元测试
- 每个Repository方法应有测试覆盖
- NLP提取函数应有多种输入场景的测试

### 集成测试
- 爬虫Pipeline端到端测试
- API端点到端点测试
- 数据库事务测试

### E2E测试
- 关键用户旅程：搜索->查看->订阅->接收通知
- 爬虫完整流程：配置->运行->验证数据
- 管理操作：登录->配置爬虫->监控任务

### 性能测试
- API响应时间测试 (<500ms P95)
- 并发用户测试 (100+用户)
- 大数据量查询测试 (百万级记录)

---

*本文档基于 superpowers:behavior-driven-development 技能生成*
