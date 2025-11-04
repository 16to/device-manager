#!/bin/bash

#####################################################
# 设备管理系统 - 故障排查脚本
#####################################################

echo "=========================================="
echo "   设备管理系统 - 故障排查工具"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查服务状态
echo -e "${YELLOW}1. 检查服务状态${NC}"
echo "----------------------------------------"
sudo systemctl status device-manager --no-pager
echo ""

# 查看最近日志
echo -e "${YELLOW}2. 查看最近日志（最后50行）${NC}"
echo "----------------------------------------"
sudo journalctl -u device-manager -n 50 --no-pager
echo ""

# 检查 Python 版本
echo -e "${YELLOW}3. 检查 Python 版本${NC}"
echo "----------------------------------------"
DEPLOY_DIR=${1:-/opt/device-manager}
if [ -f "$DEPLOY_DIR/.venv/bin/python3" ]; then
    PYTHON_VERSION=$($DEPLOY_DIR/.venv/bin/python3 --version)
    echo "虚拟环境 Python: $PYTHON_VERSION"
else
    echo -e "${RED}虚拟环境不存在: $DEPLOY_DIR/.venv${NC}"
fi
echo ""

# 检查依赖包
echo -e "${YELLOW}4. 检查关键依赖包${NC}"
echo "----------------------------------------"
if [ -f "$DEPLOY_DIR/.venv/bin/pip3" ]; then
    $DEPLOY_DIR/.venv/bin/pip3 list | grep -E "Flask|SQLAlchemy|Werkzeug|paramiko|socketio"
else
    echo -e "${RED}pip3 不存在${NC}"
fi
echo ""

# 检查配置文件
echo -e "${YELLOW}5. 检查配置文件${NC}"
echo "----------------------------------------"
if [ -f "$DEPLOY_DIR/config.json" ]; then
    echo -e "${GREEN}✓ config.json 存在${NC}"
    cat "$DEPLOY_DIR/config.json"
else
    echo -e "${RED}✗ config.json 不存在${NC}"
fi
echo ""

# 检查文件权限
echo -e "${YELLOW}6. 检查目录权限${NC}"
echo "----------------------------------------"
ls -la "$DEPLOY_DIR" | head -20
echo ""

# 检查端口占用
echo -e "${YELLOW}7. 检查端口占用${NC}"
echo "----------------------------------------"
PORT=$(python3 -c "import json; print(json.load(open('$DEPLOY_DIR/config.json'))['server']['port'])" 2>/dev/null || echo "3000")
if command -v netstat &> /dev/null; then
    netstat -tuln | grep ":$PORT"
elif command -v ss &> /dev/null; then
    ss -tuln | grep ":$PORT"
fi
echo ""

# 尝试手动启动
echo -e "${YELLOW}8. 建议的手动测试命令${NC}"
echo "----------------------------------------"
echo "cd $DEPLOY_DIR/backend"
echo "source $DEPLOY_DIR/.venv/bin/activate"
echo "python3 app.py"
echo ""

# 常见问题
echo -e "${YELLOW}9. 常见问题和解决方案${NC}"
echo "----------------------------------------"
echo "问题1: ModuleNotFoundError"
echo "  解决: cd $DEPLOY_DIR && source .venv/bin/activate && pip3 install -r requirements.txt"
echo ""
echo "问题2: 端口被占用"
echo "  解决: 修改 config.json 中的端口号，或停止占用该端口的进程"
echo ""
echo "问题3: 权限问题"
echo "  解决: sudo chown -R \$USER:\$USER $DEPLOY_DIR"
echo ""
echo "问题4: Python 版本过低"
echo "  解决: 安装 Python 3.6 或更高版本"
echo ""
echo "问题5: SQLAlchemy 版本冲突"
echo "  解决: pip3 install 'Flask-SQLAlchemy==2.5.1' 'SQLAlchemy==1.4.54'"
echo ""

# 重启服务建议
echo -e "${YELLOW}10. 服务管理命令${NC}"
echo "----------------------------------------"
echo "重启服务: sudo systemctl restart device-manager"
echo "停止服务: sudo systemctl stop device-manager"
echo "查看日志: sudo journalctl -u device-manager -f"
echo "查看状态: sudo systemctl status device-manager"
echo ""

echo "=========================================="
echo "   故障排查完成"
echo "=========================================="
