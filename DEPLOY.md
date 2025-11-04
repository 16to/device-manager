# 🚀 部署指南

## 快速修复服务启动失败

如果部署后服务启动失败，运行故障排查脚本：

```bash
chmod +x troubleshoot.sh
sudo ./troubleshoot.sh
```

## 📦 环境要求

- **Python 版本**: Python 3.6 或更高版本
- **操作系统**: Linux / macOS / Windows
- **网络**: 建议配置国内镜像源以加速安装

## 🔧 推荐版本（已测试）

### Python 3.6 兼容版本

**重要：** Python 3.6 需要使用特定版本以避免兼容性问题：

```
Flask==2.0.3
Flask-CORS>=3.0.0
Flask-SQLAlchemy==2.5.1
Flask-SocketIO==5.3.2
python-socketio==5.7.2
python-engineio==4.3.4
paramiko>=2.7.0
Werkzeug==2.0.3
SQLAlchemy==1.4.46
click==8.0.4
itsdangerous==2.0.1
Jinja2==3.0.3
MarkupSafe==2.0.1
```

### Python 3.7+ 推荐版本

```
Flask==2.3.3
Flask-CORS>=3.0.0
Flask-SQLAlchemy==2.5.1
Flask-SocketIO>=5.0.0,<6.0.0
python-socketio>=5.0.0,<6.0.0
python-engineio>=4.0.0,<5.0.0
paramiko>=2.7.0
Werkzeug==2.3.7
SQLAlchemy==1.4.54
```

**注意：** `deploy.sh` 脚本会自动检测 Python 版本并安装对应的兼容版本。

## 🚀 部署方式

### 方式一：自动部署（推荐）

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

部署完成后，服务会自动启动。如果失败：

```bash
# 查看服务状态
sudo systemctl status device-manager

# 查看日志
sudo journalctl -u device-manager -n 50

# 运行故障排查
sudo ./troubleshoot.sh
```

### 方式二：手动部署

#### 1. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 2. 安装依赖（使用国内镜像）

**Python 3.6 用户**：
```bash
chmod +x install-py36.sh
./install-py36.sh
```

**Python 3.7+ 用户**：
```bash
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

#### 3. 配置系统

编辑 `config.json`：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 3000,
    "debug": false
  },
  "admin": {
    "username": "admin",
    "password": "your_secure_password"
  }
}
```

#### 4. 启动服务

```bash
cd backend
python3 app.py
```

## 🐛 常见问题解决

### 1. 服务启动失败（systemd）

**问题**: `systemctl status device-manager` 显示 `exit-code`

**排查步骤**:

```bash
# 1. 运行故障排查脚本
sudo ./troubleshoot.sh

# 2. 查看详细日志
sudo journalctl -u device-manager -n 100 --no-pager

# 3. 手动测试
cd /opt/device-manager/backend
source /opt/device-manager/.venv/bin/activate
python3 app.py
```

**常见原因**:
- Python 版本过低（需要 >= 3.6）
- 依赖包未正确安装
- 配置文件不存在或格式错误
- 端口被占用
- 文件权限问题

### 2. Flask-SocketIO 版本冲突（Python 3.6）

**错误**: `AttributeError: type object 'Server' has no attribute 'reason'`

**原因**: Python 3.6 需要特定版本的 Flask-SocketIO 和 python-socketio

**解决**:
```bash
cd /opt/device-manager
source .venv/bin/activate

# 卸载冲突的包
pip3 uninstall -y Flask-SocketIO python-socketio python-engineio

# 安装 Python 3.6 兼容版本
pip3 install -i https://mirrors.aliyun.com/pypi/simple/ \
    'python-engineio==4.3.4' \
    'python-socketio==5.7.2' \
    'Flask-SocketIO==5.3.2'

sudo systemctl restart device-manager
```

或使用自动安装脚本：
```bash
cd /opt/device-manager
source .venv/bin/activate
bash install-py36.sh
sudo systemctl restart device-manager
```

### 3. ModuleNotFoundError

**错误**: `ModuleNotFoundError: No module named 'flask'`

**解决**:
```bash
cd /opt/device-manager
source .venv/bin/activate
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
sudo systemctl restart device-manager
```

