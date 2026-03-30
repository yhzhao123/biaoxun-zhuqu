#!/bin/bash
# 项目目录清理和重构脚本

echo "=== 开始清理项目目录 ==="

# 1. 删除 frontend 下的临时文件和嵌套目录
echo "1. 清理 frontend 临时文件..."
cd frontend || exit 1

# 删除嵌套的 frontend 目录
if [ -d "frontend" ]; then
    echo "  删除嵌套的 frontend/frontend/"
    rm -rf frontend/
fi

# 删除 new_src 目录
if [ -d "new_src" ]; then
    echo "  删除 new_src/"
    rm -rf new_src/
fi

# 删除临时文件
echo "  删除临时文件..."
rm -f *-new.*
rm -f *.log
rm -f server.log

cd ..

# 2. 清理 backend 下的临时文件
echo "2. 清理 backend 临时文件..."
cd backend || exit 1

# 删除 frontend 目录 (backend 下的)
if [ -d "frontend" ]; then
    echo "  删除 backend/frontend/"
    rm -rf frontend/
fi

# 删除 src 目录 (backend 下的)
if [ -d "src" ]; then
    echo "  删除 backend/src/"
    rm -rf src/
fi

# 删除 index.html 和 package.json 等前端文件
rm -f index.html package.json postcss.config.js tailwind.config.js eslint.config.js
rm -f tsconfig.json tsconfig.node.json vite.config.ts

cd ..

echo "=== 清理完成 ==="
echo ""
echo "项目结构："
echo "  - backend/       Django + deer-flow 后端"
echo "  - frontend/      React 前端"
echo "  - deer-flow/     deer-flow 框架 (子模块)"
echo "  - docker/        Docker 配置"
echo "  - docs/          文档"
echo "  - skills/        deer-flow Skills"
echo "  - scripts/       脚本"
