#!/bin/bash
# 快速部署更新脚本 - 用于更新已部署的生产环境

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "   设备管理系统 - 快速更新脚本"
echo "=========================================="
echo ""

# 目标部署路径（根据实际情况修改）
DEPLOY_PATH="/opt/device-manager"

# 检查部署路径是否存在
if [ ! -d "$DEPLOY_PATH" ]; then
    echo -e "${RED}错误: 部署路径不存在: $DEPLOY_PATH${NC}"
    echo "请修改脚本中的 DEPLOY_PATH 变量"
    exit 1
fi

echo -e "${GREEN}[1/5]${NC} 备份当前版本..."
sudo cp "$DEPLOY_PATH/backend/app.py" "$DEPLOY_PATH/backend/app.py.backup.$(date +%Y%m%d_%H%M%S)"
echo "     已备份到: app.py.backup.$(date +%Y%m%d_%H%M%S)"

echo ""
echo -e "${GREEN}[2/5]${NC} 复制更新的文件..."
sudo cp backend/app.py "$DEPLOY_PATH/backend/app.py"
echo "     已更新: backend/app.py"

echo ""
echo -e "${GREEN}[3/5]${NC} 运行数据库迁移（确保login_info字段存在）..."
cd "$DEPLOY_PATH"
sudo -u $(stat -c '%U' "$DEPLOY_PATH") python3 check_and_fix_db.py || {
    echo -e "${YELLOW}警告: 数据库检查脚本执行失败，尝试使用migrate_db.py${NC}"
    sudo -u $(stat -c '%U' "$DEPLOY_PATH") python3 migrate_db.py
}

echo ""
echo -e "${GREEN}[4/5]${NC} 重启服务..."
sudo systemctl restart device-manager

echo ""
echo -e "${GREEN}[5/5]${NC} 检查服务状态..."
sleep 2
sudo systemctl status device-manager --no-pager -l

echo ""
echo "=========================================="
echo -e "${GREEN}更新完成！${NC}"
echo "=========================================="
echo ""
echo "现在请："
echo "1. 占用一个设备（确保设备已配置SSH连接）"
echo "2. 查看服务日志以确认是否有调试信息："
echo "   sudo journalctl -u device-manager -f"
echo ""
