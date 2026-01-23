#!/bin/bash
# 快速部署更新脚本 - 用于更新已部署的生产环境
# 适用于快捷命令功能更新

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "   设备管理系统 - 快速更新脚本"
echo "   更新内容：快捷命令功能"
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

echo -e "${BLUE}更新内容说明：${NC}"
echo "  - 新增快捷命令管理功能"
echo "  - 管理员可创建最多5个自定义SSH命令按钮"
echo "  - 所有用户可在SSH终端中使用这些快捷按钮"
echo ""

echo -e "${GREEN}[1/7]${NC} 备份当前版本..."
BACKUP_DIR="$DEPLOY_PATH/backups/$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo cp "$DEPLOY_PATH/backend/app.py" "$BACKUP_DIR/app.py.backup"
sudo cp "$DEPLOY_PATH/backend/models.py" "$BACKUP_DIR/models.py.backup"
sudo cp "$DEPLOY_PATH/frontend/index.html" "$BACKUP_DIR/index.html.backup"
echo "     已备份到: $BACKUP_DIR"

echo ""
echo -e "${GREEN}[2/7]${NC} 复制更新的文件..."
sudo cp backend/app.py "$DEPLOY_PATH/backend/app.py"
echo "     已更新: backend/app.py"
sudo cp backend/models.py "$DEPLOY_PATH/backend/models.py"
echo "     已更新: backend/models.py"
sudo cp frontend/index.html "$DEPLOY_PATH/frontend/index.html"
echo "     已更新: frontend/index.html"
sudo cp migrate_db.py "$DEPLOY_PATH/migrate_db.py"
echo "     已更新: migrate_db.py"
sudo cp init_db.py "$DEPLOY_PATH/init_db.py"
echo "     已更新: init_db.py"

echo ""
echo -e "${GREEN}[3/7]${NC} 运行数据库迁移（添加quick_commands表）..."
cd "$DEPLOY_PATH"
sudo -u $(stat -c '%U' "$DEPLOY_PATH") python3 migrate_db.py || {
    echo -e "${YELLOW}警告: 数据库迁移失败，尝试手动创建表${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}[4/7]${NC} 验证数据库表结构..."
sudo -u $(stat -c '%U' "$DEPLOY_PATH") sqlite3 "$DEPLOY_PATH/backend/device_manager.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='quick_commands';" | grep -q "1" && {
    echo "     ✅ quick_commands表创建成功"
} || {
    echo -e "${RED}     ❌ quick_commands表未创建${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}[5/7]${NC} 设置文件权限..."
sudo chown -R $(stat -c '%U' "$DEPLOY_PATH"):$(stat -c '%G' "$DEPLOY_PATH") "$DEPLOY_PATH"
echo "     已设置文件所有权"

echo ""
echo -e "${GREEN}[6/7]${NC} 重启服务..."
sudo systemctl restart device-manager

echo ""
echo -e "${GREEN}[7/7]${NC} 检查服务状态..."
sleep 2
sudo systemctl status device-manager --no-pager -l

echo ""
echo "=========================================="
echo -e "${GREEN}更新完成！${NC}"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 访问系统并以管理员身份登录"
echo "2. 点击顶部导航的 '快捷命令' 标签"
echo "3. 创建快捷命令（最多5个）"
echo "4. 打开SSH终端查看快捷按钮"
echo ""
echo "查看详细文档："
echo "  cat $DEPLOY_PATH/QUICK_COMMANDS_FEATURE.md"
echo ""
