"""
数据库迁移脚本：为 Customer 表添加 business_type 字段
纯 SQLite 实现，不依赖 Flask
"""
import sqlite3
import os
import sys

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def migrate():
    """执行数据库迁移"""
    # 获取数据库文件路径
    db_path = 'instance/contracts.db'

    if not os.path.exists(db_path):
        print(f"[ERROR] 数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("正在检查 customer 表结构...")

        # 检查 customer 表是否存在 business_type 字段
        cursor.execute("PRAGMA table_info(customer)")
        columns = [column[1] for column in cursor.fetchall()]

        print(f"当前字段列表: {', '.join(columns)}")

        if 'business_type' in columns:
            print("[OK] customer.business_type 字段已存在，无需迁移")
        else:
            print("\n正在添加 customer.business_type 字段...")
            cursor.execute("ALTER TABLE customer ADD COLUMN business_type VARCHAR(20) DEFAULT '销售'")
            conn.commit()
            print("[OK] customer.business_type 字段添加成功")

            # 验证字段是否添加成功
            cursor.execute("PRAGMA table_info(customer)")
            new_columns = [column[1] for column in cursor.fetchall()]
            if 'business_type' in new_columns:
                print("[OK] 字段验证成功")
            else:
                print("[ERROR] 字段验证失败")
                conn.close()
                return False

        conn.close()
        print("\n[SUCCESS] 数据库迁移完成！")
        return True

    except Exception as e:
        print(f"[ERROR] 迁移过程中出现错误: {e}")
        if 'conn' in locals():
            conn.close()
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
