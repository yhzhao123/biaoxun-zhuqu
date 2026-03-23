# Task 005: 搭建前端React项目

**Task ID:** 005
**Task Name:** 搭建前端React项目
**Type:** setup
**Depends-on:** []
**Status:** pending

---

## Description

Set up the frontend project with React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, and Zustand. This provides the foundation for the bidding system UI.

---

## Files to Create

| File | Purpose |
|------|---------|
| `frontend/package.json` | NPM dependencies and scripts |
| `frontend/tsconfig.json` | TypeScript configuration |
| `frontend/tsconfig.node.json` | TypeScript config for Node tooling |
| `frontend/vite.config.ts` | Vite build configuration |
| `frontend/tailwind.config.js` | Tailwind CSS configuration |
| `frontend/postcss.config.js` | PostCSS configuration |
| `frontend/index.html` | HTML entry point |
| `frontend/.eslintrc.cjs` | ESLint configuration |
| `frontend/.prettierrc` | Prettier configuration |
| `frontend/src/main.tsx` | Application entry point |
| `frontend/src/App.tsx` | Root App component |
| `frontend/src/App.css` | App-specific styles |
| `frontend/src/index.css` | Global styles with Tailwind |
| `frontend/src/vite-env.d.ts` | Vite type declarations |
| `frontend/src/types/index.ts` | Global type definitions |
| `frontend/src/store/index.ts` | Zustand store setup |
| `frontend/src/hooks/useStore.ts` | Store hooks |
| `frontend/src/lib/queryClient.ts` | TanStack Query client |
| `frontend/src/lib/api.ts` | API client configuration |
| `frontend/src/components/ui/README.md` | UI component documentation |

## Files to Modify

| File | Changes |
|------|---------|
| `.gitignore` | Add frontend node_modules and build output |

---

## Implementation Steps

### 1. Create Project Structure

```bash
mkdir -p frontend/src/{components/{ui,layout},pages,hooks,lib,store,types,utils}
```

### 2. Initialize Package.json

Create `frontend/package.json`:
```json
{
  "name": "bidding-system-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css,json}\"",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.8.0",
    "@tanstack/react-query-devtools": "^5.8.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0",
    "lucide-react": "^0.294.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "prettier": "^3.1.1",
    "prettier-plugin-tailwindcss": "^0.5.9",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  },
  "engines": {
    "node": ">=18.0.0",
    "pnpm": ">=8.0.0"
  }
}
```

### 3. TypeScript Configuration

Create `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@pages/*": ["src/pages/*"],
      "@hooks/*": ["src/hooks/*"],
      "@lib/*": ["src/lib/*"],
      "@store/*": ["src/store/*"],
      "@types/*": ["src/types/*"],
      "@utils/*": ["src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `frontend/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

### 4. Vite Configuration

Create `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@store': path.resolve(__dirname, './src/store'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          state: ['zustand'],
        },
      },
    },
  },
})
```

### 5. Tailwind CSS Configuration

Create `frontend/tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
```

Create `frontend/postcss.config.js`:
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### 6. ESLint and Prettier Configuration

Create `frontend/.eslintrc.cjs`:
```javascript
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
}
```

Create `frontend/.prettierrc`:
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

### 7. HTML Entry Point

Create `frontend/index.html`:
```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="招标系统 - 智能招标信息聚合平台" />
    <title>招标系统</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### 8. Global Styles

Create `frontend/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground antialiased;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

@layer utilities {
  .animate-in {
    animation: fadeIn 0.3s ease-out;
  }

  .slide-in {
    animation: slideIn 0.3s ease-out;
  }
}
```

Create `frontend/src/App.css`:
```css
/* App-specific styles */
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
```

### 9. Type Definitions

Create `frontend/src/vite-env.d.ts`:
```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

Create `frontend/src/types/index.ts`:
```typescript
// Global type definitions

export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiError {
  message: string
  code?: string
  details?: Record<string, string[]>
}

// Utility types
export type Nullable<T> = T | null
export type Optional<T> = T | undefined
```

