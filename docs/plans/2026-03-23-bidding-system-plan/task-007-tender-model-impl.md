# Task 007: 招标模型实现

## 任务信息

- **任务ID**: 007
- **任务名称**: 招标模型实现
- **任务类型**: impl
- **依赖任务**: 006 (招标模型测试)

## BDD Scenario

```gherkin
Scenario: 成功爬取政府采购网信息
  Given 爬虫任务"政府采购网-每日更新"已配置
  And 目标URL为"http://www.ccgp.gov.cn/"
  When 爬虫在每日凌晨2:00启动
  Then 应在4小时内完成爬取
  And 成功提取的招标信息数量应大于0
  And 所有提取的数据应包含title、notice_id、tenderer字段
```

## 实现目标

实现 TenderNotice 模型，使所有模型测试通过。

## 修改的文件

- `apps/tenders/models.py` - 招标信息模型
- `apps/tenders/admin.py` - Admin配置

## 实施步骤

1. **定义模型字段**
   ```python
   class TenderNotice(models.Model):
       class Status(models.TextChoices):
           PENDING = 'pending', '待处理'
           PROCESSED = 'processed', '已处理'
           ANALYZED = 'analyzed', '已分析'

       notice_id = models.CharField(max_length=64, unique=True)
       title = models.CharField(max_length=500)
       description = models.TextField(blank=True)
       tenderer = models.CharField(max_length=200, blank=True)
       budget = models.DecimalField(max_digits=15, decimal_places=2, null=True)
       currency = models.CharField(max_length=3, default='CNY')
       publish_date = models.DateField()
       deadline_date = models.DateField(null=True, blank=True)
       region = models.CharField(max_length=100, blank=True)
       industry = models.CharField(max_length=100, blank=True)
       source_url = models.URLField()
       source_site = models.CharField(max_length=100, blank=True)
       ai_summary = models.TextField(blank=True)
       ai_keywords = models.JSONField(default=list, blank=True)
       ai_category = models.CharField(max_length=50, blank=True)
       relevance_score = models.DecimalField(max_digits=5, decimal_places=4, null=True)
       status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
       crawl_batch_id = models.BigIntegerField(null=True)
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)
   ```

2. **添加索引**
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['-publish_date']),
           models.Index(fields=['tenderer', '-publish_date']),
           models.Index(fields=['region', '-publish_date']),
           models.Index(fields=['-relevance_score']),
       ]
   ```

3. **实现__str__方法**
   ```python
   def __str__(self):
       return f"{self.notice_id} - {self.title[:50]}"
   ```

4. **配置Admin**
   ```python
   @admin.register(TenderNotice)
   class TenderNoticeAdmin(admin.ModelAdmin):
       list_display = ['notice_id', 'title', 'tenderer', 'publish_date', 'status']
       list_filter = ['status', 'region', 'industry', 'publish_date']
       search_fields = ['notice_id', 'title', 'tenderer', 'description']
   ```

5. **创建迁移文件**
   ```bash
   python manage.py makemigrations tenders
   ```

## 验证步骤

运行测试命令:
```bash
pytest apps/tenders/tests/test_models.py -v
```

**预期结果**: 所有测试通过(GREEN状态)

## 提交信息

```
feat: implement TenderNotice model

- Add TenderNotice model with all required fields
- Add database indexes for common queries
- Configure Django Admin with list/filter/search
- Create migration file
- All tests passing (GREEN state)
```
