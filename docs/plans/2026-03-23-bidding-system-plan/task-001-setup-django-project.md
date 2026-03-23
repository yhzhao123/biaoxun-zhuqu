# Task 001: 初始化Django项目结构

## 任务信息

- **任务ID**: 001
- **任务名称**: 初始化Django项目结构
- **任务类型**: setup
- **依赖任务**: 无

## 任务描述

初始化Django单体项目的基础结构，包括项目配置、应用目录、依赖管理等。

## 创建的文件

```
biaoxun-zhuqu/
├── config/                      # 项目配置
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py             # 基础配置
│   │   ├── development.py      # 开发环境
│   │   └── production.py       # 生产环境
│   ├── urls.py                 # 根路由
│   ├── wsgi.py                 # WSGI入口
│   └── asgi.py                 # ASGI入口
├── apps/                        # 应用目录
│   ├── __init__.py
│   ├── core/                    # 核心模块
│   ├── tenders/                 # 招标模块
│   ├── crawler/                 # 爬虫模块
│   ├── analysis/                # 分析模块
│   ├── subscriptions/           # 订阅模块
│   └── api/                     # API模块
├── tests/                       # 测试目录
├── requirements/
│   ├── base.txt                 # 基础依赖
│   ├── development.txt          # 开发依赖
│   └── production.txt           # 生产依赖
├── manage.py
└── .env.example                 # 环境变量模板
```

## 实施步骤

1. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **安装基础依赖**
   ```bash
   pip install django djangorestframework django-filter celery redis
   pip install psycopg2-binary python-dotenv
   pip install pytest pytest-django factory-boy
   ```

3. **创建Django项目**
   ```bash
   django-admin startproject config .
   ```

4. **创建应用目录结构**
   - 在 `apps/` 目录下创建各模块子目录
   - 每个应用包含: models.py, views.py, serializers.py, admin.py

5. **配置settings**
   - 拆分base/development/production配置
   - 配置INSTALLED_APPS包含所有应用
   - 配置数据库连接(使用环境变量)

6. **配置pytest**
   ```ini
   # pytest.ini
   [pytest]
   DJANGO_SETTINGS_MODULE = config.settings.development
   python_files = tests.py test_*.py *_tests.py
   ```

## 验证步骤

1. 运行 Django 检查
   ```bash
   python manage.py check
   ```
   预期: `System check identified no issues`

2. 验证应用加载
   ```bash
   python manage.py diffsettings
   ```
   预期: 所有自定义配置正确显示

3. 运行测试框架
   ```bash
   pytest --collect-only
   ```
   预期: 测试收集成功，无错误

## 提交信息

```
chore: initialize Django project structure

- Create Django 4.2 project with config directory
- Set up apps structure (core, tenders, crawler, analysis, subscriptions, api)
- Configure settings split (base/development/production)
- Add requirements files with base dependencies
- Configure pytest for testing
```
