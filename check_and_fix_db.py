#!/usr/bin/env python3
"""
数据库检查和修复脚本
检查数据库是否包含所有必需的字段，并自动修复缺失的字段
"""
import sqlite3
import os
import sys

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_root, 'backend', 'device_manager.db')

print(f"{'='*60}")
print(f"数据库检查和修复脚本")
print(f"{'='*60}")
print(f"数据库路径: {db_path}")
print(f"数据库存在: {os.path.exists(db_path)}")
print()

if not os.path.exists(db_path):
    print("❌ 数据库文件不存在")
    print("   请先运行系统初始化数据库或启动应用程序")
    sys.exit(1)

try:
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"✅ 数据库包含 {len(tables)} 个表:")
    for table in tables:
        print(f"   • {table[0]}")
    print()
    
    # 检查 usage_records 表的字段
    print("检查 usage_records 表结构...")
    cursor.execute("PRAGMA table_info(usage_records)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    print(f"当前字段 ({len(column_names)}):")
    for col in columns:
        print(f"   • {col[1]} ({col[2]}){' - NOT NULL' if col[3] else ''}")
    print()
    
    # 需要的字段列表
    required_fields = {
        'login_info': ('TEXT', '登录信息字段（用于存储Linux登录信息）')
    }
    
    # 检查缺失的字段
    missing_fields = []
    for field_name, (field_type, description) in required_fields.items():
        if field_name not in column_names:
            missing_fields.append((field_name, field_type, description))
    
    if missing_fields:
        print(f"⚠️  发现 {len(missing_fields)} 个缺失的字段:")
        for field_name, field_type, description in missing_fields:
            print(f"   • {field_name} ({field_type}) - {description}")
        print()
        
        print("正在自动修复...")
        for field_name, field_type, description in missing_fields:
            try:
                cursor.execute(f"ALTER TABLE usage_records ADD COLUMN {field_name} {field_type}")
                conn.commit()
                print(f"✅ 已添加字段: {field_name}")
            except Exception as e:
                print(f"❌ 添加字段失败 {field_name}: {e}")
        print()
        
        # 再次验证
        cursor.execute("PRAGMA table_info(usage_records)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        print("修复后的表结构:")
        for col in columns:
            print(f"   • {col[1]} ({col[2]}){' - NOT NULL' if col[3] else ''}")
        print()
        
        # 检查是否所有字段都已添加
        still_missing = [f for f, _, _ in missing_fields if f not in column_names]
        if still_missing:
            print(f"❌ 以下字段仍然缺失: {', '.join(still_missing)}")
            sys.exit(1)
        else:
            print("✅ 所有缺失的字段已成功添加！")
    else:
        print("✅ 数据库结构完整，无需修复")
    
    # 显示统计信息
    print()
    print("数据库统计信息:")
    
    cursor.execute("SELECT COUNT(*) FROM devices")
    device_count = cursor.fetchone()[0]
    print(f"   • 设备数量: {device_count}")
    
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"   • 用户数量: {user_count}")
    
    cursor.execute("SELECT COUNT(*) FROM usage_records")
    record_count = cursor.fetchone()[0]
    print(f"   • 使用记录: {record_count}")
    
    cursor.execute("SELECT COUNT(*) FROM allowed_users")
    allowed_count = cursor.fetchone()[0]
    print(f"   • 授权用户: {allowed_count}")
    
    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    log_count = cursor.fetchone()[0]
    print(f"   • 审计日志: {log_count}")
    
    conn.close()
    
    print()
    print(f"{'='*60}")
    print(f"数据库检查完成！")
    print(f"{'='*60}")
    
except Exception as e:
    print(f"❌ 数据库操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
