# LLM 调用问题修复计划 (修订版)

## 问题概述

用户报告在LLM配置页面提交后总是提示错误。

**诊断结果 (2026-03-26)**：
```
[1] Ollama (本地模型) - [FAIL] 无法连接
[2] OpenAI           - [FAIL] 未配置API密钥
[3] Claude           - [FAIL] 未配置API密钥
```

**核心问题**：后端与LLM提供商之间的连接完全断开，这是所有错误的根本原因。

---

## 已完成的修复

### Phase 1: 后端健康检查API ✅ 已完成

**文件**: `backend/apps/llm/views.py`

添加了无需认证的健康检查端点：
- GET `/api/v1/llm/configs/health/`
- 检查Ollama、OpenAI、Claude三种提供商状态
- 返回详细错误信息和解决方案

### Phase 2: 测试连接增强 ✅ 已完成

**文件**: `backend/apps/llm/views.py`

改进了测试连接功能：
- 返回详细的错误类型 (connection_error, timeout, http_error等)
- 提供具体的解决方案建议
- 区分不同HTTP状态码的错误原因

### Phase 3: 前端连接状态显示 ✅ 已完成

**文件**: `frontend/src/pages/LLMConfigPage.tsx`

- 页面顶部显示三种提供商的连接状态卡片
- 实时检测各提供商可用性
- 显示具体的错误原因和解决建议

### Phase 4: 前端API服务增强 ✅ 已完成

**文件**: `frontend/src/services/llmApi.ts`

- 添加健康检查API方法
- 改进错误响应拦截器
- 添加用户友好的错误消息

---

## 用户操作指南

### 启动Ollama服务

```bash
# 安装Ollama (如果未安装)
# Windows: 从 https://ollama.ai 下载安装

# 启动服务
ollama serve

# 下载模型
ollama pull qwen2.5:7b

# 验证运行
ollama list
```

### 配置OpenAI/Claude API密钥

在后端服务器设置环境变量：

```bash
# OpenAI
export OPENAI_API_KEY=sk-your-key

# Claude (Anthropic)
export ANTHROPIC_API_KEY=sk-ant-your-key
```

---

## 测试验证

1. 访问 `/llm-config` 页面
2. 点击"检测连接"按钮
3. 查看各提供商状态卡片
4. 如果Ollama不可用，运行 `ollama serve`
5. 添加配置后点击"测试"验证