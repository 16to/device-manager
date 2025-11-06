# 审计日志API 404 问题修复指南

## 问题描述
在Linux服务器上部署后，访问审计日志API `/api/audit-logs` 返回404错误。

## 问题原因
数据库初始化脚本 `init_db.py` 未导入 `AuditLog` 模型，导致 `audit_logs` 表未被创建。

## 修复步骤

### 方案1: 重新部署（推荐）
如果服务器上的数据可以重置：

```bash
# 1. 更新代码
cd /opt/device-manager  # 或你的部署目录
git pull

# 2. 停止服务
sudo systemctl stop device-manager

# 3. 重新初始化数据库
source .venv/bin/activate
python3 init_db.py
deactivate

# 4. 启动服务
sudo systemctl start device-manager

# 5. 验证服务状态
sudo systemctl status device-manager
```

### 方案2: 手动创建表（保留现有数据）
如果需要保留现有数据：

```bash
# 1. 更新代码
cd /opt/device-manager  # 或你的部署目录
git pull

# 2. 停止服务
sudo systemctl stop device-manager

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 进入Python交互式环境
python3 << 'EOF'
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
db_path = os.path.join(os.path.dirname(__file__), CONFIG['database']['path'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 创建审计日志表
with app.app_context():
    db.create_all()
    print("✅ 审计日志表创建成功")
    
    # 验证表
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    if 'audit_logs' in tables:
        print("✅ audit_logs 表已存在")
    else:
        print("❌ audit_logs 表创建失败")
EOF

deactivate

# 5. 启动服务
sudo systemctl start device-manager

# 6. 验证
curl -s http://localhost:3001/api/audit-logs/action-types
```

### 方案3: 使用部署脚本（全新部署）
```bash
# 1. 下载最新代码到本地
git clone https://github.com/16to/device-manager.git
cd device-manager

# 2. 运行部署脚本
chmod +x deploy.sh
sudo ./deploy.sh

# 根据提示选择：
# - 覆盖部署（保留数据库）
# - 或清空重新部署（会删除所有数据）
```

## 验证修复

### 1. 检查数据库表
```bash
cd /opt/device-manager
source .venv/bin/activate
python3 << 'EOF'
import sys
sys.path.insert(0, 'backend')
from flask import Flask
from models import db
import json

with open('config.json', 'r') as f:
    CONFIG = json.load(f)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + CONFIG['database']['path']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"数据库表: {', '.join(tables)}")
    print(f"\naudit_logs表存在: {'audit_logs' in tables}")
EOF
deactivate
```

预期输出应包含：
```
数据库表: allowed_users, audit_logs, devices, usage_records, users
audit_logs表存在: True
```

### 2. 测试API接口
```bash
# 测试操作类型接口
curl -s http://localhost:3001/api/audit-logs/action-types | python3 -m json.tool

# 测试审计日志列表
curl -s "http://localhost:3001/api/audit-logs?page=1&per_page=10" | python3 -m json.tool
```

预期返回JSON数据，而非404错误。

### 3. 查看服务日志
```bash
# 查看实时日志
sudo journalctl -u device-manager -f

# 查看最近50条日志
sudo journalctl -u device-manager -n 50
```

正常日志应包含：
```
✅ 数据库表创建成功，当前存在的表: allowed_users, audit_logs, devices, usage_records, users
✅ 后台清理任务已启动（每24小时清理30天前的审计日志）
```

## 常见问题

### Q1: 执行 init_db.py 后仍然404
**A:** 检查服务是否重启
```bash
sudo systemctl restart device-manager
sudo systemctl status device-manager
```

### Q2: 表已存在但API仍然404
**A:** 检查路由是否正确注册
```bash
sudo journalctl -u device-manager | grep "audit-logs"
```

### Q3: systemd服务启动失败
**A:** 查看详细错误信息
```bash
sudo journalctl -u device-manager -n 100 --no-pager
```

常见原因：
- Python版本不兼容（需要 >= 3.8）
- 依赖包未安装
- 配置文件权限问题

## 技术细节

### 修复的文件
1. **init_db.py**
   - 添加 `AuditLog` 模型导入
   - 添加表创建验证逻辑
   
2. **backend/app.py**
   - 优化后台任务启动时机
   - 移到 `if __name__ == '__main__'` 块中

### 相关Commit
- feat: 添加审计日志功能和30天数据保留策略 (e9f94fc)
- fix: 修复Linux部署时审计日志API 404问题 (2d0e6b8)

## 联系支持
如果按以上步骤操作后仍有问题，请提供：
1. 操作系统信息：`cat /etc/os-release`
2. Python版本：`python3 --version`
3. 服务日志：`sudo journalctl -u device-manager -n 100`
4. 数据库表列表：执行上述"检查数据库表"脚本的输出
