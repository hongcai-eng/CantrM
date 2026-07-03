#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库结构"""

import sqlite3
import sys

def check_database(db_path):
    print(f"\n{'='*60}")
    print(f"检查数据库: {db_path}")
    print(f"{'='*60}\n")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"表列表 ({len(tables)}个):")
        for table in tables:
            print(f"  - {table[0]}")

        # 检查关键表的结构
        key_tables = ['tenant_customer', 'user', 'contract', 'customer', 'product', 'organization']

        for table_name in key_tables:
            print(f"\n{'-'*60}")
            print(f"表: {table_name}")
            print(f"{'-'*60}")
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                if columns:
                    print(f"字段 ({len(columns)}个):")
                    for col in columns:
                        # col: (cid, name, type, notnull, dflt_value, pk)
                        print(f"  {col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else 'NULL':10} {'PK' if col[5] else ''}")
                else:
                    print(f"  ⚠️  表不存在")
            except Exception as e:
                print(f"  ❌ 错误: {e}")

        conn.close()

    except Exception as e:
        print(f"❌ 无法打开数据库: {e}")
        return False

    return True

if __name__ == '__main__':
    # 检查当前数据库
    check_database('instance/contracts.db')

    # 检查备份数据库
    if len(sys.argv) > 1:
        check_database(sys.argv[1])
