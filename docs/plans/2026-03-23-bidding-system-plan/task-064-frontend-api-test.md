# Task 064: 前端API集成测试

## 任务信息

- **任务ID**: 064
- **任务名称**: 前端API集成测试
- **任务类型**: test
- **依赖任务**: 063 (Tender API实现), 005 (搭建前端React项目)

## BDD Scenario

```gherkin
Scenario: 前端成功获取招标列表
  Given 后端API已启动并包含招标数据
  And 用户已成功登录
  When React组件挂载并调用useTenders hook
  Then 应显示加载状态
  And 数据加载完成后应显示招标列表
  And 列表应包含标题、招标人、发布日期等信息

Scenario: 前端处理API错误
  Given 后端API返回500错误
  When 前端发起请求
  Then 应显示错误提示信息
  And 应提供重试按钮
  And 错误信息应对用户友好

Scenario: 前端实现搜索功能
  Given 用户输入搜索关键词"软件开发"
  When 点击搜索按钮或按下回车键
  Then 应调用API并传递search参数
  And 搜索结果应替换当前列表
  And URL应更新以反映搜索状态

Scenario: 前端实现筛选功能
  Given 用户选择地区"北京市"和行业"IT"
  When 点击应用筛选按钮
  Then 应调用API并传递region和industry参数
  And 筛选结果应正确显示
  And 筛选条件应保存在URL中

Scenario: 前端实现分页功能
  Given 招标列表有超过20条记录
  When 用户点击下一页按钮
  Then 应调用API获取下一页数据
  And 页面应滚动到顶部
  And 分页状态应正确更新
```

## 测试目标

编写前端API集成测试，包括API客户端、React Hooks、错误处理和状态管理。

## 文件说明

- **测试文件**: `frontend/src/lib/api/tenders.test.ts`
- **测试文件**: `frontend/src/hooks/useTenders.test.ts`
- **测试文件**: `frontend/src/components/TenderList.test.tsx`
- **测试目标**: 尚未实现的API客户端和React Hooks
- **预期状态**: 所有测试初始为失败状态(Red)

## 测试内容

### 1. API客户端测试

```typescript
// frontend/src/lib/api/tenders.test.ts

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getTenders, getTenderById, searchTenders } from './tenders'
import { apiClient } from './client'

vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

describe('Tenders API', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('getTenders', () => {
    it('should fetch tenders with default params', async () => {
      const mockResponse = {
        data: {
          count: 100,
          results: [{ id: 1, title: 'Test Tender' }],
          next: null,
          previous: null,
        },
      }
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

      const result = await getTenders()

      expect(apiClient.get).toHaveBeenCalledWith('/tenders/', {
        params: { page: 1, page_size: 20 },
      })
      expect(result.data.results).toHaveLength(1)
    })

    it('should fetch tenders with search params', async () => {
      const mockResponse = { data: { count: 10, results: [], next: null, previous: null } }
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

      await getTenders({ search: '软件开发', region: '北京' })

      expect(apiClient.get).toHaveBeenCalledWith('/tenders/', {
        params: { page: 1, page_size: 20, search: '软件开发', region: '北京' },
      })
    })

    it('should handle API errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'))

      await expect(getTenders()).rejects.toThrow('Network error')
    })
  })

  describe('getTenderById', () => {
    it('should fetch tender detail', async () => {
      const mockResponse = {
        data: { id: 1, title: 'Test Tender', description: 'Detailed description' },
      }
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

      const result = await getTenderById(1)

      expect(apiClient.get).toHaveBeenCalledWith('/tenders/1/')
      expect(result.data.title).toBe('Test Tender')
    })
  })

  describe('searchTenders', () => {
    it('should search tenders with highlight', async () => {
      const mockResponse = {
        data: {
          count: 5,
          results: [{
            id: 1,
            title: '软件<mark>开发</mark>项目',
            highlighted_title: '软件<mark>开发</mark>项目',
          }],
        },
      }
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

      const result = await searchTenders({ query: '开发', highlight: true })

      expect(apiClient.get).toHaveBeenCalledWith('/tenders/', {
        params: { search: '开发', highlight: true, page: 1, page_size: 20 },
      })
      expect(result.data.results[0].highlighted_title).toContain('<mark>')
    })
  })
})
```

### 2. API客户端基础测试

