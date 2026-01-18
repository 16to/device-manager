# 🚀 部署指南

> **📖 相关文档**:  
> - 数据库升级问题？查看 [数据库升级指南](DATABASE_MIGRATION_GUIDE.md)  
> - 登录信息功能不可用？查看 [登录信息故障排除](TROUBLESHOOTING_LOGIN_INFO.md)

## 📦 环境要求

- **Python 版本**: Python 3.8 或更高版本
- **操作系统**: Linux / macOS / Windows
- **网络**: 建议配置国内镜像源以加速安装

## 🔧 推荐版本（已测试）

```
Flask==2.3.3
Flask-CORS>=3.0.0
Flask-SQLAlchemy==2.5.1
Flask-SocketIO>=5.0.0
python-socketio>=5.0.0
python-engineio>=4.0.0
paramiko>=2.7.0
Werkzeug==2.3.7
SQLAlchemy==1.4.54
```

**此版本组合兼容 Python 3.8+，在生产环境中稳定运行。**

## 🚀 部署方式

### 方式一：自动部署（推荐）

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

**部署过程说明：**
1. 检查系统环境和依赖
2. 复制项目文件（自动排除数据库文件）
3. 创建虚拟环境并安装依赖
4. 创建配置文件（config.json）
5. **数据库智能迁移**（自动检测并升级表结构，保留现有数据）
6. 创建 systemd 服务
7. 启动服务

**重要改进：** 
- ✅ 部署时会自动运行数据库迁移脚本
- ✅ 自动检测表结构差异并添加缺失的表/字段
- ✅ 完全保留现有数据，不会删除任何信息
- ✅ 无需手动运行升级脚本

部署完成后，服务会自动启动。如果失败：

```bash
# 查看服务状态
sudo systemctl status device-manager

# 查看日志
sudo journalctl -u device-manager -n 50
```

### 方式二：手动部署

#### 1. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

#### 3. 配置系统

编辑 `config.json`：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 3001,
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

**首次启动会自动创建空数据库和默认管理员账号。**

## 🗄️ 数据库说明

### 数据库智能迁移机制 ⭐新功能

系统现在使用智能迁移机制，**完全自动化**处理数据库升级：

- ✅ **自动检测**：对比代码模型与数据库结构
- ✅ **自动升级**：添加缺失的表和字段
- ✅ **保留数据**：不删除任何现有数据
- ✅ **幂等操作**：可重复运行，安全可靠

**工作原理**：
1. 检查数据库是否存在
2. 如果不存在，创建新数据库和所有表
3. 如果存在，对比每个表的字段
4. 自动添加代码中定义但数据库中缺失的字段
5. 保留所有现有数据和字段

**使用方法**：
```bash
# 自动迁移（推荐）
python3 migrate_db.py

# 或在部署时自动运行
./deploy.sh  # 会自动提示运行迁移
```

### 数据库文件管理

- 数据库文件已添加到 `.gitignore`，不会被提交到代码库
- `deploy.sh` 部署时会自动排除数据库文件
- 每次部署都会创建全新的空数据库
- 如需保留数据，请在部署前手动备份数据库文件

### 数据备份与恢复

```bash
# 备份数据库
cp backend/device_manager.db ~/backup/device_manager_$(date +%Y%m%d).db

# 恢复数据库
cp ~/backup/device_manager_20250104.db backend/device_manager.db

# ⚠️ 重要：恢复旧数据库后，运行智能迁移脚本
python3 migrate_db.py

# 然后重启服务
sudo systemctl restart device-manager
```

**说明**：
- ✅ 使用新的 `migrate_db.py` 脚本，自动检测并升级所有表结构
- ✅ 不再需要运行多个升级脚本（`update_db_add_login_info.py` 已废弃）
- ✅ 一个命令解决所有数据库升级问题
- ✅ 完全保留所有现有数据

## 🐛 常见问题解决

### 1. 服务启动失败（systemd）

**问题**: `systemctl status device-manager` 显示 `exit-code`

**排查步骤**:

```bash
# 1. 查看详细日志
sudo journalctl -u device-manager -n 100 --no-pager

# 2. 手动测试
cd /opt/device-manager/backend
source /opt/device-manager/.venv/bin/activate
python3 app.py
```

**常见原因**:
- Python 版本过低（需要 >= 3.8）
- 依赖包未正确安装
- 配置文件不存在或格式错误
- 端口被占用
- 文件权限问题

### 2. ModuleNotFoundError

