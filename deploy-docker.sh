#!/bin/bash

#####################################################
# 设备管理系统 - 快速部署脚本（Docker版本）
# 使用Docker容器化部署，更简单快速
#####################################################

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "   设备管理系统 - Docker快速部署"
echo "=========================================="
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker未安装，正在安装...${NC}"
    curl -fsSL https://get.docker.com | bash
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker安装完成，请重新登录后再次运行此脚本${NC}"
    exit 0
fi

echo -e "${GREEN}✓ Docker已安装${NC}"

# 获取配置
read -p "服务端口 [默认: 3001]: " PORT
PORT=${PORT:-3001}

read -p "管理员用户名 [默认: admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}

read -s -p "管理员密码 [默认: admin123]: " ADMIN_PASS
echo ""
ADMIN_PASS=${ADMIN_PASS:-admin123}

# 创建Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

# 暴露端口
EXPOSE 3001

# 启动命令
CMD ["python", "backend/app.py"]
EOF

# 创建配置文件
cat > config.json << EOF
{
  "server": {
    "host": "0.0.0.0",
    "port": $PORT,
    "debug": false
  },
  "admin": {
    "username": "$ADMIN_USER",
    "password": "$ADMIN_PASS"
  },
  "database": {
    "path": "backend/device_manager.db"
  },
  "user": {
    "default_password": "123456"
  },
  "socketio": {
    "ping_timeout": 120,
    "ping_interval": 25,
    "max_http_buffer_size": 1073741824
  }
}
EOF

# 创建docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  device-manager:
    build: .
    container_name: device-manager
    ports:
      - "$PORT:$PORT"
    volumes:
      - ./backend/device_manager.db:/app/backend/device_manager.db
      - ./config.json:/app/config.json
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
EOF

# 构建和启动
echo ""
echo -e "${GREEN}正在构建Docker镜像...${NC}"
docker-compose build

echo -e "${GREEN}正在启动服务...${NC}"
docker-compose up -d

# 等待服务启动
sleep 5

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "=========================================="
    echo -e "${GREEN}   部署成功！${NC}"
    echo "=========================================="
    echo ""
    echo "访问地址: http://$(hostname -I | awk '{print $1}'):$PORT"
    echo "管理员: $ADMIN_USER / $ADMIN_PASS"
    echo ""
    echo "管理命令:"
    echo "  启动: docker-compose start"
    echo "  停止: docker-compose stop"
    echo "  重启: docker-compose restart"
    echo "  日志: docker-compose logs -f"
    echo "  卸载: docker-compose down"
    echo ""
else
    echo -e "${RED}服务启动失败，请查看日志: docker-compose logs${NC}"
    exit 1
fi
