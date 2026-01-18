#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库自动迁移脚本
- 自动检测表结构差异
- 添加缺失的表和字段
- 保留所有现有数据
- 不删除任何表或字段
"""

import os
import sys
import json
from datetime import datetime

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from models import db, User, Device, UsageRecord, AllowedUser, AuditLog
from sqlalchemy import inspect, text

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

def print_header(text):
    """打印标题"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def print_section(text):
    """打印章节"""
    print(f"\n--- {text} ---")

def get_model_columns(model):
    """获取模型定义的所有字段"""
    columns = {}
    for column in model.__table__.columns:
        col_type = str(column.type)
        columns[column.name] = {
            'type': col_type,
            'nullable': column.nullable,
            'primary_key': column.primary_key,
            'unique': column.unique if hasattr(column, 'unique') else False,
            'default': str(column.default.arg) if column.default is not None else None
        }
    return columns

def get_db_columns(inspector, table_name):
    """获取数据库中表的所有字段"""
    columns = {}
    try:
        for column in inspector.get_columns(table_name):
            columns[column['name']] = {
                'type': str(column['type']),
                'nullable': column['nullable'],
                'primary_key': column.get('primary_key', False),
                'default': column.get('default', None)
            }
    except:
        pass
    return columns

def add_column_to_table(table_name, column_name, column_info):
    """添加字段到表"""
    # 构建字段定义
    col_type = column_info['type']
    nullable = 'NULL' if column_info['nullable'] else 'NOT NULL'
    
    # SQLite 的 ALTER TABLE 只支持简单的 ADD COLUMN
    # 不能添加 NOT NULL 约束（除非有 DEFAULT），也不能添加主键
    if not column_info['nullable'] and column_info['default'] is None:
        # 如果是 NOT NULL 但没有默认值，使用合理的默认值
        if 'INTEGER' in col_type.upper():
            default_value = '0'
        elif 'BOOLEAN' in col_type.upper():
            default_value = '0'
        else:
            default_value = "''"
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type} NOT NULL DEFAULT {default_value}"
    else:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type}"
    
    try:
        with db.engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)

with app.app_context():
    print_header("数据库自动迁移工具")
    print(f"数据库路径: {db_path}")
    print(f"数据库存在: {os.path.exists(db_path)}")
    
    # 定义所有模型
    models = {
        'users': User,
        'devices': Device,
        'usage_records': UsageRecord,
        'allowed_users': AllowedUser,
        'audit_logs': AuditLog
    }
    
    # 检查数据库是否存在
    db_exists = os.path.exists(db_path)
    
    if not db_exists:
        print_section("数据库不存在，创建新数据库")
        db.create_all()
        
        # 创建默认管理员
        admin_username = CONFIG['admin']['username']
        admin_password = CONFIG['admin']['password']
        admin = User(username=admin_username, password=admin_password, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ 已创建新数据库")
        print(f"✅ 已创建所有表: {', '.join(models.keys())}")
        print(f"✅ 已创建管理员账号: {admin_username}")
        
    else:
        print_section("数据库已存在，检查表结构")
        
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print(f"现有表 ({len(existing_tables)}): {', '.join(sorted(existing_tables))}")
        
        # 统计信息
        total_tables_added = 0
        total_columns_added = 0
        total_tables_checked = 0
        errors = []
        
        # 检查每个模型
        for table_name, model in models.items():
            print_section(f"检查表: {table_name}")
            total_tables_checked += 1
            
            if table_name not in existing_tables:
                # 表不存在，创建表
                print(f"  ⚠️  表不存在，正在创建...")
                try:
                    model.__table__.create(db.engine)
                    total_tables_added += 1
                    print(f"  ✅ 已创建表: {table_name}")
                except Exception as e:
                    error_msg = f"创建表 {table_name} 失败: {e}"
                    errors.append(error_msg)
                    print(f"  ❌ {error_msg}")
                continue
            
            # 表存在，检查字段
            model_columns = get_model_columns(model)
            db_columns = get_db_columns(inspector, table_name)
            
            print(f"  模型定义字段: {len(model_columns)}")
            print(f"  数据库现有字段: {len(db_columns)}")
            
            # 找出缺失的字段
            missing_columns = set(model_columns.keys()) - set(db_columns.keys())
            
            if missing_columns:
                print(f"  ⚠️  发现 {len(missing_columns)} 个缺失字段: {', '.join(sorted(missing_columns))}")
                
                for col_name in sorted(missing_columns):
                    col_info = model_columns[col_name]
                    print(f"    正在添加字段: {col_name} ({col_info['type']})")
                    
                    success, error = add_column_to_table(table_name, col_name, col_info)
                    if success:
                        total_columns_added += 1
                        print(f"    ✅ 已添加字段: {col_name}")
                    else:
                        error_msg = f"添加字段 {table_name}.{col_name} 失败: {error}"
                        errors.append(error_msg)
                        print(f"    ❌ {error_msg}")
            else:
                print(f"  ✅ 表结构完整，无需更新")
        
        # 显示汇总
        print_header("迁移汇总")
        print(f"检查的表数量: {total_tables_checked}")
        print(f"新创建的表: {total_tables_added}")
        print(f"新添加的字段: {total_columns_added}")
        
        if errors:
            print(f"\n⚠️  发现 {len(errors)} 个错误:")
            for error in errors:
                print(f"  - {error}")
        
        if total_tables_added > 0 or total_columns_added > 0:
            print(f"\n✅ 数据库已成功升级到最新版本！")
        else:
            print(f"\n✅ 数据库结构已是最新，无需升级")
    
    # 验证表结构
    print_section("验证数据库表结构")
    inspector = inspect(db.engine)
    
    for table_name in sorted(models.keys()):
        if table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            print(f"  ✅ {table_name}: {len(columns)} 个字段")
    
    # 显示数据统计
    print_section("数据库统计")
    try:
        user_count = User.query.count()
        device_count = Device.query.count()
        record_count = UsageRecord.query.count()
        allowed_count = AllowedUser.query.count()
        log_count = AuditLog.query.count()
        
        print(f"  用户数量: {user_count}")
        print(f"  设备数量: {device_count}")
        print(f"  使用记录: {record_count}")
        print(f"  授权用户: {allowed_count}")
        print(f"  审计日志: {log_count}")
    except Exception as e:
        print(f"  ⚠️  无法获取统计信息: {e}")
    
    # 确保有管理员账号
    print_section("检查管理员账号")
    admin_count = User.query.filter_by(is_admin=True).count()
    if admin_count == 0:
        print(f"  ⚠️  未找到管理员账号，正在创建...")
        admin_username = CONFIG['admin']['username']
        admin_password = CONFIG['admin']['password']
        admin = User(username=admin_username, password=admin_password, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print(f"  ✅ 已创建管理员账号: {admin_username}")
    else:
        print(f"  ✅ 已有 {admin_count} 个管理员账号")
    
    print_header("迁移完成")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
