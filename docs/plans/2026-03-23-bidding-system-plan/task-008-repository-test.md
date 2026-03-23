# Task 008: Repository层测试

## 任务信息

- **任务ID**: 008
- **任务名称**: Repository层测试
- **任务类型**: test
- **依赖任务**: 007 (招标模型实现)

## 测试目标

编写TenderRepository的单元测试，验证查询方法、搜索、过滤和分页功能。

## 创建的文件

- `apps/tenders/repositories/__init__.py` - 包初始化
- `apps/tenders/repositories/tender_repository.py` - Repository接口/抽象类(骨架)
- `apps/tenders/tests/test_repositories.py` - Repository单元测试

## 测试用例

### Test Case 1: get_by_id查询
```python
def test_get_by_id_returns_tender_notice():
    """根据ID获取招标信息"""
    # Arrange: 创建招标记录
    # Act: 调用get_by_id
    # Assert: 返回正确的招标对象
```

### Test Case 2: get_by_id不存在
```python
def test_get_by_id_returns_none_for_nonexistent():
    """获取不存在的招标ID应返回None"""
    # Arrange: 使用不存在的notice_id
    # Act: 调用get_by_id
    # Assert: 返回None
```

### Test Case 3: 搜索标题
```python
def test_search_by_title_keyword():
    """按标题关键词搜索"""
    # Arrange: 创建多个招标记录
    # Act: 使用关键词搜索
    # Assert: 返回匹配的招标列表
```

### Test Case 4: 按招标人过滤
```python
def test_filter_by_tenderer():
    """按招标人名称过滤"""
    # Arrange: 创建不同招标人的记录
    # Act: 按招标人过滤
    # Assert: 只返回该招标人的记录
```

### Test Case 5: 按地区过滤
```python
def test_filter_by_region():
    """按地区过滤招标信息"""
    # Arrange: 创建不同地区的记录
    # Act: 按地区过滤
    # Assert: 只返回该地区的记录
```

### Test Case 6: 按日期范围过滤
```python
def test_filter_by_date_range():
    """按发布日期范围过滤"""
    # Arrange: 创建不同日期的记录
    # Act: 按日期范围过滤
    # Assert: 只返回范围内的记录
```

### Test Case 7: 组合过滤条件
```python
def test_composite_filters():
    """组合多个过滤条件"""
    # Arrange: 创建多样化的测试数据
    # Act: 同时应用地区+日期+关键词过滤
    # Assert: 返回符合所有条件的记录
```

### Test Case 8: 分页查询
```python
def test_pagination():
    """测试分页功能"""
    # Arrange: 创建多条记录
    # Act: 按页大小查询
    # Assert: 返回正确的页数据
```

### Test Case 9: 排序功能
```python
def test_order_by_publish_date_desc():
    """按发布日期降序排序"""
    # Arrange: 创建不同日期的记录
    # Act: 查询并按日期排序
    # Assert: 结果按日期降序排列
```

### Test Case 10: create_or_update创建
```python
def test_create_or_update_creates_new():
    """create_or_update创建新记录"""
    # Arrange: 准备新数据
    # Act: 调用create_or_update
    # Assert: 数据库新增记录
```

### Test Case 11: create_or_update更新
```python
def test_create_or_update_updates_existing():
    """create_or_update更新已存在记录"""
    # Arrange: 创建现有记录
    # Act: 使用相同notice_id更新
    # Assert: 记录被更新，未创建新记录
```

## 实施步骤

1. **创建Repository包结构**
   ```bash
   mkdir -p apps/tenders/repositories
   touch apps/tenders/repositories/__init__.py
   ```

2. **创建Repository骨架**
   ```python
   class TenderRepository:
       @staticmethod
       def get_by_id(notice_id: str) -> Optional[TenderNotice]:
           raise NotImplementedError

       @staticmethod
       def search(keyword: str, **filters) -> QuerySet:
           raise NotImplementedError

       @staticmethod
       def filter_by_region(region: str) -> QuerySet:
           raise NotImplementedError

       @staticmethod
       def filter_by_date_range(start: date, end: date) -> QuerySet:
           raise NotImplementedError

       @staticmethod
       def create_or_update(data: dict) -> Tuple[TenderNotice, bool]:
           raise NotImplementedError
   ```

3. **编写测试文件**
   ```bash
   touch apps/tenders/tests/test_repositories.py
   ```

4. **运行测试**
   ```bash
   pytest apps/tenders/tests/test_repositories.py -v
   ```

## 验证步骤

运行测试命令:
```bash
pytest apps/tenders/tests/test_repositories.py::test_get_by_id_returns_tender_notice -v
pytest apps/tenders/tests/test_repositories.py::test_search_by_title_keyword -v
pytest apps/tenders/tests/test_repositories.py::test_filter_by_tenderer -v
pytest apps/tenders/tests/test_repositories.py::test_filter_by_region -v
pytest apps/tenders/tests/test_repositories.py::test_filter_by_date_range -v
pytest apps/tenders/tests/test_repositories.py::test_composite_filters -v
pytest apps/tenders/tests/test_repositories.py::test_pagination -v
pytest apps/tenders/tests/test_repositories.py::test_create_or_update_creates_new -v
```

**预期结果**: 所有测试失败(RED状态)，因为Repository尚未实现

## 提交信息

```
test: add TenderRepository layer tests

- Test get_by_id query method
- Test search by title keyword
- Test filter by tenderer, region, date range
- Test composite filters combining multiple conditions
- Test pagination with page size and offset
- Test ordering by publish_date desc
- Test create_or_update for both create and update scenarios
- All tests currently failing (RED state)
```