### 10. API Client Setup

Create `frontend/src/lib/api.ts`:
```typescript
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import { ApiError, ApiResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

class ApiClient {
  private client: AxiosInstance

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
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token')
          window.location.href = '/login'
        }
        return Promise.reject(this.handleError(error))
      }
    )
  }

  private handleError(error: AxiosError<ApiError>): ApiError {
    if (error.response?.data) {
      return error.response.data
    }
    return {
      message: error.message || 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
    }
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url, config)
    return response.data.data
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<ApiResponse<T>>(url, config)
    return response.data.data
  }
}

export const api = new ApiClient()
export default api
```

### 11. Query Client Setup

Create `frontend/src/lib/queryClient.ts`:
```typescript
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: (failureCount, error) => {
        if (failureCount > 3) return false
        // Don't retry on 404s
        if (error instanceof Error && error.message.includes('404')) return false
        return true
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: false,
    },
  },
})

export default queryClient
```

### 12. Zustand Store Setup

Create `frontend/src/store/index.ts`:
```typescript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

// Auth store
interface AuthState {
  token: string | null
  user: { id: string; email: string; name: string } | null
  isAuthenticated: boolean
  setToken: (token: string | null) => void
  setUser: (user: AuthState['user']) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        token: null,
        user: null,
        isAuthenticated: false,
        setToken: (token) => set({ token, isAuthenticated: !!token }),
        setUser: (user) => set({ user }),
        logout: () => set({ token: null, user: null, isAuthenticated: false }),
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({ token: state.token }),
      }
    ),
    { name: 'AuthStore' }
  )
)

// UI store
interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
}

export const useUIStore = create<UIState>()(
  devtools(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'UIStore' }
  )
)
```

### 13. Application Components

Create `frontend/src/App.tsx`:
```typescript
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { RouterProvider, createBrowserRouter } from 'react-router-dom'
import { queryClient } from '@/lib/queryClient'
import './App.css'

// Routes will be added in subsequent tasks
const router = createBrowserRouter([
  {
    path: '/',
    element: <div className="p-8"><h1>招标系统</h1><p>Welcome to Bidding System</p></div>,
  },
  {
    path: '*',
    element: <div className="p-8"><h1>404</h1><p>Page not found</p></div>,
  },
])

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app-container">
        <RouterProvider router={router} />
      </div>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}

export default App
```

Create `frontend/src/main.tsx`:
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### 14. Update Root .gitignore

Add to `.gitignore`:
```
# Frontend
frontend/node_modules/
frontend/dist/
frontend/.env
frontend/.env.local
frontend/.env.*.local
frontend/*.log
frontend/coverage/
frontend/.vscode/
```

---

## Verification Steps

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Check TypeScript compilation:**
   ```bash
   npm run typecheck
   ```

3. **Run linter:**
   ```bash
   npm run lint
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```
   - Verify Vite server starts on port 5173
   - Open http://localhost:5173 and confirm page loads
   - Check React Query DevTools are accessible

5. **Test production build:**
   ```bash
   npm run build
   npm run preview
   ```
   - Verify build completes without errors
   - Preview server shows the app correctly

6. **Verify Tailwind is working:**
   - Add a Tailwind class like `bg-blue-500` to App.tsx
   - Confirm styles are applied in browser

7. **Test proxy configuration:**
   - Start Django backend on port 8000
   - Make an API call from frontend
   - Verify requests are proxied correctly

---

## Git Commit Message

```
feat: setup React frontend with TypeScript and Vite

- Initialize React 18 project with TypeScript
- Configure Vite with path aliases for clean imports
- Setup Tailwind CSS with custom theme and utilities
- Configure ESLint and Prettier for code quality
- Setup TanStack Query with React Query Devtools
- Create Zustand store for state management
- Implement API client with axios interceptors
- Add development proxy for Django backend
- Configure code splitting for vendor chunks
```