### 4. SQLAlchemy 版本冲突

**错误**: `AttributeError: module 'sqlalchemy' has no attribute '__all__'`

**解决**:
```bash
cd /opt/device-manager
source .venv/bin/activate
pip3 install 'Flask-SQLAlchemy==2.5.1' 'SQLAlchemy==1.4.54' --force-reinstall
sudo systemctl restart device-manager
```

### 4. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查看占用端口的进程
sudo netstat -tuln | grep :3000
# 或
sudo ss -tuln | grep :3000

# 修改配置文件中的端口
vi /opt/device-manager/config.json

# 重启服务
sudo systemctl restart device-manager
```

### 5. 权限问题

**错误**: `Permission denied`

**解决**:
```bash
# 修改目录所有者
sudo chown -R $USER:$USER /opt/device-manager

# 或给予执行权限
sudo chmod +x /opt/device-manager/.venv/bin/python3
```

## 📊 服务管理命令

```bash
# 启动服务
sudo systemctl start device-manager

# 停止服务
sudo systemctl stop device-manager

# 重启服务
sudo systemctl restart device-manager

# 查看状态
sudo systemctl status device-manager

# 查看实时日志
sudo journalctl -u device-manager -f

# 查看最近50行日志
sudo journalctl -u device-manager -n 50

# 开机自启
sudo systemctl enable device-manager

# 禁用自启
sudo systemctl disable device-manager
```

## 🔍 手动测试步骤

如果 systemd 服务启动失败，按以下步骤手动测试：

```bash
# 1. 进入部署目录
cd /opt/device-manager

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 检查 Python 版本
python3 --version

# 4. 检查依赖包
pip3 list | grep -E "Flask|SQLAlchemy"

# 5. 测试配置文件
python3 -c "import json; print(json.load(open('config.json')))"

# 6. 进入后端目录
cd backend

# 7. 尝试启动
python3 app.py
```

如果手动启动成功，但 systemd 失败，检查：
- systemd 服务文件: `/etc/systemd/system/device-manager.service`
- 工作目录和路径是否正确
- 用户权限是否足够

## 🔐 生产环境建议

### 1. 使用 Gunicorn

```bash
# 安装
pip3 install gunicorn

# 修改 systemd 服务
sudo vi /etc/systemd/system/device-manager.service
```

修改 ExecStart 行：
```ini
ExecStart=/opt/device-manager/.venv/bin/gunicorn -w 4 -b 0.0.0.0:3000 --chdir /opt/device-manager/backend app:app
```

```bash
# 重启服务
sudo systemctl daemon-reload
sudo systemctl restart device-manager
```

### 2. 配置 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:3000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. 启用 HTTPS

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 4. 数据库备份

```bash
# 创建备份脚本
cat > /opt/device-manager/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/device-manager/backups"
mkdir -p $BACKUP_DIR
cp /opt/device-manager/backend/device_manager.db \
   $BACKUP_DIR/device_manager_$(date +%Y%m%d_%H%M%S).db
# 保留最近7天的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x /opt/device-manager/backup.sh

# 添加到 crontab（每天凌晨2点备份）
echo "0 2 * * * /opt/device-manager/backup.sh" | crontab -
```

## 📞 故障排查工具

系统提供了自动故障排查脚本：

```bash
sudo ./troubleshoot.sh [部署目录]
```

该脚本会检查：
- 服务状态
- 系统日志
- Python 版本
- 依赖包
- 配置文件
- 文件权限
- 端口占用

## 🎯 验证部署

```bash
# 检查服务是否运行
curl http://localhost:3000

# 测试 API
curl http://localhost:3000/api/devices

# 查看服务状态
sudo systemctl status device-manager
```

## 📝 重新部署

如需重新部署：

```bash
# 1. 停止服务
sudo systemctl stop device-manager

# 2. 备份数据库
cp /opt/device-manager/backend/device_manager.db /tmp/backup.db

# 3. 重新运行部署脚本
sudo ./deploy.sh

# 4. 如需保留数据，恢复数据库
cp /tmp/backup.db /opt/device-manager/backend/device_manager.db

# 5. 重启服务
sudo systemctl restart device-manager
```

---

**部署完成后，记得修改默认管理员密码！** 🔐
