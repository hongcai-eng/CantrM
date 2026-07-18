#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库升级脚本 - 自动检测并添加缺失的字段
用于兼容旧版本数据库

使用方法：
1. 将旧的 contracts.db 替换到 instance/ 目录
2. 运行: python upgrade_db.py
3. 重启应用
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app, db
from sqlalchemy import inspect, text

def upgrade_database():
    """检测并添加缺失的字段"""
    with app.app_context():
        inspector = inspect(db.engine)

        # 检查 tenant_customer 表的字段
        if 'tenant_customer' in inspector.get_table_names():
            print('\n检查 tenant_customer 表...')
            columns = [col['name'] for col in inspector.get_columns('tenant_customer')]

            # 添加缺失的 system_name 字段
            if 'system_name' not in columns:
                print('  正在添加 system_name 字段...')
                try:
                    db.session.execute(text(
                        'ALTER TABLE tenant_customer ADD COLUMN system_name VARCHAR(200)'
                    ))
                    db.session.commit()
                    print('  [OK] system_name 字段添加成功')
                except Exception as e:
                    print(f'  [ERROR] 添加 system_name 字段失败: {e}')
                    db.session.rollback()
            else:
                print('  [OK] system_name 字段已存在')

            # 添加缺失的 company_name 字段
            if 'company_name' not in columns:
                print('  正在添加 company_name 字段...')
                try:
                    db.session.execute(text(
                        'ALTER TABLE tenant_customer ADD COLUMN company_name VARCHAR(200)'
                    ))
                    db.session.commit()
                    print('  [OK] company_name 字段添加成功')
                except Exception as e:
                    print(f'  [ERROR] 添加 company_name 字段失败: {e}')
                    db.session.rollback()
            else:
                print('  [OK] company_name 字段已存在')

            # 添加缺失的 logo_file 字段
            if 'logo_file' not in columns:
                print('  正在添加 logo_file 字段...')
                try:
                    db.session.execute(text(
                        'ALTER TABLE tenant_customer ADD COLUMN logo_file VARCHAR(200)'
                    ))
                    db.session.commit()
                    print('  [OK] logo_file 字段添加成功')
                except Exception as e:
                    print(f'  [ERROR] 添加 logo_file 字段失败: {e}')
                    db.session.rollback()
            else:
                print('  [OK] logo_file 字段已存在')

            # 添加缺失的 trial_expires_at 字段
            if 'trial_expires_at' not in columns:
                print('  正在添加 trial_expires_at 字段...')
                try:
                    db.session.execute(text(
                        'ALTER TABLE tenant_customer ADD COLUMN trial_expires_at DATETIME'
                    ))
                    db.session.commit()
                    print('  [OK] trial_expires_at 字段添加成功')
                except Exception as e:
                    print(f'  [ERROR] 添加 trial_expires_at 字段失败: {e}')
                    db.session.rollback()
            else:
                print('  [OK] trial_expires_at 字段已存在')

        # 检查 contract 表
        if 'contract' in inspector.get_table_names():
            print('\n检查 contract 表...')
            columns = [col['name'] for col in inspector.get_columns('contract')]

            if 'business_type' not in columns:
                print('  正在添加 business_type 字段...')
                try:
                    db.session.execute(text(
                        "ALTER TABLE contract ADD COLUMN business_type VARCHAR(20) DEFAULT '销售'"
                    ))
                    db.session.commit()
                    print('  [OK] business_type 字段添加成功')
                except Exception as e:
                    print(f'  [ERROR] 添加 business_type 字段失败: {e}')
                    db.session.rollback()
            else:
                print('  [OK] business_type 字段已存在')

        # 检查 customer 表
        if 'customer' in inspector.get_table_names():
            print('\n检查 customer 表...')
            columns = [col['name'] for col in inspector.get_columns('customer')]

            if 'business_type' not in columns:
                print('  正在添加 business_type 字段...')
                try:
                    db.session.execute(text(
                        "ALTER TABLE customer ADD COLUMN business_type VARCHAR(20) DEFAULT '销售'"
                    ))
                    db.session.commit()
                    print('  [OK] business_type 字段添加成功')
                except Exception as e:
                    print(f'  [ERROR] 添加 customer.business_type 字段失败: {e}')
                    db.session.rollback()
            else:
                print('  [OK] business_type 字段已存在')

        print('\n数据库升级完成！')

if __name__ == '__main__':
    print('开始检测数据库...\n')
    upgrade_database()
