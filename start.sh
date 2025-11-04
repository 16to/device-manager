#!/bin/bash

echo "========================================="
echo "  服务器设备使用管理系统 - 启动脚本"
echo "========================================="
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3，请先安装Python3"
    exit 1
fi

echo "✅ Python3 已安装"

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "📥 安装Python依赖包..."
pip3 install -q -r requirements.txt

# 读取配置文件中的端口号
PORT=$(python3 -c "import json; print(json.load(open('config.json'))['server']['port'])" 2>/dev/null || echo "3000")
ADMIN_USER=$(python3 -c "import json; print(json.load(open('config.json'))['admin']['username'])" 2>/dev/null || echo "admin")
ADMIN_PASS=$(python3 -c "import json; print(json.load(open('config.json'))['admin']['password'])" 2>/dev/null || echo "admin123")
DEFAULT_PASS=$(python3 -c "import json; print(json.load(open('config.json'))['user']['default_password'])" 2>/dev/null || echo "123456")

# 启动服务
echo ""
echo "========================================="
echo "🚀 启动服务..."
echo "========================================="
echo ""
cd backend
python app.py &
APP_PID=$!
cd ..

# 等待服务启动
sleep 3

echo ""
echo "========================================="
echo "✅ 系统启动成功！"
echo "========================================="
echo ""
echo "📌 访问地址："
echo "   http://localhost:${PORT}"
echo ""
echo "📌 管理员账号："
echo "   用户名: ${ADMIN_USER}"
echo "   密码: ${ADMIN_PASS}"
echo ""
echo "📌 默认用户密码: ${DEFAULT_PASS}"
echo ""
echo "💡 提示：可在 config.json 中修改配置"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 等待用户中断
wait $APP_PID
