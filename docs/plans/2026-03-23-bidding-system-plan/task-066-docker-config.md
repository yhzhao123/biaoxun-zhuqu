# Task 066: Docker配置

## 任务信息

- **任务ID**: 066
- **任务名称**: Docker配置
- **任务类型**: config
- **依赖任务**: 065 (前端API集成实现)

## 任务描述

配置Docker容器化部署，支持私有化部署需求。

## 创建的文件

```
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── .dockerignore
└── scripts/
    ├── entrypoint.sh
    └── init-db.sh
```

## 实施步骤

1. **创建后端Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements/production.txt .
   RUN pip install -r production.txt

   COPY . .

   EXPOSE 8000

   CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000"]
   ```

2. **创建前端Dockerfile**
   ```dockerfile
   FROM node:18-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   RUN npm run build

   FROM nginx:alpine
   COPY --from=builder /app/build /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   ```

3. **创建docker-compose.yml**
   ```yaml
   version: '3.8'
   services:
     db:
       image: postgres:15
       environment:
         POSTGRES_DB: tenders
         POSTGRES_USER: ${DB_USER}
         POSTGRES_PASSWORD: ${DB_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data

     redis:
       image: redis:7-alpine
       volumes:
         - redis_data:/data

     backend:
       build:
         context: .
         dockerfile: Dockerfile.backend
       environment:
         DATABASE_URL: postgres://${DB_USER}:${DB_PASSWORD}@db:5432/tenders
         REDIS_URL: redis://redis:6379/0
       depends_on:
         - db
         - redis

     worker:
       build:
         context: .
         dockerfile: Dockerfile.backend
       command: celery -A config worker -l info
       depends_on:
         - db
         - redis

     frontend:
       build:
         context: ./frontend
         dockerfile: Dockerfile.frontend
       ports:
         - "80:80"
       depends_on:
         - backend

   volumes:
     postgres_data:
     redis_data:
   ```

4. **创建启动脚本**
   ```bash
   #!/bin/bash
   # scripts/entrypoint.sh
   python manage.py migrate
   python manage.py collectstatic --noinput
   exec "$@"
   ```

5. **配置.dockerignore**
   ```
   .git
   .venv
   __pycache__
   *.pyc
   .env
   node_modules
   ```

## 验证步骤

1. **构建镜像**
   ```bash
   docker-compose build
   ```

2. **启动服务**
   ```bash
   docker-compose up -d
   ```

3. **验证运行状态**
   ```bash
   docker-compose ps
   ```

4. **测试API访问**
   ```bash
   curl http://localhost/api/v1/health
   ```

## 提交信息

```
chore: add Docker configuration

- Add Dockerfile.backend for Django
- Add Dockerfile.frontend for React
- Add docker-compose.yml with all services
- Add entrypoint and init scripts
- Add .dockerignore
- Support for private deployment
```
