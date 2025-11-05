#!/bin/bash

#####################################################
# 下载 Python 依赖到本地 libs 目录
#####################################################

set -e

echo "=========================================="
echo "   下载 Python 依赖到本地"
echo "=========================================="
echo ""

# 创建 libs 目录
rm -rf libs
mkdir -p libs

echo "正在下载依赖包..."
pip3 download -r requirements.txt -d libs --python-version 38 -i https://mirrors.aliyun.com/pypi/simple/

echo ""
echo "✅ 依赖包已下载到 libs/ 目录"
ls -lh libs/ | head -20
echo ""
echo "总大小:"
du -sh libs/
