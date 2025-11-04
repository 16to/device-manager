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
from models import db, User
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
    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除旧数据库: {db_path}")
    
    # 创建所有表
    db.create_all()
    print(f"✅ 已创建数据库表")
    
    # 创建默认管理员
    admin_username = CONFIG['admin']['username']
    admin_password = CONFIG['admin']['password']
    
    admin = User(username=admin_username, password=admin_password, is_admin=True)
    db.session.add(admin)
    db.session.commit()
    print(f"✅ 已创建管理员账号: {admin_username}")
    
    print(f"\n数据库初始化完成: {db_path}")
