# LLM API 403 Forbidden 错误修复指南

## 问题原因

403错误表示认证失败，原因包括：
1. 未提供有效的认证Token
2. 后端缺少登录API
3. 用户不存在或未生成Token
4. CORS配置问题

## 修复步骤

### 1. 运行数据库迁移

需要创建 `rest_framework.authtoken` 的数据库表：

```bash
cd E:\github项目\biaoxun-zhuqu\backend
python manage.py migrate
```

### 2. 创建测试用户和Token

```bash
python manage.py shell < scripts/create_test_user.py
```

输出示例：
```
Created user: testuser
Created token: abc123def456...

=== 登录信息 ===
用户名: testuser
密码: testpass123
Token: abc123def456...
```

### 3. 登录并获取Token

#### 方法1: 使用API登录

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

返回：
```json
{
  "token": "abc123def456..."
}
```

#### 方法2: 使用浏览器控制台

1. 打开前端页面
2. 按F12打开开发者工具
3. 在Console中运行：

```javascript
// 加载测试脚本
fetch('/login-test.js')
  .then(r => r.text())
  .then(t => eval(t))
  .then(() => testLogin());
```

#### 方法3: 手动设置Token

```javascript
localStorage.setItem('token', '你的token值');
```

### 4. 验证Token是否生效

在浏览器控制台运行：

```javascript
const token = localStorage.getItem('token');
console.log('Token:', token);

// 测试API
fetch('http://localhost:8000/api/v1/llm/configs/', {
  headers: {
    'Authorization': `Token ${token}`
  }
})
.then(r => r.json())
.then(d => console.log('成功:', d))
.catch(e => console.error('失败:', e));
```

## 已完成的修复

### 后端修复 (config/settings.py)

1. **添加CORS_ALLOW_HEADERS**：明确允许 `authorization` 头
2. **添加rest_framework.authtoken**：启用Token认证
3. **添加登录API**：配置 `/api/v1/auth/login/` 端点

### 前端修复 (src/services/llmApi.ts)

已修复Token格式：
```typescript
// 错误的格式（JWT风格）
config.headers.Authorization = `Bearer ${token}`;

// 正确的格式（DRF风格）
config.headers.Authorization = `Token ${token}`;
```

## 常见问题

### Q: 迁移失败或找不到表

A: 确保在正确的目录运行命令：
```bash
cd E:\github项目\biaoxun-zhuqu\backend
python manage.py migrate
```

### Q: 登录返回 "Invalid username/password"

A: 先运行创建用户的脚本：
```bash
python manage.py shell < scripts/create_test_user.py
```

### Q: 仍然收到403错误

A: 检查以下几点：
1. 确认Token格式是 `Token abc123` 而不是 `Bearer abc123`
2. 检查浏览器Network标签，查看请求头中的Authorization
3. 确认后端服务已重启
4. 检查CORS错误（通常是不同的问题，会有不同的错误信息）

### Q: 如何查看当前的token

A: 在浏览器控制台：
```javascript
localStorage.getItem('token');
```

### Q: 如何清除token重新登录

A: 在浏览器控制台：
```javascript
localStorage.removeItem('token');
location.reload();
```

## 快速检查清单

- [ ] 后端数据库迁移已运行
- [ ] 测试用户已创建
- [ ] 前端服务已重启（加载了修改后的llmApi.ts）
- [ ] 后端服务已重启（加载了新的settings.py和urls.py）
- [ ] Token已保存到localStorage
- [ ] 请求头中包含正确的 `Authorization: Token xxx`

## 测试命令

```bash
# 1. 后端迁移
cd backend
python manage.py migrate

# 2. 创建用户
python manage.py shell < scripts/create_test_user.py

# 3. 启动后端
python manage.py runserver

# 4. 在另一个窗口启动前端
cd ../frontend
npm run dev

# 5. 登录获取token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# 6. 使用token访问LLM API
curl http://localhost:8000/api/v1/llm/configs/ \
  -H "Authorization: Token <your-token>"
```
