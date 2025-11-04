#!/bin/bash

#####################################################
# 设备管理系统 - 自动部署脚本
# 支持 Ubuntu/Debian/CentOS/RedHat
# 作者: Device Manager Team
# 日期: 2025-11-04
#####################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 打印欢迎信息
print_header() {
    echo "=========================================="
    echo "   设备管理系统 - 自动部署脚本"
    echo "=========================================="
    echo ""
}

# 检测操作系统
detect_os() {
    log_step "检测操作系统..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    log_info "操作系统: $OS $VER"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warn "当前以root用户运行"
        USE_SUDO=""
    else
        log_info "当前为普通用户，将使用sudo"
        USE_SUDO="sudo"
    fi
}

# 安装Python3
install_python() {
    log_step "检查Python3安装..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python3已安装: $PYTHON_VERSION"
        return 0
    fi
    
    log_warn "Python3未安装，开始安装..."
    
    case "$OS" in
        ubuntu|debian)
            $USE_SUDO apt-get update
            $USE_SUDO apt-get install -y python3 python3-pip python3-venv
            ;;
        centos|rhel|fedora)
            $USE_SUDO yum install -y python3 python3-pip
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    log_info "Python3安装完成"
}

# 安装必要的系统依赖
install_dependencies() {
    log_step "安装系统依赖..."
    
    case "$OS" in
        ubuntu|debian)
            $USE_SUDO apt-get update
            $USE_SUDO apt-get install -y curl wget git
            ;;
        centos|rhel|fedora)
            $USE_SUDO yum install -y curl wget git
            ;;
    esac
    
    log_info "系统依赖安装完成"
}

# 获取部署配置
get_config() {
    log_step "配置部署参数..."
    
    # 部署目录
    read -p "请输入部署目录 [默认: /opt/device-manager]: " DEPLOY_DIR
    DEPLOY_DIR=${DEPLOY_DIR:-/opt/device-manager}
    
    # 服务端口
    read -p "请输入服务端口 [默认: 3000]: " SERVER_PORT
    SERVER_PORT=${SERVER_PORT:-3000}
    
    # 管理员用户名
    read -p "请输入管理员用户名 [默认: admin]: " ADMIN_USER
    ADMIN_USER=${ADMIN_USER:-admin}
    
    # 管理员密码
    read -s -p "请输入管理员密码 [默认: admin123]: " ADMIN_PASS
    echo ""
    ADMIN_PASS=${ADMIN_PASS:-admin123}
    
    # 确认配置
    echo ""
    log_info "部署配置："
    echo "  部署目录: $DEPLOY_DIR"
    echo "  服务端口: $SERVER_PORT"
    echo "  管理员用户名: $ADMIN_USER"
    echo "  管理员密码: ********"
    echo ""
    read -p "确认以上配置? [Y/n]: " CONFIRM
    CONFIRM=${CONFIRM:-Y}
    
    if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
        log_error "部署已取消"
        exit 0
    fi
}

# 创建部署目录
create_deploy_dir() {
    log_step "创建部署目录..."
    
    if [ -d "$DEPLOY_DIR" ]; then
        log_warn "目录已存在: $DEPLOY_DIR"
        read -p "是否清空并重新部署? [y/N]: " CLEAN
        CLEAN=${CLEAN:-N}
        if [[ $CLEAN =~ ^[Yy]$ ]]; then
            $USE_SUDO rm -rf "$DEPLOY_DIR"
            log_info "已清空目录"
        else
            log_error "部署已取消"
            exit 0
        fi
    fi
    
    $USE_SUDO mkdir -p "$DEPLOY_DIR"
    $USE_SUDO chown -R $USER:$USER "$DEPLOY_DIR"
    log_info "部署目录创建完成: $DEPLOY_DIR"
}