```typescript
// frontend/src/lib/api/client.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'

describe('API Client', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should include auth token in requests', async () => {
    localStorage.setItem('access_token', 'test_token')

    // Mock axios instance
    const mockGet = vi.fn().mockResolvedValue({ data: {} })
    vi.mock('axios', () => ({
      create: () => ({ get: mockGet, interceptors: { request: { use: vi.fn() } } }),
    }))

    await apiClient.get('/tenders/')

    expect(mockGet).toHaveBeenCalledWith('/tenders/', {
      headers: { Authorization: 'Bearer test_token' },
    })
  })

  it('should handle 401 errors and redirect to login', async () => {
    const mockError = { response: { status: 401 } }
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    // Should clear token and redirect
    await expect(apiClient.get('/tenders/')).rejects.toThrow()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('should handle 500 errors with user-friendly message', async () => {
    const mockError = { response: { status: 500, data: { detail: 'Server error' } } }
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(apiClient.get('/tenders/')).rejects.toThrow('服务器错误，请稍后重试')
  })

  it('should retry on network errors', async () => {
    const mockGet = vi.fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ data: {} })
    vi.mocked(apiClient.get).mockImplementation(mockGet)

    const result = await apiClient.get('/tenders/')

    expect(mockGet).toHaveBeenCalledTimes(2)
  })
})
```

### 3. React Hooks测试

```typescript
// frontend/src/hooks/useTenders.test.ts

import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useTenders, useTenderDetail, useTenderSearch } from './useTenders'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useTenders', () => {
  it('should fetch tenders on mount', async () => {
    const { result } = renderHook(() => useTenders(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toBeDefined()
    expect(result.current.data?.results).toBeInstanceOf(Array)
  })

  it('should support pagination', async () => {
    const { result } = renderHook(() => useTenders({ page: 2 }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.page).toBe(2)
  })

  it('should support filters', async () => {
    const { result } = renderHook(
      () => useTenders({ region: '北京', industry: 'IT' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Verify filters applied
    expect(result.current.data).toBeDefined()
  })

  it('should handle errors', async () => {
    vi.mocked(getTenders).mockRejectedValue(new Error('API Error'))

    const { result } = renderHook(() => useTenders(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe('useTenderDetail', () => {
  it('should fetch tender detail', async () => {
    const { result } = renderHook(() => useTenderDetail(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.id).toBe(1)
  })

  it('should not fetch when id is null', () => {
    const { result } = renderHook(() => useTenderDetail(null), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBeUndefined()
  })
})

describe('useTenderSearch', () => {
  it('should debounce search query', async () => {
    const { result, rerender } = renderHook(
      ({ query }) => useTenderSearch(query),
      {
        wrapper: createWrapper(),
        initialProps: { query: '' },
      }
    )

    // Fast consecutive updates should not trigger multiple requests
    rerender({ query: 'a' })
    rerender({ query: 'ab' })
    rerender({ query: 'abc' })

    // Wait for debounce
    await waitFor(() => expect(result.current.isFetching).toBe(true), {
      timeout: 1000,
    })
  })
})
```

### 4. 组件集成测试

```typescript
// frontend/src/components/TenderList.test.tsx

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TenderList } from './TenderList'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../hooks/useTenders', () => ({
  useTenders: vi.fn(),
}))

describe('TenderList Component', () => {
  const mockTenders = {
    results: [
      { id: 1, title: '招标项目1', tenderer: '招标人A', publish_date: '2024-01-01' },
      { id: 2, title: '招标项目2', tenderer: '招标人B', publish_date: '2024-01-02' },
    ],
    count: 2,
    next: null,
    previous: null,
  }

  it('should display loading state', () => {
    vi.mocked(useTenders).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    })

    render(<TenderList />)

    expect(screen.getByText(/加载中/i)).toBeInTheDocument()
  })

  it('should display tender list', () => {
    vi.mocked(useTenders).mockReturnValue({
      data: mockTenders,
      isLoading: false,
      isError: false,
      error: null,
    })

    render(<TenderList />)

    expect(screen.getByText('招标项目1')).toBeInTheDocument()
    expect(screen.getByText('招标人A')).toBeInTheDocument()
  })

  it('should display error state', () => {
    vi.mocked(useTenders).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Failed to fetch'),
    })

    render(<TenderList />)

    expect(screen.getByText(/加载失败/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /重试/i })).toBeInTheDocument()
  })

  it('should handle search input', async () => {
    const mockRefetch = vi.fn()
    vi.mocked(useTenders).mockReturnValue({
      data: mockTenders,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
    })

    render(<TenderList />)

    const searchInput = screen.getByPlaceholderText(/搜索/i)
    fireEvent.change(searchInput, { target: { value: '软件' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => expect(mockRefetch).toHaveBeenCalled())
  })

  it('should handle pagination', async () => {
    const mockSetPage = vi.fn()
    vi.mocked(useTenders).mockReturnValue({
      data: { ...mockTenders, next: '/api/tenders/?page=2' },
      isLoading: false,
      isError: false,
      error: null,
    })

    render(<TenderList />)

    const nextButton = screen.getByRole('button', { name: /下一页/i })
    fireEvent.click(nextButton)

    expect(mockSetPage).toHaveBeenCalledWith(2)
  })
})
```

