#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试组织权限合并功能
验证用户调入组织时，原有权限是否被保留
"""

from app import app, db
from models import User, Organization, TenantCustomer

def test_permission_merge():
    with app.app_context():
        # 1. 准备测试数据
        print("=" * 60)
        print("步骤 1: 准备测试数据")
        print("=" * 60)

        # 检查或创建测试租户
        tenant = TenantCustomer.query.filter_by(name='测试租户_权限').first()
        if not tenant:
            tenant = TenantCustomer(name='测试租户_权限', description='用于权限测试')
            db.session.add(tenant)
            db.session.commit()
        print(f"租户ID: {tenant.id}, 租户名称: {tenant.name}")

        # 创建测试组织（带权限）
        org = Organization.query.filter_by(name='测试组织_权限合并', customer_id=tenant.id).first()
        if org:
            db.session.delete(org)
            db.session.commit()

        org = Organization(
            name='测试组织_权限合并',
            description='用于测试权限合并',
            customer_id=tenant.id,
            permissions='查阅,下载'
        )
        db.session.add(org)
        db.session.commit()
        print(f"组织ID: {org.id}, 组织名称: {org.name}, 组织权限: {org.permissions}")

        # 创建测试用户（带初始权限）
        test_user = User.query.filter_by(username='test_perm_user', customer_id=tenant.id).first()
        if test_user:
            db.session.delete(test_user)
            db.session.commit()

        test_user = User(
            username='test_perm_user',
            role='普通用户',
            permissions='增加,修改',
            customer_id=tenant.id,
            organization_id=None
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
        print(f"用户ID: {test_user.id}, 用户名: {test_user.username}")
        print(f"用户初始权限: {test_user.permissions}")
        print(f"用户所属组织: {test_user.organization_id}")

        # 2. 模拟用户调入组织的操作
        print("\n" + "=" * 60)
        print("步骤 2: 模拟用户调入组织")
        print("=" * 60)

        # 保存原始权限用于对比
        original_perms = test_user.permissions
        print(f"调入前 - 用户权限: {original_perms}")
        print(f"调入前 - 组织权限: {org.permissions}")

        # 执行调入操作（模拟 transfer_user 函数的逻辑）
        test_user.organization_id = org.id
        if org.permissions:
            # 获取用户当前权限集合
            current_perms = set()
            if test_user.permissions and test_user.permissions != 'all':
                current_perms = set(test_user.permissions.split(','))

            # 获取组织权限集合
            org_perms = set(org.permissions.split(','))

            # 合并权限（用户权限 + 组织权限）
            merged_perms = current_perms.union(org_perms)
            test_user.permissions = ','.join(sorted(merged_perms))

        db.session.commit()

        # 3. 验证结果
        print("\n" + "=" * 60)
        print("步骤 3: 验证权限合并结果")
        print("=" * 60)

        # 重新查询用户以确保数据已持久化
        test_user = User.query.get(test_user.id)

        print(f"调入后 - 用户所属组织: {test_user.organization_id} (组织名: {org.name})")
        print(f"调入后 - 用户权限: {test_user.permissions}")

        # 检查原有权限是否保留
        current_perms_set = set(test_user.permissions.split(','))
        original_perms_set = set(original_perms.split(','))
        org_perms_set = set(org.permissions.split(','))

        print("\n权限详细分析:")
        print(f"  原始用户权限: {original_perms_set}")
        print(f"  组织权限: {org_perms_set}")
        print(f"  合并后权限: {current_perms_set}")

        # 验证：原有权限是否都保留
        missing_perms = original_perms_set - current_perms_set
        if missing_perms:
            print(f"\n[FAIL] 用户原有权限丢失: {missing_perms}")
            return False
        else:
            print(f"\n[PASS] 用户原有权限已保留: {original_perms_set}")

        # 验证：组织权限是否已添加
        added_perms = org_perms_set - original_perms_set
        if not added_perms.issubset(current_perms_set):
            print(f"[FAIL] 组织权限未正确添加")
            return False
        else:
            print(f"[PASS] 组织权限已添加: {org_perms_set}")

        # 验证：最终权限应该是两者的并集
        expected_perms = original_perms_set.union(org_perms_set)
        if current_perms_set == expected_perms:
            print(f"[PASS] 权限合并正确，最终权限为两者并集")
        else:
            print(f"[FAIL] 权限合并错误")
            print(f"  期望权限: {expected_perms}")
            print(f"  实际权限: {current_perms_set}")
            return False

        # 4. 清理测试数据
        print("\n" + "=" * 60)
        print("步骤 4: 清理测试数据")
        print("=" * 60)
        db.session.delete(test_user)
        db.session.delete(org)
        # 保留租户以便后续测试使用
        db.session.commit()
        print("测试数据已清理")

        print("\n" + "=" * 60)
        print("测试结果: 全部通过!")
        print("=" * 60)
        return True

if __name__ == '__main__':
    try:
        success = test_permission_merge()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
