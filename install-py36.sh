#!/bin/bash

#####################################################
# Python 3.6 环境依赖安装脚本
# 用于解决 Python 3.6 的版本兼容问题
#####################################################

set -e

echo "=========================================="
echo "   Python 3.6 环境依赖安装"
echo "=========================================="
echo ""

# 检查 Python 版本
PYTHON_CMD=${1:-python3}
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "检测到 Python 版本: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -lt 6 ]; then
    echo "❌ 错误：需要 Python 3.6 或更高版本"
    exit 1
fi

# 使用阿里云镜像
MIRROR="https://mirrors.aliyun.com/pypi/simple/"

echo ""
echo "开始安装依赖包..."
echo "使用镜像: $MIRROR"
echo ""

# Python 3.6 需要特定版本
if [ "$PYTHON_MINOR" -eq 6 ]; then
    echo "为 Python 3.6 安装兼容版本..."
    
    # 先卸载可能冲突的包
    $PYTHON_CMD -m pip uninstall -y Flask Flask-SocketIO python-socketio python-engineio Flask-SQLAlchemy SQLAlchemy 2>/dev/null || true
    
    # 安装兼容 Python 3.6 的版本
    $PYTHON_CMD -m pip install -i $MIRROR \
        'Flask==2.0.3' \
        'Flask-CORS>=3.0.0' \
        'Werkzeug==2.0.3' \
        'click==8.0.4' \
        'itsdangerous==2.0.1' \
        'Jinja2==3.0.3' \
        'MarkupSafe==2.0.1' \
        'importlib-metadata>=4.0.0' \
        'Flask-SQLAlchemy==2.5.1' \
        'SQLAlchemy==1.4.46' \
        'python-engineio==4.3.4' \
        'python-socketio==5.7.2' \
        'Flask-SocketIO==5.3.2' \
        'paramiko>=2.7.0'
        
    echo ""
    echo "✅ Python 3.6 兼容版本安装完成"
else
    echo "为 Python 3.7+ 安装推荐版本..."
    
    # Python 3.7+ 可以使用较新版本
    $PYTHON_CMD -m pip install -i $MIRROR \
        'Flask>=2.0.0,<3.0.0' \
        'Flask-CORS>=3.0.0' \
        'Werkzeug>=2.0.0,<3.0.0' \
        'Flask-SQLAlchemy>=2.5.0,<3.0.0' \
        'SQLAlchemy>=1.4.0,<2.0.0' \
        'python-engineio>=4.0.0,<5.0.0' \
        'python-socketio>=5.0.0,<6.0.0' \
        'Flask-SocketIO>=5.0.0,<6.0.0' \
        'paramiko>=2.7.0'
    
    echo ""
    echo "✅ 依赖包安装完成"
fi

echo ""
echo "=========================================="
echo "   安装完成！"
echo "=========================================="
echo ""
echo "已安装的包版本："
$PYTHON_CMD -m pip list | grep -E "Flask|SQLAlchemy|Werkzeug|socketio|paramiko"
