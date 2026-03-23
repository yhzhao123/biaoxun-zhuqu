# Task 062: Tender API测试

## 任务信息

- **任务ID**: 062
- **任务名称**: Tender API测试
- **任务类型**: test
- **依赖任务**: 031 (全文搜索实现), 033 (多条件筛选实现), 035 (搜索结果高亮实现)

## BDD Scenario

```gherkin
Scenario: 通过API获取招标列表
  Given 系统已存在招标数据
  And 用户已认证并持有有效JWT令牌
  When 用户发送GET请求到"/api/v1/tenders/"
  Then 应返回200状态码
  And 响应应包含分页数据
  And 每页默认显示20条记录
  And 响应数据应包含id, title, tenderer, publish_date, budget字段

Scenario: 通过API搜索招标信息
  Given 系统已存在招标数据包含"软件开发"关键词
  And 用户已认证
  When 用户发送GET请求到"/api/v1/tenders/?search=软件开发"
  Then 应返回200状态码
  And 响应应只包含标题或描述中包含"软件开发"的招标
  And 搜索结果应支持高亮显示

Scenario: 通过API筛选招标信息
  Given 系统已存在不同地区和行业的招标数据
  And 用户已认证
  When 用户发送GET请求到"/api/v1/tenders/?region=北京&industry=IT"
  Then 应返回200状态码
  And 响应应只包含北京地区IT行业的招标
  And 返回结果应按发布日期降序排列

Scenario: 通过API获取招标详情
  Given 系统已存在招标数据
  And 用户已认证
  When 用户发送GET请求到"/api/v1/tenders/{id}/"
  Then 应返回200状态码
  And 响应应包含完整的招标详情
  And 响应应包含招标人信息和联系方式
```

## 测试目标

编写Tender API的完整测试套件，包括列表查询、搜索、筛选和详情接口的测试。

## 文件说明

- **测试文件**: `apps/tenders/tests/test_api.py`
- **测试目标**: 尚未存在的API视图和序列化器
- **预期状态**: 所有测试初始为失败状态(Red)

## 测试内容

### 1. API基础测试

```python
def test_tender_list_api_returns_200(self, auth_client, tenders):
    """测试招标列表API返回200"""
    response = auth_client.get('/api/v1/tenders/')
    assert response.status_code == 200

def test_tender_list_returns_paginated_results(self, auth_client, tenders):
    """测试招标列表返回分页结果"""
    response = auth_client.get('/api/v1/tenders/')
    data = response.json()
    assert 'results' in data
    assert 'count' in data
    assert 'next' in data
    assert 'previous' in data

def test_tender_detail_api_returns_200(self, auth_client, tender):
    """测试招标详情API返回200"""
    response = auth_client.get(f'/api/v1/tenders/{tender.id}/')
    assert response.status_code == 200

def test_tender_detail_returns_full_data(self, auth_client, tender):
    """测试招标详情返回完整数据"""
    response = auth_client.get(f'/api/v1/tenders/{tender.id}/')
    data = response.json()
    assert data['id'] == tender.id
    assert data['title'] == tender.title
    assert data['tenderer'] == tender.tenderer
```

### 2. 搜索功能测试

```python
def test_tender_search_by_keyword(self, auth_client, tenders):
    """测试通过关键词搜索招标"""
    response = auth_client.get('/api/v1/tenders/?search=软件开发')
    data = response.json()
    assert data['count'] > 0
    for item in data['results']:
        assert '软件' in item['title'] or '软件' in item.get('description', '')

def test_tender_search_with_highlight(self, auth_client, tenders):
    """测试搜索结果高亮显示"""
    response = auth_client.get('/api/v1/tenders/?search=软件开发&highlight=true')
    data = response.json()
    for item in data['results']:
        assert '<mark>' in item.get('highlighted_title', '') or \
               '<mark>' in item.get('highlighted_description', '')
```

### 3. 筛选功能测试

```python
def test_tender_filter_by_region(self, auth_client, tenders):
    """测试按地区筛选"""
    response = auth_client.get('/api/v1/tenders/?region=北京市')
    data = response.json()
    for item in data['results']:
        assert item['region'] == '北京市'

def test_tender_filter_by_industry(self, auth_client, tenders):
    """测试按行业筛选"""
    response = auth_client.get('/api/v1/tenders/?industry=IT')
    data = response.json()
    for item in data['results']:
        assert item['industry'] == 'IT'

def test_tender_filter_by_budget_range(self, auth_client, tenders):
    """测试按预算范围筛选"""
    response = auth_client.get('/api/v1/tenders/?budget_min=100000&budget_max=500000')
    data = response.json()
    for item in data['results']:
        budget = item.get('budget')
        if budget:
            assert 100000 <= float(budget) <= 500000

def test_tender_filter_by_date_range(self, auth_client, tenders):
    """测试按日期范围筛选"""
    response = auth_client.get('/api/v1/tenders/?publish_date_from=2024-01-01&publish_date_to=2024-12-31')
    data = response.json()
    assert response.status_code == 200
```

### 4. 排序和分页测试

```python
def test_tender_list_sorted_by_publish_date(self, auth_client, tenders):
    """测试招标列表按发布日期排序"""
    response = auth_client.get('/api/v1/tenders/?ordering=-publish_date')
    data = response.json()
    dates = [item['publish_date'] for item in data['results']]
    assert dates == sorted(dates, reverse=True)

def test_tender_list_pagination(self, auth_client, tenders):
    """测试分页功能"""
    response = auth_client.get('/api/v1/tenders/?page_size=10')
    data = response.json()
    assert len(data['results']) <= 10

def test_tender_list_page_navigation(self, auth_client, tenders):
    """测试分页导航"""
    response = auth_client.get('/api/v1/tenders/?page_size=5')
    data = response.json()
    if data['count'] > 5:
        assert data['next'] is not None
```

### 5. 认证和权限测试

```python
def test_tender_list_requires_auth(self, client, tenders):
    """测试招标列表需要认证"""
    response = client.get('/api/v1/tenders/')
    assert response.status_code == 401

def test_tender_list_with_invalid_token(self, client, tenders):
    """测试无效令牌返回401"""
    response = client.get('/api/v1/tenders/', HTTP_AUTHORIZATION='Bearer invalid_token')
    assert response.status_code == 401
```

### 6. 响应格式测试

```python
def test_tender_list_response_format(self, auth_client, tender):
    """测试列表响应格式"""
    response = auth_client.get('/api/v1/tenders/')
    data = response.json()
    assert 'results' in data
    assert isinstance(data['results'], list)
    if data['results']:
        item = data['results'][0]
        required_fields = ['id', 'title', 'tenderer', 'publish_date', 'budget', 'region', 'industry']
        for field in required_fields:
            assert field in item
```

## 测试夹具(Fixtures)

```python
@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def auth_client(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

@pytest.fixture
def tenders(db, tender_factory):
    return tender_factory.create_batch(25)
```

## 运行测试

```bash
# 运行所有API测试
pytest apps/tenders/tests/test_api.py -v

# 运行特定测试
pytest apps/tenders/tests/test_api.py::TestTenderAPI::test_tender_list_api_returns_200 -v
```

## 预期结果

- 所有测试初始状态为 **FAILED (Red)**
- 测试将报错：无法导入序列化器、视图或URL配置
- 错误信息应指导后续实现工作

## 提交信息

```
test: add Tender API test suite

- Add tests for tender list API with pagination
- Add tests for search functionality with highlighting
- Add tests for filter by region, industry, budget, date
- Add tests for authentication and permissions
- Add tests for response format validation
- All tests failing (RED state) as expected
```
