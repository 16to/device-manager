#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建空的初始化数据库
"""

import os
import sys

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from models import db, User, Device, UsageRecord, AllowedUser, AuditLog
import json

# 读取配置
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except:
    CONFIG = {
        "admin": {"username": "admin", "password": "admin123"},
        "database": {"path": "backend/device_manager.db"}
    }

# 创建 Flask 应用
app = Flask(__name__)
db_path = os.path.join(os.path.dirname(__file__), CONFIG['database']['path'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

with app.app_context():
    print(f"\n{'='*60}")
    print(f"开始初始化数据库: {db_path}")
    print(f"{'='*60}\n")
    
    # 1. 删除旧数据库文件（包括可能的备份文件）
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ 已删除旧数据库: {db_path}")
    
    # 删除可能的临时文件
    for ext in ['-shm', '-wal', '-journal']:
        temp_file = db_path + ext
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"✅ 已删除临时文件: {temp_file}")
    
    print()
    
    # 2. 创建所有表
    print("正在创建数据库表...")
    db.create_all()
    print(f"✅ 数据库表创建完成")
    print()
    
    # 3. 验证表是否创建成功
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    
    print(f"当前数据库表: {', '.join(sorted(table_names))}")
    print()
    
    # 4. 检查必需的表
    required_tables = ['devices', 'users', 'usage_records', 'allowed_users', 'audit_logs']
    missing_tables = [t for t in required_tables if t not in table_names]
    
    if missing_tables:
        print(f"❌ 错误: 缺少以下表: {', '.join(missing_tables)}")
        print(f"   请检查 models.py 中的模型定义")
        sys.exit(1)
    else:
        print(f"✅ 所有必需的表已创建:")
        for table in sorted(required_tables):
            # 获取表的列信息
            columns = inspector.get_columns(table)
            column_names = [col['name'] for col in columns]
            print(f"   • {table}: {len(column_names)} 个字段 ({', '.join(column_names[:5])}{'...' if len(column_names) > 5 else ''})")
    
    print()
    
    # 5. 创建默认管理员
    print("正在创建管理员账号...")
    admin_username = CONFIG['admin']['username']
    admin_password = CONFIG['admin']['password']
    
    admin = User(username=admin_username, password=admin_password, is_admin=True)
    db.session.add(admin)
    db.session.commit()
    print(f"✅ 已创建管理员账号: {admin_username}")
    print()
    
    # 6. 验证数据
    user_count = User.query.count()
    print(f"✅ 数据验证: 用户表中有 {user_count} 个用户")
    
    print(f"\n{'='*60}")
    print(f"数据库初始化成功!")
    print(f"{'='*60}")
    print(f"\n数据库文件: {db_path}")
    print(f"管理员账号: {admin_username}")
    print(f"管理员密码: {admin_password}")
    print()