### 5. 错误处理测试

```typescript
// frontend/src/lib/errors.test.ts

import { describe, it, expect } from 'vitest'
import { APIError, handleAPIError, isAuthError } from './errors'

describe('Error Handling', () => {
  describe('APIError', () => {
    it('should create APIError with message', () => {
      const error = new APIError('Not found', 404)
      expect(error.message).toBe('Not found')
      expect(error.statusCode).toBe(404)
    })
  })

  describe('handleAPIError', () => {
    it('should handle 401 error', () => {
      const error = { response: { status: 401, data: {} } }
      const result = handleAPIError(error)
      expect(result.message).toBe('登录已过期，请重新登录')
      expect(result.action).toBe('login')
    })

    it('should handle 403 error', () => {
      const error = { response: { status: 403, data: {} } }
      const result = handleAPIError(error)
      expect(result.message).toBe('没有权限执行此操作')
    })

    it('should handle 404 error', () => {
      const error = { response: { status: 404, data: {} } }
      const result = handleAPIError(error)
      expect(result.message).toBe('请求的资源不存在')
    })

    it('should handle 500 error', () => {
      const error = { response: { status: 500, data: { detail: 'Server error' } } }
      const result = handleAPIError(error)
      expect(result.message).toBe('服务器错误，请稍后重试')
    })

    it('should handle network error', () => {
      const error = new Error('Network Error')
      const result = handleAPIError(error)
      expect(result.message).toBe('网络连接失败，请检查网络设置')
    })
  })

  describe('isAuthError', () => {
    it('should return true for 401', () => {
      expect(isAuthError({ response: { status: 401 } })).toBe(true)
    })

    it('should return true for 403', () => {
      expect(isAuthError({ response: { status: 403 } })).toBe(true)
    })

    it('should return false for other errors', () => {
      expect(isAuthError({ response: { status: 500 } })).toBe(false)
    })
  })
})
```

## 测试夹具和Mock数据

```typescript
// frontend/src/lib/api/mocks.ts

export const mockTendersResponse = {
  count: 100,
  results: Array.from({ length: 20 }, (_, i) => ({
    id: i + 1,
    notice_id: `NOTICE-${2024}${String(i + 1).padStart(4, '0')}`,
    title: `招标项目 ${i + 1}`,
    tenderer: `招标人 ${String.fromCharCode(65 + (i % 26))}`,
    budget: 100000 + i * 10000,
    currency: 'CNY',
    publish_date: '2024-03-01',
    deadline_date: '2024-04-01',
    region: ['北京市', '上海市', '广州市'][i % 3],
    industry: ['IT', '建筑', '制造业'][i % 3],
    status: 'processed',
  })),
  next: '/api/v1/tenders/?page=2',
  previous: null,
}

export const mockTenderDetail = {
  id: 1,
  notice_id: 'NOTICE-20240001',
  title: '软件开发项目招标',
  description: '本项目需要开发企业管理系统...',
  tenderer: '某某科技有限公司',
  budget: 500000,
  currency: 'CNY',
  publish_date: '2024-03-01',
  deadline_date: '2024-04-01',
  region: '北京市',
  industry: 'IT',
  source_url: 'http://example.com/tender/1',
  ai_summary: '这是一个软件开发项目...',
  ai_keywords: ['软件', '开发', '系统'],
  relevance_score: 0.95,
}
```

## 运行测试

```bash
# 运行所有前端API测试
cd frontend && npm run test

# 运行特定测试文件
npm run test src/lib/api/tenders.test.ts

# 运行测试并生成覆盖率报告
npm run test -- --coverage

# 以UI模式运行测试
npm run test -- --ui
```

## 预期结果

- 所有测试初始状态为 **FAILED (Red)**
- 测试将报错：无法导入API客户端、Hooks或组件
- 错误信息应指导后续实现工作

## 提交信息

```
test: add frontend API integration test suite

- Add API client tests with mock responses
- Add React hooks tests for TanStack Query
- Add component integration tests for TenderList
- Add error handling tests for various HTTP status codes
- Add test fixtures and mock data
- All tests failing (RED state) as expected
```
