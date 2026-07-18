#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比两个数据库结构差异"""

import sqlite3

def get_table_structure(db_path, table_name):
    """获取表结构"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        return {col[1]: col[2] for col in columns}  # {字段名: 类型}
    except Exception as e:
        return None

def compare_databases():
    """对比两个数据库"""
    db1 = 'instance/contracts.db'
    db2 = 'instance/contracts1.db'

    print("="*70)
    print("数据库结构对比")
    print("="*70)
    print(f"数据库1: {db1}")
    print(f"数据库2: {db2}")
    print("="*70)

    # 需要检查的关键表
    key_tables = ['tenant_customer', 'user', 'contract', 'organization', 'sys_config']

    for table in key_tables:
        print(f"\n{'='*70}")
        print(f"表: {table}")
        print(f"{'='*70}")

        struct1 = get_table_structure(db1, table)
        struct2 = get_table_structure(db2, table)

        if struct1 is None and struct2 is None:
            print("  ⚠️  两个数据库都不存在此表")
            continue
        elif struct1 is None:
            print(f"  ❌ {db1} 不存在此表")
            continue
        elif struct2 is None:
            print(f"  ❌ {db2} 不存在此表")
            continue

        # 找出差异字段
        fields1 = set(struct1.keys())
        fields2 = set(struct2.keys())

        only_in_db1 = fields1 - fields2
        only_in_db2 = fields2 - fields1
        common = fields1 & fields2

        print(f"\n共同字段 ({len(common)}个):")
        for field in sorted(common):
            print(f"  ✓ {field:25} {struct1[field]}")

        if only_in_db1:
            print(f"\n⚠️  仅在 {db1} 中存在 ({len(only_in_db1)}个):")
            for field in sorted(only_in_db1):
                print(f"  + {field:25} {struct1[field]}")

        if only_in_db2:
            print(f"\n⚠️  仅在 {db2} 中存在 ({len(only_in_db2)}个):")
            for field in sorted(only_in_db2):
                print(f"  - {field:25} {struct2[field]}")

    # 检查代码期望的字段
    print(f"\n{'='*70}")
    print("检查代码期望 vs 实际数据库")
    print(f"{'='*70}")

    print("\n根据 models.py，tenant_customer 表应该包含:")
    expected_fields = [
        'id', 'name', 'description', 'created_at',
        'system_name',  # 品牌名称
        'company_name',  # 公司名称
        'logo_file',  # Logo文件
        'trial_expires_at'  # 试用期
    ]

    actual = get_table_structure(db1, 'tenant_customer')
    actual_fields = set(actual.keys()) if actual else set()

    for field in expected_fields:
        if field in actual_fields:
            print(f"  ✓ {field}")
        else:
            print(f"  ❌ 缺失: {field}")

if __name__ == '__main__':
    compare_databases()
