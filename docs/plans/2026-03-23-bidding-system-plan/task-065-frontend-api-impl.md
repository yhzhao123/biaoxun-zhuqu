# Task 065: 前端API集成实现

## 任务信息

- **任务ID**: 065
- **任务名称**: 前端API集成实现
- **任务类型**: impl
- **依赖任务**: 064 (前端API集成测试)

## BDD Scenario

```gherkin
Scenario: 前端API集成正常工作
  Given 所有前端API测试已定义
  When 实现API客户端、React Hooks和组件
  Then 所有前端API测试应通过
  And 前端应能正确调用后端API
  And 应正确处理加载、错误和数据状态
```

## 实现目标

实现完整的前端API集成，包括API客户端、TanStack Query Hooks、错误处理和组件集成，使所有测试通过。

## 修改的文件

- `frontend/src/lib/api/client.ts` - Axios客户端配置(新建)
- `frontend/src/lib/api/tenders.ts` - 招标API调用(新建)
- `frontend/src/lib/errors.ts` - 错误处理(新建)
- `frontend/src/hooks/useTenders.ts` - React Hooks(新建)
- `frontend/src/components/TenderList.tsx` - 列表组件(新建)
- `frontend/src/providers/QueryProvider.tsx` - QueryClient配置(新建)
- `frontend/package.json` - 添加依赖

## 实施步骤

### 1. 安装依赖

```bash
cd frontend
npm install @tanstack/react-query @tanstack/react-query-devtools axios
npm install -D @tanstack/eslint-plugin-query
```

### 2. 配置API客户端

```typescript
// frontend/src/lib/api/client.ts

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

class APIClient {
  private client: AxiosInstance
  private retryCount: number = 3
  private retryDelay: number = 1000

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const config = error.config as AxiosRequestConfig & { retryCount?: number }

        // Retry on network errors
        if (!error.response && config) {
          config.retryCount = config.retryCount || 0
          if (config.retryCount < this.retryCount) {
            config.retryCount++
            await this.delay(this.retryDelay * config.retryCount)
            return this.client(config)
          }
        }

        // Handle 401 - Token expired
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(new Error('登录已过期，请重新登录'))
        }

        return Promise.reject(this.normalizeError(error))
      }
    )
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  private normalizeError(error: AxiosError): Error {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data as { detail?: string; message?: string }
      const message = data?.detail || data?.message || this.getErrorMessage(status)
      return new Error(message)
    }
    if (error.request) {
      return new Error('网络连接失败，请检查网络设置')
    }
    return new Error(error.message || '未知错误')
  }

  private getErrorMessage(status: number): string {
    const messages: Record<number, string> = {
      403: '没有权限执行此操作',
      404: '请求的资源不存在',
      422: '请求数据验证失败',
      429: '请求过于频繁，请稍后再试',
      500: '服务器错误，请稍后重试',
      502: '服务器暂时不可用',
      503: '服务正在维护中',
    }
    return messages[status] || `请求失败 (${status})`
  }

  // Public methods
  get<T>(url: string, config?: AxiosRequestConfig) {
    return this.client.get<T>(url, config)
  }

  post<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return this.client.post<T>(url, data, config)
  }

  put<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return this.client.put<T>(url, data, config)
  }

  patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return this.client.patch<T>(url, data, config)
  }

  delete<T>(url: string, config?: AxiosRequestConfig) {
    return this.client.delete<T>(url, config)
  }
}

export const apiClient = new APIClient()
```

### 3. 实现招标API

