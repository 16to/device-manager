#!/usr/bin/env python3
"""
数据库更新脚本：为 usage_records 表添加 login_info 字段
"""
import sqlite3
import os
import sys

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_root, 'backend', 'device_manager.db')

print(f"========== 数据库更新脚本 ==========")
print(f"数据库路径: {db_path}")
print(f"数据库存在: {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    print("❌ 数据库文件不存在，请先运行系统初始化数据库")
    sys.exit(1)

try:
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(usage_records)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'login_info' in columns:
        print("✅ login_info 字段已存在，无需更新")
    else:
        print("📝 正在添加 login_info 字段...")
        cursor.execute("ALTER TABLE usage_records ADD COLUMN login_info TEXT")
        conn.commit()
        print("✅ 成功添加 login_info 字段")
    
    # 验证更新
    cursor.execute("PRAGMA table_info(usage_records)")
    columns = cursor.fetchall()
    
    print("\n当前 usage_records 表结构:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    print("\n✅ 数据库更新完成！")
    
except Exception as e:
    print(f"❌ 数据库更新失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
