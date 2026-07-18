#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复数据库缺失字段"""

import sqlite3
import sys

def fix_database(db_path='instance/contracts.db'):
    """添加缺失的字段"""
    print(f"正在修复数据库: {db_path}")
    print("="*60)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查并添加 tenant_customer 表的字段
        print("\n检查 tenant_customer 表...")
        cursor.execute("PRAGMA table_info(tenant_customer)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'system_name' not in columns:
            print("  添加字段: system_name")
            cursor.execute("ALTER TABLE tenant_customer ADD COLUMN system_name VARCHAR(200)")
            print("    [OK] 已添加 system_name")
        else:
            print("    [SKIP] system_name 已存在")

        if 'company_name' not in columns:
            print("  添加字段: company_name")
            cursor.execute("ALTER TABLE tenant_customer ADD COLUMN company_name VARCHAR(200)")
            print("    [OK] 已添加 company_name")
        else:
            print("    [SKIP] company_name 已存在")

        if 'logo_file' not in columns:
            print("  添加字段: logo_file")
            cursor.execute("ALTER TABLE tenant_customer ADD COLUMN logo_file VARCHAR(200)")
            print("    [OK] 已添加 logo_file")
        else:
            print("    [SKIP] logo_file 已存在")

        if 'trial_expires_at' not in columns:
            print("  添加字段: trial_expires_at")
            cursor.execute("ALTER TABLE tenant_customer ADD COLUMN trial_expires_at DATETIME")
            print("    [OK] 已添加 trial_expires_at")
        else:
            print("    [SKIP] trial_expires_at 已存在")

        # 检查并添加 customer 表的字段
        print("\n检查 customer 表...")
        cursor.execute("PRAGMA table_info(customer)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'business_type' not in columns:
            print("  添加字段: business_type")
            cursor.execute("ALTER TABLE customer ADD COLUMN business_type VARCHAR(20) DEFAULT '销售'")
            print("    [OK] 已添加 business_type")
        else:
            print("    [SKIP] business_type 已存在")

        conn.commit()
        conn.close()

        print("\n" + "="*60)
        print("修复完成！")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'instance/contracts.db'
    fix_database(db_path)