```typescript
// frontend/src/lib/api/tenders.ts

import { apiClient } from './client'

export interface Tender {
  id: number
  notice_id: string
  title: string
  description?: string
  tenderer: string
  budget?: number
  currency: string
  publish_date: string
  deadline_date?: string
  region?: string
  industry?: string
  source_url?: string
  ai_summary?: string
  ai_keywords?: string[]
  relevance_score?: number
  status: string
  created_at: string
  updated_at: string
}

export interface TenderSearchResult extends Tender {
  highlighted_title?: string
  highlighted_description?: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface TenderListParams {
  page?: number
  page_size?: number
  search?: string
  region?: string
  industry?: string
  status?: string
  budget_min?: number
  budget_max?: number
  publish_date_from?: string
  publish_date_to?: string
  ordering?: string
  highlight?: boolean
}

export interface TenderSearchParams {
  query: string
  highlight?: boolean
  page?: number
  page_size?: number
}

// API Functions
export const getTenders = (params: TenderListParams = {}) => {
  const defaultParams: TenderListParams = {
    page: 1,
    page_size: 20,
    ...params,
  }
  return apiClient.get<PaginatedResponse<Tender>>('/tenders/', {
    params: defaultParams,
  })
}

export const getTenderById = (id: number) => {
  return apiClient.get<Tender>(`/tenders/${id}/`)
}

export const searchTenders = (params: TenderSearchParams) => {
  const { query, highlight = false, page = 1, page_size = 20 } = params
  return apiClient.get<PaginatedResponse<TenderSearchResult>>('/tenders/', {
    params: {
      search: query,
      highlight,
      page,
      page_size,
    },
  })
}

export const getTenderStatistics = () => {
  return apiClient.get<{
    total_count: number
    region_distribution: Array<{ region: string; count: number }>
    industry_distribution: Array<{ industry: string; count: number }>
    monthly_trend: Array<{ month: string; count: number }>
  }>('/tenders/statistics/')
}

// Export API object for easy access
export const tendersApi = {
  getTenders,
  getTenderById,
  searchTenders,
  getTenderStatistics,
}
```

### 4. 配置QueryClient

```typescript
// frontend/src/providers/QueryProvider.tsx

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { ReactNode } from 'react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && error.message.includes('403')) {
          return false
        }
        return failureCount < 3
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      refetchOnMount: true,
    },
    mutations: {
      retry: false,
    },
  },
})

interface QueryProviderProps {
  children: ReactNode
}

export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}

export { queryClient }
```

### 5. 实现React Hooks

```typescript
// frontend/src/hooks/useTenders.ts

import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query'
import { useDebounce } from './useDebounce'
import {
  tendersApi,
  TenderListParams,
  TenderSearchParams,
} from '../lib/api/tenders'

// Query keys
export const tenderKeys = {
  all: ['tenders'] as const,
  lists: () => [...tenderKeys.all, 'list'] as const,
  list: (params: TenderListParams) => [...tenderKeys.lists(), params] as const,
  details: () => [...tenderKeys.all, 'detail'] as const,
  detail: (id: number) => [...tenderKeys.details(), id] as const,
  search: (params: TenderSearchParams) => [...tenderKeys.all, 'search', params] as const,
  statistics: () => [...tenderKeys.all, 'statistics'] as const,
}

// Hook: Get tenders list with pagination
export function useTenders(params: TenderListParams = {}) {
  return useQuery({
    queryKey: tenderKeys.list(params),
    queryFn: () => tendersApi.getTenders(params).then((res) => res.data),
    placeholderData: keepPreviousData,
  })
}

// Hook: Get tender detail
export function useTenderDetail(id: number | null) {
  return useQuery({
    queryKey: tenderKeys.detail(id!),
    queryFn: () => tendersApi.getTenderById(id!).then((res) => res.data),
    enabled: id !== null,
  })
}

// Hook: Search tenders with debounce
export function useTenderSearch(params: TenderSearchParams) {
  const debouncedQuery = useDebounce(params.query, 300)

  return useQuery({
    queryKey: tenderKeys.search({ ...params, query: debouncedQuery }),
    queryFn: () =>
      tendersApi
        .searchTenders({ ...params, query: debouncedQuery })
        .then((res) => res.data),
    enabled: debouncedQuery.length > 0,
    placeholderData: keepPreviousData,
  })
}

// Hook: Get tender statistics
export function useTenderStatistics() {
  return useQuery({
    queryKey: tenderKeys.statistics(),
    queryFn: () => tendersApi.getTenderStatistics().then((res) => res.data),
    staleTime: 1000 * 60 * 10, // 10 minutes
  })
}

// Hook: Refresh tenders list
export function useRefreshTenders() {
  const queryClient = useQueryClient()

  return {
    refresh: () => {
      queryClient.invalidateQueries({ queryKey: tenderKeys.lists() })
    },
    refreshDetail: (id: number) => {
      queryClient.invalidateQueries({ queryKey: tenderKeys.detail(id) })
    },
  }
}
```

