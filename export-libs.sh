#!/bin/bash

#####################################################
# 导出 Python 依赖包到本地
# 将所有第三方库打包到 libs/ 目录
#####################################################

set -e

echo "=========================================="
echo "   导出 Python 依赖库到本地"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip3 install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

# 安装依赖
echo ""
echo "安装依赖包..."
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 创建 libs 目录
echo ""
echo "创建 libs 目录..."
rm -rf libs
mkdir -p libs

# 导出所有已安装的包到 libs 目录
echo ""
echo "导出依赖包到 libs/ 目录..."

# 先下载构建依赖（setuptools, wheel 等）
# 注意：使用兼容 Python 3.8 的版本
echo "   下载构建依赖..."
pip3 download "setuptools<70" "wheel" -d libs -i https://mirrors.aliyun.com/pypi/simple/

# 下载项目依赖（包括所有传递依赖）
echo "   下载项目依赖及其所有传递依赖..."
pip3 download -r requirements.txt -d libs -i https://mirrors.aliyun.com/pypi/simple/

# 手动下载 Python 3.8/3.9 需要的额外依赖
echo "   下载 Python 3.8/3.9 兼容性依赖..."
pip3 download "importlib-metadata>=3.6.0" "zipp>=0.5" -d libs -i https://mirrors.aliyun.com/pypi/simple/

# 下载 Linux 平台的二进制包（用于跨平台部署，兼容 Python 3.8）
echo "   下载 Linux x86_64 平台包（Python 3.8+ 兼容）..."
# 下载带源码的包，确保可以在任何平台上安装
pip3 download --no-binary bcrypt "bcrypt>=3.2,<5.0" -d libs -i https://mirrors.aliyun.com/pypi/simple/ 2>/dev/null || true
pip3 download --no-binary MarkupSafe "MarkupSafe>=2.0" -d libs -i https://mirrors.aliyun.com/pypi/simple/ 2>/dev/null || true
# 下载 Python 3.8 兼容的二进制包
pip3 download --platform manylinux2014_x86_64 --python-version 38 --only-binary=:all: "cryptography>=3.3" "PyNaCl>=1.5" "cffi>=1.12" -d libs -i https://mirrors.aliyun.com/pypi/simple/ 2>/dev/null || true

# 获取包数量和大小
PKG_COUNT=$(ls -1 libs/*.whl libs/*.tar.gz 2>/dev/null | wc -l | tr -d ' ')
LIBS_SIZE=$(du -sh libs | cut -f1)

echo ""
echo -e "${GREEN}=========================================="
echo "   导出完成！"
echo "==========================================${NC}"
echo "导出包数量: $PKG_COUNT"
echo "总大小: $LIBS_SIZE"
echo "目录: libs/"
echo ""
echo "现在可以将整个项目（包含 libs/ 目录）打包部署"
echo "部署时无需网络即可安装 Python 依赖"

deactivate
