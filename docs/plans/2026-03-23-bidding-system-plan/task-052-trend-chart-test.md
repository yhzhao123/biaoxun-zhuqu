# Task 052: 趋势图表组件测试

## 任务信息

- **任务ID**: 052
- **任务名称**: 趋势图表组件测试
- **任务类型**: test
- **依赖任务**: 005 (搭建前端React项目)

## BDD Scenario

```gherkin
Scenario: 展示招标趋势图表
  Given 用户进入仪表盘页面
  When 页面加载完成
  Then 应显示最近12个月的招标数量趋势图
  And 图表应支持按行业筛选
  And 悬停应显示具体数值
```

## 测试目标

测试前端趋势图表组件的渲染和交互功能。

## 创建的文件

- `frontend/src/components/TrendChart.test.tsx` - 趋势图表组件测试

## 测试用例

### Test Case 1: 组件渲染
```typescript
it('renders trend chart with data', () => {
  // Given: 模拟图表数据
  const mockData = [
    { month: '2024-01', count: 150, budget: 15000000 },
    { month: '2024-02', count: 180, budget: 18000000 },
  ];

  // When: 渲染组件
  render(<TrendChart data={mockData} />);

  // Then: 应显示图表标题
  expect(screen.getByText('招标趋势')).toBeInTheDocument();
  expect(screen.getByTestId('echarts-container')).toBeInTheDocument();
});
```

### Test Case 2: 筛选交互
```typescript
it('filters by industry', async () => {
  const mockData = [...];
  const onFilterChange = jest.fn();

  render(<TrendChart data={mockData} onFilterChange={onFilterChange} />);

  // When: 选择行业筛选
  fireEvent.click(screen.getByLabelText('行业筛选'));
  fireEvent.click(screen.getByText('信息技术'));

  // Then: 应触发筛选回调
  expect(onFilterChange).toHaveBeenCalledWith({ industry: '信息技术' });
});
```

### Test Case 3: 空数据处理
```typescript
it('displays empty state when no data', () => {
  render(<TrendChart data={[]} />);

  expect(screen.getByText('暂无数据')).toBeInTheDocument();
});

### Test Case 4: 加载状态
```typescript
it('shows loading state', () => {
  render(<TrendChart data={[]} loading={true} />);

  expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
});
```

## 实施步骤

1. 创建组件测试文件
2. 配置 Jest 和 React Testing Library
3. 编写渲染和交互测试
4. 使用 Mock 隔离 ECharts 依赖

## 验证步骤

```bash
cd frontend && npm test -- TrendChart.test.tsx
```

**预期**: 测试失败，因为组件未实现

## 提交信息

```
test: add TrendChart component tests

- Test chart rendering with data
- Test industry filter interaction
- Test empty data state
- Test loading state
- All tests currently failing (RED)
```
