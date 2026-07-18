#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库升级脚本 - 虚拟组织 + 虚拟岗位 + 岗位赋权
"""
from app import app, db
from models import Organization, Position, UserPosition, PositionContractPermission, UserOrganization

def upgrade():
    """升级数据库表结构"""
    with app.app_context():
        print("=" * 60)
        print("开始升级数据库：虚拟组织 + 虚拟岗位 + 岗位赋权")
        print("=" * 60)

        try:
            # 1. 为 Organization 表添加 is_virtual 字段
            print("\n[1] 检查 Organization 表的 is_virtual 字段...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            org_columns = [col['name'] for col in inspector.get_columns('organization')]

            if 'is_virtual' not in org_columns:
                print("   添加 is_virtual 字段...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE organization ADD COLUMN is_virtual BOOLEAN DEFAULT 0'))
                    conn.commit()
                print("   [OK] is_virtual 字段添加成功")
            else:
                print("   [OK] is_virtual 字段已存在")

            # 2. 创建新表
            print("\n[2] 创建新表...")
            db.create_all()
            print("   [OK] 所有表创建成功")

            # 3. 验证表是否创建成功
            print("\n[3] 验证表结构...")
            tables = inspector.get_table_names()

            required_tables = ['position', 'user_position', 'position_contract_permission', 'user_organization']
            for table_name in required_tables:
                if table_name in tables:
                    print(f"   [OK] {table_name} 表已创建")
                else:
                    print(f"   [X] {table_name} 表创建失败")

            print("\n" + "=" * 60)
            print("数据库升级完成！")
            print("=" * 60)
            print("\n新增功能：")
            print("1. 虚拟组织 - 支持跨部门临时项目组")
            print("2. 岗位模板 - 预定义岗位及其权限")
            print("3. 用户岗位 - 用户可担任多个岗位")
            print("4. 岗位赋权 - 为岗位指定可访问的合同")
            print("5. 多组织归属 - 用户可同时属于多个组织")

        except Exception as e:
            print(f"\n[ERROR] 升级失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    return True


if __name__ == '__main__':
    success = upgrade()
    if success:
        print("\n[OK] 升级成功！可以开始使用新功能。")
    else:
        print("\n[X] 升级失败，请检查错误信息。")
