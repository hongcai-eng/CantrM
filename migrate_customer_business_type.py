"""
数据库迁移脚本：为 Customer 表添加 business_type 字段
此脚本会检查并添加缺失的字段，安全执行
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db
import sqlite3

def migrate():
    """执行数据库迁移"""
    # 获取数据库文件路径
    db_path = 'instance/contracts.db'

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        # 使用 sqlite3 直接操作数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查 customer 表是否存在 business_type 字段
        cursor.execute("PRAGMA table_info(customer)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'business_type' in columns:
            print("✓ customer.business_type 字段已存在，无需迁移")
        else:
            print("正在添加 customer.business_type 字段...")
            cursor.execute("ALTER TABLE customer ADD COLUMN business_type VARCHAR(20) DEFAULT '销售'")
            conn.commit()
            print("✓ customer.business_type 字段添加成功")

        conn.close()
        print("\n✅ 数据库迁移完成！")
        return True

    except Exception as e:
        print(f"❌ 迁移过程中出现错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("开始执行数据库迁移...")
    print("=" * 60)

    success = migrate()

    if success:
        print("\n" + "=" * 60)
        print("迁移成功！现在可以重启应用了。")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("迁移失败！请检查错误信息。")
        print("=" * 60)
        sys.exit(1)
