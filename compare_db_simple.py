#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比两个数据库结构差异"""

import sqlite3
import sys

def get_table_structure(db_path, table_name):
    """获取表结构"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        return {col[1]: col[2] for col in columns}
    except Exception as e:
        return None

def compare_databases():
    """对比两个数据库"""
    db1 = 'instance/contracts.db'
    db2 = 'instance/contracts1.db'

    print("="*70)
    print("Database Structure Comparison")
    print("="*70)
    print(f"DB1: {db1}")
    print(f"DB2: {db2}")
    print("="*70)

    # 检查关键表
    key_tables = ['tenant_customer', 'customer']

    for table in key_tables:
        print(f"\n{'='*70}")
        print(f"Table: {table}")
        print(f"{'='*70}")

        struct1 = get_table_structure(db1, table)
        struct2 = get_table_structure(db2, table)

        if struct1 is None or struct2 is None:
            print("  Table not found in one of the databases")
            continue

        fields1 = set(struct1.keys())
        fields2 = set(struct2.keys())

        only_in_db1 = fields1 - fields2
        only_in_db2 = fields2 - fields1

        print(f"\nDB1 has {len(fields1)} fields")
        print(f"DB2 has {len(fields2)} fields")

        if only_in_db1:
            print(f"\n[!] Only in DB1 ({len(only_in_db1)} fields):")
            for field in sorted(only_in_db1):
                print(f"    - {field} ({struct1[field]})")

        if only_in_db2:
            print(f"\n[!] Only in DB2 ({len(only_in_db2)} fields):")
            for field in sorted(only_in_db2):
                print(f"    + {field} ({struct2[field]})")

        if not only_in_db1 and not only_in_db2:
            print("\n[OK] Both databases have the same fields")

    # 检查代码期望
    print(f"\n{'='*70}")
    print("Code Expectation Check (models.py)")
    print(f"{'='*70}")

    print("\nTenantCustomer model expects these fields:")
    expected_fields = [
        'id', 'name', 'description', 'created_at',
        'system_name',      # System brand name
        'company_name',     # Company name
        'logo_file',        # Logo file
        'trial_expires_at'  # Trial expiration
    ]

    actual1 = get_table_structure(db1, 'tenant_customer')
    actual2 = get_table_structure(db2, 'tenant_customer')
    actual1_fields = set(actual1.keys()) if actual1 else set()
    actual2_fields = set(actual2.keys()) if actual2 else set()

    print(f"\nDB1 (contracts.db):")
    for field in expected_fields:
        status = "[OK]" if field in actual1_fields else "[MISSING]"
        print(f"  {status} {field}")

    print(f"\nDB2 (contracts1.db):")
    for field in expected_fields:
        status = "[OK]" if field in actual2_fields else "[MISSING]"
        print(f"  {status} {field}")

if __name__ == '__main__':
    compare_databases()
