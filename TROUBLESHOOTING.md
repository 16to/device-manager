# Linux服务器审计日志API 404问题 - 完整排查流程

## 快速修复（推荐首先尝试）

```bash
# 1. 连接到Linux服务器
ssh your-server

# 2. 进入部署目录
cd /opt/device-manager  # 或你的实际部署目录

# 3. 更新代码
git pull

# 4. 停止服务
sudo systemctl stop device-manager

# 5. 运行诊断工具
source .venv/bin/activate
python3 diagnose.py
deactivate

# 根据诊断结果进行修复...
```

## 诊断工具输出分析

### ✅ 正常输出示例
```
============================================================
审计日志功能诊断工具
============================================================

1. 检查配置文件...
   ✅ 配置文件存在: /opt/device-manager/config.json
   ✅ 配置加载成功

2. 检查数据库文件...
   ✅ 数据库文件存在: /opt/device-manager/backend/device_manager.db
   ✅ 数据库大小: 36864 bytes

3. 检查模型导入...
   ✅ 所有模型导入成功

4. 检查数据库表...
   ✅ 数据库表列表: allowed_users, audit_logs, devices, usage_records, users
   ✅ 所有必需的表都存在
   ✅ audit_logs 表字段:
      - id: INTEGER
      - action_type: VARCHAR(50)
      - operator: VARCHAR(100)
      - ip_address: VARCHAR(50)
      - details: TEXT
      - created_at: DATETIME

5. 检查Flask应用路由...
   ✅ 找到 2 个审计日志路由:
      - GET        /api/audit-logs
      - GET        /api/audit-logs/action-types
```

### ❌ 常见错误及解决方案

#### 错误1: 缺少 audit_logs 表
```
❌ 缺少表: audit_logs

解决方案: 运行以下命令重新创建表
python3 init_db.py
```

**修复步骤:**
```bash
cd /opt/device-manager
source .venv/bin/activate
python3 init_db.py
deactivate
sudo systemctl start device-manager
```

#### 错误2: 未找到审计日志路由
```
❌ 未找到审计日志路由
```

**可能原因:**
- app.py 文件未正确更新
- Python缓存文件导致旧代码被加载

**修复步骤:**
```bash
cd /opt/device-manager

# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 确保代码最新
git pull

# 重启服务
sudo systemctl restart device-manager
```

#### 错误3: 模型导入失败
```
❌ 模型导入失败: cannot import name 'AuditLog'
```

**修复步骤:**
```bash
cd /opt/device-manager

# 检查 models.py 是否包含 AuditLog
grep -n "class AuditLog" backend/models.py

# 如果没有，更新代码
git pull

# 清理缓存并重启
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
sudo systemctl restart device-manager
```

## 完整修复流程

### 方案A: 保留数据修复（推荐）

```bash
#!/bin/bash
# 在Linux服务器上执行

cd /opt/device-manager

# 1. 备份数据库
echo "备份数据库..."
cp backend/device_manager.db backend/device_manager.db.backup.$(date +%Y%m%d_%H%M%S)

# 2. 停止服务
echo "停止服务..."
sudo systemctl stop device-manager

# 3. 更新代码
echo "更新代码..."
git pull

# 4. 清理缓存
echo "清理缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 5. 激活虚拟环境
source .venv/bin/activate

# 6. 手动添加缺失的表（不删除现有数据）
echo "检查并创建缺失的表..."
python3 << 'EOFPYTHON'
import sys
import os
sys.path.insert(0, 'backend')

from flask import Flask
from models import db, AuditLog
import json

# 读取配置
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# 创建应用
app = Flask(__name__)
db_path = CONFIG['database']['path']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 只创建缺失的表（不影响现有数据）
with app.app_context():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    
    print(f"现有表: {', '.join(existing_tables)}")
    
    if 'audit_logs' not in existing_tables:
        print("创建 audit_logs 表...")
        db.create_all()
        print("✅ audit_logs 表创建成功")
    else:
        print("✅ audit_logs 表已存在，跳过创建")
    
    # 再次验证
    existing_tables = inspector.get_table_names()
    required_tables = ['devices', 'users', 'usage_records', 'allowed_users', 'audit_logs']
    missing = [t for t in required_tables if t not in existing_tables]
    
    if missing:
        print(f"❌ 仍缺少表: {', '.join(missing)}")
    else:
        print(f"✅ 所有必需的表都已就绪: {', '.join(existing_tables)}")
EOFPYTHON

# 7. 运行诊断
echo "运行诊断..."
python3 diagnose.py

deactivate

# 8. 启动服务
echo "启动服务..."
sudo systemctl start device-manager

# 9. 等待服务启动
sleep 3

# 10. 检查服务状态
echo "检查服务状态..."
sudo systemctl status device-manager --no-pager

# 11. 测试API
echo ""
echo "测试API..."
curl -s http://localhost:3001/api/audit-logs/action-types | python3 -m json.tool

echo ""
echo "修复完成！"
```