# 复制项目文件
copy_files() {
    log_step "复制项目文件..."
    
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    # 复制所有文件
    cp -r "$SCRIPT_DIR"/* "$DEPLOY_DIR/" 2>/dev/null || true
    
    # 确保必要的目录存在
    mkdir -p "$DEPLOY_DIR/backend"
    mkdir -p "$DEPLOY_DIR/frontend"
    mkdir -p "$DEPLOY_DIR/frontend/static"
    
    log_info "项目文件复制完成"
}

# 创建配置文件
create_config() {
    log_step "创建配置文件..."
    
    cat > "$DEPLOY_DIR/config.json" << EOF
{
  "server": {
    "host": "0.0.0.0",
    "port": $SERVER_PORT,
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
    
    chmod 600 "$DEPLOY_DIR/config.json"
    log_info "配置文件创建完成"
}

# 安装Python依赖
install_python_deps() {
    log_step "安装Python依赖..."
    
    cd "$DEPLOY_DIR"
    
    # 创建虚拟环境
    python3 -m venv .venv
    source .venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip -q
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q
        log_info "Python依赖安装完成"
    else
        log_warn "requirements.txt不存在，跳过依赖安装"
    fi
    
    deactivate
}

# 配置防火墙
configure_firewall() {
    log_step "配置防火墙..."
    
    # 检查firewalld
    if command -v firewall-cmd &> /dev/null; then
        if systemctl is-active --quiet firewalld; then
            log_info "配置firewalld..."
            $USE_SUDO firewall-cmd --permanent --add-port=$SERVER_PORT/tcp
            $USE_SUDO firewall-cmd --reload
            log_info "防火墙规则已添加"
        fi
    fi
    
    # 检查ufw
    if command -v ufw &> /dev/null; then
        if $USE_SUDO ufw status | grep -q "Status: active"; then
            log_info "配置ufw..."
            $USE_SUDO ufw allow $SERVER_PORT/tcp
            log_info "防火墙规则已添加"
        fi
    fi
}

# 创建systemd服务
create_systemd_service() {
    log_step "创建systemd服务..."
    
    cat > /tmp/device-manager.service << EOF
[Unit]
Description=Device Manager Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$DEPLOY_DIR/.venv/bin/python $DEPLOY_DIR/backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    $USE_SUDO mv /tmp/device-manager.service /etc/systemd/system/
    $USE_SUDO systemctl daemon-reload
    $USE_SUDO systemctl enable device-manager
    
    log_info "systemd服务创建完成"
}

# 启动服务
start_service() {
    log_step "启动服务..."
    
    $USE_SUDO systemctl start device-manager
    sleep 3
    
    if $USE_SUDO systemctl is-active --quiet device-manager; then
        log_info "服务启动成功"
    else
        log_error "服务启动失败"
        $USE_SUDO systemctl status device-manager
        exit 1
    fi
}

# 获取服务器IP
get_server_ip() {
    # 尝试获取公网IP
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "")
    
    # 获取内网IP
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    
    if [ -n "$PUBLIC_IP" ]; then
        SERVER_IP=$PUBLIC_IP
    else
        SERVER_IP=$LOCAL_IP
    fi
}

# 打印部署结果
print_result() {
    get_server_ip
    
    echo ""
    echo "=========================================="
    echo "   部署完成！"
    echo "=========================================="
    echo ""
    log_info "访问地址："
    if [ -n "$PUBLIC_IP" ]; then
        echo "  公网: http://$PUBLIC_IP:$SERVER_PORT"
    fi
    echo "  内网: http://$LOCAL_IP:$SERVER_PORT"
    echo ""
    log_info "管理员账号："
    echo "  用户名: $ADMIN_USER"
    echo "  密码: $ADMIN_PASS"
    echo ""
    log_info "服务管理命令："
    echo "  启动服务: sudo systemctl start device-manager"
    echo "  停止服务: sudo systemctl stop device-manager"
    echo "  重启服务: sudo systemctl restart device-manager"
    echo "  查看状态: sudo systemctl status device-manager"
    echo "  查看日志: sudo journalctl -u device-manager -f"
    echo ""
    log_info "配置文件："
    echo "  $DEPLOY_DIR/config.json"
    echo ""
    log_warn "注意: 请确保服务器安全组/防火墙已开放端口 $SERVER_PORT"
    echo ""
}

# 主函数
main() {
    print_header
    detect_os
    check_root
    install_dependencies
    install_python
    get_config
    create_deploy_dir
    copy_files
    create_config
    install_python_deps
    configure_firewall
    create_systemd_service
    start_service
    print_result
}

# 执行主函数
main
