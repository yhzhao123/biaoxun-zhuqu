# 项目目录重构说明

## 清理后的项目结构

```
biaoxun-zhuqu/
├── backend/                    # Django + FastAPI 后端
│   ├── apps/                   # Django apps
│   │   ├── analytics/          # 数据分析模块 (Phase 5)
│   │   ├── api/                # API 模块
│   │   ├── core/               # 核心功能
│   │   ├── crawler/            # 爬虫
│   │   ├── llm/                # LLM 模块
│   │   ├── monitoring/         # 监控
│   │   ├── permissions/        # 权限
│   │   ├── subscriptions/      # 订阅
│   │   ├── tenders/            # 招标
│   │   └── users/              # 用户
│   ├── config/                 # 项目配置
│   ├── database/               # 数据库相关
│   ├── scripts/                # 脚本
│   ├── skills/                 # Skills (符号链接到 ../skills)
│   ├── tests/                  # 测试
│   ├── manage.py               # Django 管理
│   ├── requirements.txt        # Python 依赖
│   ├── Dockerfile              # 后端 Dockerfile
│   ├── pytest.ini              # 测试配置
│   └── db.sqlite3              # 数据库
│
├── frontend/                   # React + TypeScript 前端 (已清理)
│   ├── src/                    # 源代码
│   ├── public/                 # 静态资源
│   ├── e2e/                    # E2E 测试
│   ├── tests/                  # 单元测试
│   ├── package.json            # Node 依赖
│   ├── vite.config.ts          # Vite 配置
│   ├── tsconfig.json           # TypeScript 配置
│   ├── tailwind.config.js      # Tailwind 配置
│   ├── eslint.config.js        # ESLint 配置
│   ├── Dockerfile              # 前端 Dockerfile
│   └── README.md               # 前端说明
│
├── deer-flow/                  # deer-flow 框架 (子模块)
│   ├── backend/                # 后端代码
│   ├── docker/                 # Docker 配置
│   ├── docs/                   # 文档
│   ├── frontend/               # 前端代码
│   ├── scripts/                # 脚本
│   └── skills/                 # Skills
│
├── docker/                     # Docker 配置
│   ├── docker-compose.yml      # Docker Compose
│   ├── docker-compose.prod.yml # 生产配置
│   ├── Dockerfile.backend      # 后端 Dockerfile
│   └── nginx.conf              # Nginx 配置
│
├── docs/                       # 项目文档
│   ├── database/               # 数据库文档
│   ├── frontend-ui-plan.md     # 前端规划
│   └── plans/                  # 计划文档
│
├── skills/                     # deer-flow Skills
│   └── tender-extraction/      # 招标提取 Skill
│
├── scripts/                    # 项目脚本
│   └── cleanup.sh              # 清理脚本
│
├── tests/                      # 集成测试
│
├── .env                        # 环境变量
├── .env.example                # 环境变量示例
├── docker-compose.yml          # Docker Compose (根目录)
├── .gitignore                  # Git 忽略
├── .gitmodules                 # Git 子模块
├── CLAUDE.md                   # 项目说明
├── PROGRESS.md                 # 进度记录
├── Makefile                    # 自动化
└── README.md                   # 项目 README
```

## 需要清理的文件

### frontend/ 目录下的临时文件
- [ ] `frontend/` - 嵌套目录
- [ ] `new_src/` - 临时目录
- [ ] `*-new.*` - 临时文件
- [ ] `*.log` - 日志文件
- [ ] `eslint-new.config.js`
- [ ] `index-new.html`
- [ ] `package-new.json`
- [ ] `postcss-new.config.js`
- [ ] `tailwind-new.config.js`
- [ ] `tsconfig-new.json`
- [ ] `tsconfig-node-new.json`
- [ ] `vite-new.config.ts`

### backend/ 目录下的临时文件
- [ ] `frontend/` - 前端代码 (已移动到根目录)
- [ ] `src/` - 源代码 (部分已移动到 frontend/src)
- [ ] `index.html` - 前端文件
- [ ] `package.json` - 前端配置
- [ ] `postcss.config.js` - 前端配置
- [ ] `tailwind.config.js` - 前端配置
- [ ] `eslint.config.js` - 前端配置
- [ ] `tsconfig.json` - 前端配置
- [ ] `tsconfig.node.json` - 前端配置
- [ ] `vite.config.ts` - 前端配置
- [ ] `frontend.log` - 日志
- [ ] `server.log` - 日志

## 使用说明

1. **启动后端**：
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **启动前端**：
   ```bash
   cd frontend
   npm run dev
   ```

3. **使用 Docker**：
   ```bash
   cd docker
   docker-compose up
   ```

## deer-flow 框架

deer-flow 是一个独立的子模块，位于 `deer-flow/` 目录。
在 backend 中通过 Python 路径或软链接引用。