**错误**: `ModuleNotFoundError: No module named 'flask'`

**解决**:
```bash
cd /opt/device-manager
source .venv/bin/activate
pip3 install -r requirements.txt
sudo systemctl restart device-manager
```

### 3. SQLAlchemy 版本冲突

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
sudo netstat -tuln | grep :3001
# 或
sudo ss -tuln | grep :3001

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

### 6. 数据库表不存在

**错误**: `no such table: device` 或类似错误

**原因**: 数据库文件损坏或未正确初始化

**解决**:
```bash
cd /opt/device-manager/backend

# 备份旧数据库（如果需要）
mv device_manager.db device_manager.db.old

# 删除数据库文件，让系统重新创建
rm -f device_manager.db*

# 重启服务（会自动创建新数据库）
sudo systemctl restart device-manager
```

### 7. 数据库被意外保留

**问题**: 部署后发现有旧数据

**解决**:
```bash
cd /opt/device-manager/backend
sudo systemctl stop device-manager
rm -f device_manager.db*
sudo systemctl start device-manager
```

## 🔧 服务管理命令

```bash
# 启动服务
sudo systemctl start device-manager

# 停止服务
sudo systemctl stop device-manager

# 重启服务
sudo systemctl restart device-manager

# 查看状态
sudo systemctl status device-manager

# 查看日志
sudo journalctl -u device-manager -f

# 查看最近日志
sudo journalctl -u device-manager -n 50

# 禁用开机自启
sudo systemctl disable device-manager

# 启用开机自启
sudo systemctl enable device-manager
```

## 📊 手动测试

如果 systemd 服务启动失败，可以手动运行进行调试：

```bash
cd /opt/device-manager/backend
source /opt/device-manager/.venv/bin/activate

# 检查 Python 版本
python3 --version

# 检查依赖包
pip3 list | grep -E "Flask|SQLAlchemy|socketio"

# 手动启动（会显示详细错误信息）
python3 app.py
```

## 🌐 生产环境建议

### 1. 使用 Gunicorn + Nginx

```bash
# 安装 Gunicorn
pip3 install gunicorn eventlet

# 创建 Gunicorn 启动脚本
cat > /opt/device-manager/start_gunicorn.sh << 'EOF'
#!/bin/bash
cd /opt/device-manager/backend
source /opt/device-manager/.venv/bin/activate
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:3001 app:app
EOF

chmod +x /opt/device-manager/start_gunicorn.sh

# 配置 Nginx 反向代理
sudo nano /etc/nginx/sites-available/device-manager
```

Nginx 配置示例：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 2. 配置 HTTPS

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 3. 定期备份

```bash
# 创建备份脚本
cat > /opt/backup_device_manager.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/device-manager"
mkdir -p $BACKUP_DIR
cp /opt/device-manager/backend/device_manager.db \
   $BACKUP_DIR/device_manager_$(date +%Y%m%d_%H%M%S).db
# 保留最近30天的备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
EOF

chmod +x /opt/backup_device_manager.sh

# 添加到 crontab（每天凌晨2点备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup_device_manager.sh") | crontab -
```

### 4. 监控和日志轮转

```bash
# 配置日志轮转
sudo cat > /etc/logrotate.d/device-manager << EOF
/var/log/device-manager/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload device-manager > /dev/null 2>&1 || true
    endscript
}
EOF
```

## 📝 更新部署

当有新版本时：

```bash
# 1. 备份数据库
sudo cp /opt/device-manager/backend/device_manager.db ~/backup_$(date +%Y%m%d).db

# 2. 停止服务
sudo systemctl stop device-manager

# 3. 拉取最新代码
cd /path/to/source
git pull

# 4. 重新部署
sudo ./deploy.sh

# 5. 恢复数据库（如果需要保留数据）
sudo cp ~/backup_$(date +%Y%m%d).db /opt/device-manager/backend/device_manager.db

# 6. 重启服务
sudo systemctl restart device-manager
```

## 🔐 安全建议

1. **修改默认密码**: 在 `config.json` 中修改管理员密码
2. **使用 HTTPS**: 配置 SSL 证书
3. **防火墙**: 只开放必要的端口
4. **定期更新**: 保持系统和依赖包更新
5. **备份**: 定期备份数据库文件
6. **访问控制**: 使用 Nginx 添加 IP 白名单或基础认证

---

**部署完成后访问**: http://your-server-ip:3001

默认管理员账号：
- 用户名：admin
- 密码：admin123（请及时修改！）