### 6. 实现防抖Hook

```typescript
// frontend/src/hooks/useDebounce.ts

import { useState, useEffect } from 'react'

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(timer)
    }
  }, [value, delay])

  return debouncedValue
}
```

### 7. 实现招标列表组件

```typescript
// frontend/src/components/TenderList.tsx

import { useState } from 'react'
import { useTenders, useTenderSearch } from '../hooks/useTenders'
import { TenderListItem } from './TenderListItem'
import { Pagination } from './Pagination'
import { SearchInput } from './SearchInput'
import { FilterBar } from './FilterBar'
import { LoadingSpinner } from './LoadingSpinner'
import { ErrorMessage } from './ErrorMessage'

export function TenderList() {
  const [page, setPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    region: '',
    industry: '',
    budget_min: '',
    budget_max: '',
  })

  // Use search hook when query exists, otherwise use list hook
  const searchEnabled = searchQuery.length > 0
  const listQuery = useTenders({
    page,
    page_size: 20,
    ...filters,
  })
  const searchQueryResult = useTenderSearch({
    query: searchQuery,
    page,
    page_size: 20,
    highlight: true,
  })

  const { data, isLoading, isError, error, refetch } = searchEnabled
    ? searchQueryResult
    : listQuery

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setPage(1)
  }

  const handleFilterChange = (newFilters: typeof filters) => {
    setFilters(newFilters)
    setPage(1)
  }

  const handleRetry = () => {
    refetch()
  }

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorMessage
        title="加载失败"
        message={error?.message || '无法加载招标信息'}
        onRetry={handleRetry}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="space-y-4">
        <SearchInput
          value={searchQuery}
          onChange={handleSearch}
          placeholder="搜索招标标题、招标人..."
        />
        <FilterBar filters={filters} onChange={handleFilterChange} />
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600">
        共找到 <span className="font-medium">{data?.count || 0}</span> 条招标信息
      </div>

      {/* Tender List */}
      <div className="space-y-4">
        {data?.results.map((tender) => (
          <TenderListItem
            key={tender.id}
            tender={tender}
            highlighted={searchEnabled}
          />
        ))}
      </div>

      {/* Pagination */}
      {data && data.count > 20 && (
        <Pagination
          currentPage={page}
          totalCount={data.count}
          pageSize={20}
          onPageChange={setPage}
        />
      )}

      {/* Empty state */}
      {data?.results.length === 0 && (
        <div className="py-12 text-center text-gray-500">
          <p>没有找到匹配的招标信息</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setFilters({ region: '', industry: '', budget_min: '', budget_max: '' })
            }}
            className="mt-2 text-blue-600 hover:underline"
          >
            清除筛选条件
          </button>
        </div>
      )}
    </div>
  )
}
```

### 8. 实现子组件

