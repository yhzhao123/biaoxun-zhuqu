# Task 009: Repository层实现

## 任务信息

- **任务ID**: 009
- **任务名称**: Repository层实现
- **任务类型**: impl
- **依赖任务**: 008 (Repository层测试)

## 实现目标

实现TenderRepository类，提供数据访问层封装，支持查询、搜索、过滤、分页和批量操作方法。

## 修改的文件

- `apps/tenders/repositories/tender_repository.py` - Repository完整实现
- `apps/tenders/repositories/__init__.py` - 导出Repository类

## 实施步骤

1. **实现get_by_id方法**
   ```python
   @staticmethod
   def get_by_id(notice_id: str) -> Optional[TenderNotice]:
       """根据notice_id获取招标信息"""
       try:
           return TenderNotice.objects.get(notice_id=notice_id)
       except TenderNotice.DoesNotExist:
           return None
   ```

2. **实现search方法**
   ```python
   @staticmethod
   def search(
       keyword: Optional[str] = None,
       filters: Optional[dict] = None
   ) -> TenderNoticeQuerySet:
       """搜索招标信息

       Args:
           keyword: 标题关键词
           filters: 额外过滤条件
       """
       queryset = TenderNotice.objects.all()

       if keyword:
           queryset = queryset.filter(
               Q(title__icontains=keyword) |
               Q(description__icontains=keyword)
           )

       if filters:
           queryset = TenderRepository._apply_filters(queryset, filters)

       return queryset.order_by('-publish_date')
   ```

3. **实现过滤方法**
   ```python
   @staticmethod
   def _apply_filters(
       queryset: TenderNoticeQuerySet,
       filters: dict
   ) -> TenderNoticeQuerySet:
       """应用过滤条件"""
       if 'tenderer' in filters:
           queryset = queryset.filter(tenderer__icontains=filters['tenderer'])

       if 'region' in filters:
           queryset = queryset.filter(region=filters['region'])

       if 'industry' in filters:
           queryset = queryset.filter(industry=filters['industry'])

       if 'status' in filters:
           queryset = queryset.filter(status=filters['status'])

       if 'date_from' in filters:
           queryset = queryset.filter(publish_date__gte=filters['date_from'])

       if 'date_to' in filters:
           queryset = queryset.filter(publish_date__lte=filters['date_to'])

       if 'min_budget' in filters:
           queryset = queryset.filter(budget__gte=filters['min_budget'])

       if 'max_budget' in filters:
           queryset = queryset.filter(budget__lte=filters['max_budget'])

       return queryset

   @staticmethod
   def filter_by_region(region: str) -> TenderNoticeQuerySet:
       """按地区过滤"""
       return TenderNotice.objects.filter(region=region).order_by('-publish_date')

   @staticmethod
   def filter_by_date_range(
       start: date,
       end: date
   ) -> TenderNoticeQuerySet:
       """按日期范围过滤"""
       return TenderNotice.objects.filter(
           publish_date__range=(start, end)
       ).order_by('-publish_date')
   ```

4. **实现分页方法**
   ```python
   @staticmethod
   def paginate(
       queryset: TenderNoticeQuerySet,
       page: int = 1,
       page_size: int = 20
   ) -> dict:
       """分页查询

       Returns:
           dict: {
               'items': QuerySet,
               'total': int,
               'page': int,
               'page_size': int,
               'total_pages': int
           }
       """
       total = queryset.count()
       total_pages = (total + page_size - 1) // page_size

       offset = (page - 1) * page_size
       items = queryset[offset:offset + page_size]

       return {
           'items': items,
           'total': total,
           'page': page,
           'page_size': page_size,
           'total_pages': total_pages
       }
   ```

5. **实现create_or_update方法**
   ```python
   @staticmethod
   def create_or_update(data: dict) -> Tuple[TenderNotice, bool]:
       """创建或更新招标信息

       Args:
           data: 招标数据字典，必须包含notice_id

       Returns:
           Tuple[对象, 是否新建]
       """
       notice_id = data.get('notice_id')
       if not notice_id:
           raise ValueError("notice_id is required")

       tender, created = TenderNotice.objects.update_or_create(
           notice_id=notice_id,
           defaults=data
       )
       return tender, created
   ```

6. **实现批量操作方法**
   ```python
   @staticmethod
   def bulk_create_or_update(
       items: list[dict],
       batch_size: int = 100
   ) -> tuple[int, int]:
       """批量创建或更新

       Returns:
           tuple[创建数量, 更新数量]
       """
       created_count = 0
       updated_count = 0

       for item in items:
           _, created = TenderRepository.create_or_update(item)
           if created:
               created_count += 1
           else:
               updated_count += 1

       return created_count, updated_count

   @staticmethod
   def get_recent(days: int = 7, limit: int = 100) -> TenderNoticeQuerySet:
       """获取最近N天的招标信息"""
       start_date = timezone.now().date() - timedelta(days=days)
       return TenderNotice.objects.filter(
           publish_date__gte=start_date
       ).order_by('-publish_date')[:limit]
   ```

7. **更新__init__.py导出**
   ```python
   from .tender_repository import TenderRepository

   __all__ = ['TenderRepository']
   ```

## 验证步骤

运行测试命令:
```bash
pytest apps/tenders/tests/test_repositories.py -v
```

**预期结果**: 所有测试通过(GREEN状态)

运行覆盖率检查:
```bash
pytest apps/tenders/tests/test_repositories.py --cov=apps.tenders.repositories --cov-report=term-missing
```

**预期结果**: 覆盖率 >= 80%

## 提交信息

```
feat: implement TenderRepository data access layer

- Add get_by_id with DoesNotExist handling
- Add search with keyword and composite filters
- Add filter methods for region, date range, tenderer
- Add paginate with page/page_size parameters
- Add create_or_update for upsert operations
- Add bulk_create_or_update for batch processing
- Add get_recent for recent notices query
- Export TenderRepository from repositories package
- All tests passing (GREEN state)
```