### 方案B: 完全重置（数据会丢失）

```bash
#!/bin/bash
cd /opt/device-manager

# 1. 停止服务
sudo systemctl stop device-manager

# 2. 更新代码
git pull

# 3. 删除旧数据库
rm -f backend/device_manager.db

# 4. 重新初始化
source .venv/bin/activate
python3 init_db.py
deactivate

# 5. 启动服务
sudo systemctl start device-manager
sudo systemctl status device-manager
```

## 验证修复

### 1. 检查服务日志
```bash
# 查看启动日志
sudo journalctl -u device-manager -n 100 --no-pager | grep -i "audit"

# 应该看到类似:
# ✅ 数据库表创建成功，当前存在的表: allowed_users, audit_logs, devices, usage_records, users
# ✅ 后台清理任务已启动（每24小时清理30天前的审计日志）
```

### 2. 测试API接口
```bash
# 测试操作类型接口
curl -s http://localhost:3001/api/audit-logs/action-types

# 预期输出:
# {"action_types": [...]}

# 测试列表接口
curl -s "http://localhost:3001/api/audit-logs?page=1&per_page=10"

# 预期输出:
# {"logs": [...], "page": 1, "pages": ..., "per_page": 10, "total": ...}
```

### 3. 详细测试
```bash
# 带详细输出的测试
curl -v http://localhost:3001/api/audit-logs?page=1 2>&1 | grep -E "^< HTTP|^< Content-Type"

# 预期输出:
# < HTTP/1.1 200 OK
# < Content-Type: application/json

# 如果看到 404:
# < HTTP/1.1 404 NOT FOUND
# 说明路由未注册，需要检查app.py
```

## 高级排查

### 检查Python进程
```bash
# 查看正在运行的Python进程
ps aux | grep python3 | grep device-manager

# 检查进程是否加载了正确的代码
sudo lsof -p <PID> | grep app.py
```

### 检查systemd配置
```bash
# 查看服务配置
sudo systemctl cat device-manager

# 确认WorkingDirectory和ExecStart正确
# WorkingDirectory=/opt/device-manager/backend
# ExecStart=/opt/device-manager/.venv/bin/python3 /opt/device-manager/backend/app.py
```

### 手动启动测试
```bash
cd /opt/device-manager/backend
source ../.venv/bin/activate

# 手动启动，查看输出
python3 app.py

# 应该看到:
# ✅ 数据库表创建成功，当前存在的表: allowed_users, audit_logs, devices, usage_records, users
# 🚀 启动设备管理系统
# 📍 主机: 0.0.0.0
# 📍 端口: 3001

# 然后在另一个终端测试:
curl http://localhost:3001/api/audit-logs/action-types
```

## 常见问题FAQ

### Q1: 诊断工具显示表存在，但API仍404
**A:** 可能是路由未正确加载，尝试:
```bash
# 清理所有缓存
cd /opt/device-manager
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 重新安装依赖
source .venv/bin/activate
pip install --upgrade --force-reinstall Flask Flask-SQLAlchemy
deactivate

# 重启
sudo systemctl restart device-manager
```

### Q2: 服务启动失败
**A:** 查看详细日志:
```bash
sudo journalctl -u device-manager -xe
```

### Q3: 数据库文件权限问题
**A:** 修复权限:
```bash
cd /opt/device-manager
sudo chown -R $USER:$USER backend/device_manager.db
chmod 644 backend/device_manager.db
```

### Q4: 虚拟环境问题
**A:** 重建虚拟环境:
```bash
cd /opt/device-manager
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

## 联系支持

如果以上所有方法都无效，请提供以下信息：

1. **诊断工具完整输出:**
```bash
python3 diagnose.py > diagnose_output.txt 2>&1
cat diagnose_output.txt
```

2. **服务日志:**
```bash
sudo journalctl -u device-manager -n 200 > service_logs.txt
cat service_logs.txt
```

3. **系统信息:**
```bash
cat /etc/os-release
python3 --version
pip list | grep -i flask
```

4. **路由列表:**
```bash
cd /opt/device-manager/backend
source ../.venv/bin/activate
python3 -c "
import app
for rule in app.app.url_map.iter_rules():
    print(f'{list(rule.methods - {\"HEAD\", \"OPTIONS\"})} {rule}')
" | grep -i audit
```
