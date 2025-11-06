#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
诊断脚本 - 检查审计日志功能是否正常
用于排查Linux服务器上的404问题
"""

import os
import sys
import json

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("审计日志功能诊断工具")
print("=" * 60)
print()

# 1. 检查配置文件
print("1. 检查配置文件...")
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
if os.path.exists(config_path):
    print(f"   ✅ 配置文件存在: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
    print(f"   ✅ 配置加载成功")
else:
    print(f"   ❌ 配置文件不存在: {config_path}")
    sys.exit(1)
print()

# 2. 检查数据库文件
print("2. 检查数据库文件...")
db_path = os.path.join(os.path.dirname(__file__), CONFIG['database']['path'])
if os.path.exists(db_path):
    print(f"   ✅ 数据库文件存在: {db_path}")
    file_size = os.path.getsize(db_path)
    print(f"   ✅ 数据库大小: {file_size} bytes")
else:
    print(f"   ❌ 数据库文件不存在: {db_path}")
    sys.exit(1)
print()

# 3. 检查模型导入
print("3. 检查模型导入...")
try:
    from models import db, Device, User, UsageRecord, AllowedUser, AuditLog
    print("   ✅ 所有模型导入成功")
    print(f"      - Device: {Device}")
    print(f"      - User: {User}")
    print(f"      - UsageRecord: {UsageRecord}")
    print(f"      - AllowedUser: {AllowedUser}")
    print(f"      - AuditLog: {AuditLog}")
except Exception as e:
    print(f"   ❌ 模型导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# 4. 检查数据库表
print("4. 检查数据库表...")
try:
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        
        print(f"   ✅ 数据库表列表: {', '.join(table_names)}")
        
        required_tables = ['devices', 'users', 'usage_records', 'allowed_users', 'audit_logs']
        missing_tables = [t for t in required_tables if t not in table_names]
        
        if missing_tables:
            print(f"   ❌ 缺少表: {', '.join(missing_tables)}")
            print()
            print("   解决方案: 运行以下命令重新创建表")
            print("   python3 init_db.py")
            sys.exit(1)
        else:
            print(f"   ✅ 所有必需的表都存在")
            
        # 检查 audit_logs 表结构
        if 'audit_logs' in table_names:
            columns = inspector.get_columns('audit_logs')
            print(f"   ✅ audit_logs 表字段:")
            for col in columns:
                print(f"      - {col['name']}: {col['type']}")
                
        # 检查审计日志数量
        try:
            count = AuditLog.query.count()
            print(f"   ✅ audit_logs 表记录数: {count}")
        except Exception as e:
            print(f"   ⚠️  无法查询记录数: {e}")
            
except Exception as e:
    print(f"   ❌ 数据库检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# 5. 检查Flask应用和路由
print("5. 检查Flask应用路由...")
try:
    # 重新导入app模块
    import importlib
    import app as app_module
    
    # 获取所有路由
    routes = []
    for rule in app_module.app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
            'path': str(rule)
        })
    
    # 检查审计日志相关路由
    audit_routes = [r for r in routes if 'audit' in r['path'].lower()]
    
    if audit_routes:
        print(f"   ✅ 找到 {len(audit_routes)} 个审计日志路由:")
        for route in audit_routes:
            print(f"      - {route['methods']:10s} {route['path']}")
    else:
        print(f"   ❌ 未找到审计日志路由")
        print()
        print("   所有API路由:")
        api_routes = [r for r in routes if r['path'].startswith('/api/')]
        for route in api_routes[:20]:  # 只显示前20个
            print(f"      - {route['methods']:10s} {route['path']}")
        
        if len(api_routes) > 20:
            print(f"      ... 还有 {len(api_routes) - 20} 个路由")
            
except Exception as e:
    print(f"   ❌ 路由检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# 6. 测试审计日志查询
print("6. 测试审计日志查询...")
try:
    with app.app_context():
        # 测试简单查询
        logs = AuditLog.query.limit(5).all()
        print(f"   ✅ 查询成功，返回 {len(logs)} 条记录")
        
        if logs:
            print(f"   ✅ 最新的审计日志:")
            for log in logs:
                print(f"      - [{log.created_at}] {log.action_type} by {log.operator}")
        else:
            print(f"   ℹ️  数据库中暂无审计日志")
            
except Exception as e:
    print(f"   ❌ 查询失败: {e}")
    import traceback
    traceback.print_exc()
print()

# 7. Python版本检查
print("7. Python环境信息...")
print(f"   Python版本: {sys.version}")
print(f"   Python路径: {sys.executable}")
print()

# 8. 依赖包版本
print("8. 关键依赖包版本...")
try:
    import flask
    print(f"   Flask: {flask.__version__}")
except:
    print(f"   Flask: 未安装")

try:
    import flask_sqlalchemy
    print(f"   Flask-SQLAlchemy: {flask_sqlalchemy.__version__}")
except:
    print(f"   Flask-SQLAlchemy: 未安装")

try:
    import sqlalchemy
    print(f"   SQLAlchemy: {sqlalchemy.__version__}")
except:
    print(f"   SQLAlchemy: 未安装")
print()

# 总结
print("=" * 60)
print("诊断完成！")
print("=" * 60)
print()
print("如果所有检查都通过，但API仍然404，请检查:")
print("1. 服务是否正确重启: sudo systemctl restart device-manager")
print("2. 查看服务日志: sudo journalctl -u device-manager -n 50")
print("3. 测试API: curl -v http://localhost:3001/api/audit-logs?page=1")
print("4. 检查防火墙和端口: netstat -tuln | grep 3001")
print()
