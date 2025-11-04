#!/bin/bash

echo "正在停止服务器设备使用管理系统..."

# 读取配置文件中的端口号
PORT=$(python3 -c "import json; print(json.load(open('config.json'))['server']['port'])" 2>/dev/null || echo "3000")

# 停止占用指定端口的进程
lsof -ti:${PORT} | xargs kill -9 2>/dev/null || true

echo "✅ 服务已停止（端口: ${PORT}）"