```typescript
// frontend/src/components/TenderListItem.tsx

import { Link } from 'react-router-dom'
import { Tender, TenderSearchResult } from '../lib/api/tenders'

interface TenderListItemProps {
  tender: Tender | TenderSearchResult
  highlighted?: boolean
}

export function TenderListItem({ tender, highlighted }: TenderListItemProps) {
  const searchTender = tender as TenderSearchResult
  const title = highlighted && searchTender.highlighted_title
    ? searchTender.highlighted_title
    : tender.title

  const description = highlighted && searchTender.highlighted_description
    ? searchTender.highlighted_description
    : tender.description

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Link
            to={`/tenders/${tender.id}`}
            className="text-lg font-semibold text-blue-600 hover:underline"
            dangerouslySetInnerHTML={{ __html: title }}
          />
          <p
            className="mt-2 text-sm text-gray-600 line-clamp-2"
            dangerouslySetInnerHTML={{ __html: description || '' }}
          />
        </div>
        {tender.relevance_score && (
          <span className="ml-4 rounded-full bg-green-100 px-2 py-1 text-xs text-green-800">
            匹配度: {(tender.relevance_score * 100).toFixed(0)}%
          </span>
        )}
      </div>

      <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
        <span>招标人: {tender.tenderer}</span>
        {tender.region && <span>地区: {tender.region}</span>}
        {tender.industry && <span>行业: {tender.industry}</span>}
        <span>发布日期: {tender.publish_date}</span>
        {tender.budget && (
          <span className="text-orange-600">
            预算: ¥{tender.budget.toLocaleString()}
          </span>
        )}
      </div>
    </div>
  )
}
```

```typescript
// frontend/src/components/SearchInput.tsx

import { useState, KeyboardEvent } from 'react'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function SearchInput({ value, onChange, placeholder }: SearchInputProps) {
  const [inputValue, setInputValue] = useState(value)

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onChange(inputValue)
    }
  }

  return (
    <div className="relative">
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 px-4 py-2 pl-10 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
      <svg
        className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
      {inputValue && (
        <button
          onClick={() => {
            setInputValue('')
            onChange('')
          }}
          className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      )}
    </div>
  )
}
```

```typescript
// frontend/src/components/ErrorMessage.tsx

interface ErrorMessageProps {
  title: string
  message: string
  onRetry?: () => void
}

export function ErrorMessage({ title, message, onRetry }: ErrorMessageProps) {
  return (
    <div className="rounded-lg bg-red-50 p-6 text-center">
      <h3 className="text-lg font-semibold text-red-800">{title}</h3>
      <p className="mt-2 text-red-600">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700"
        >
          重试
        </button>
      )}
    </div>
  )
}
```

### 9. 配置环境变量

```typescript
// frontend/src/env.d.ts

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

```
# frontend/.env.development
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=招标信息系统
```

### 10. 更新应用入口

```typescript
// frontend/src/main.tsx

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryProvider } from './providers/QueryProvider'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryProvider>
        <App />
      </QueryProvider>
    </BrowserRouter>
  </React.StrictMode>
)
```

## 验证步骤

```bash
# 1. 安装依赖
cd frontend && npm install

# 2. 运行类型检查
npm run type-check

# 3. 运行测试
npm run test

# 4. 启动开发服务器
npm run dev

# 5. 手动测试
# - 访问 http://localhost:5173
# - 登录后查看招标列表
# - 测试搜索功能
# - 测试筛选功能
# - 测试分页功能
```

## 预期结果

- 所有前端API测试通过(GREEN状态)
- API客户端正常工作，包含认证和错误处理
- TanStack Query hooks正常工作，支持缓存和分页
- 组件正确显示加载、错误和数据状态
- 搜索和筛选功能正常工作

## 提交信息

```
feat: implement frontend API integration

- Add Axios API client with auth interceptors and retry logic
- Add tenders API functions with TypeScript types
- Add TanStack Query provider with cache configuration
- Add useTenders, useTenderDetail, useTenderSearch hooks
- Add debounce hook for search optimization
- Add TenderList component with loading/error states
- Add SearchInput, FilterBar, TenderListItem components
- Add error handling and user-friendly error messages
- Configure environment variables for API URL
- All frontend API tests passing (GREEN state)
```
