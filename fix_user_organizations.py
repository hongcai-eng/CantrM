#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复用户组织关联数据
解决用户看不到组织合同的问题
"""

from app import app, db
from models import User, UserPosition, UserOrganization

def fix_user_organizations():
    with app.app_context():
        print("=" * 60)
        print("开始修复用户组织关联数据")
        print("=" * 60)

        fixed_count = 0
        created_count = 0

        # 1. 修复 UserPosition 表
        print("\n【步骤1】修复 UserPosition.organization_id")
        user_positions = UserPosition.query.filter_by(organization_id=None).all()
        print(f"找到 {len(user_positions)} 条 organization_id 为 None 的记录")

        for up in user_positions:
            user = db.session.get(User, up.user_id)
            if user and user.organization_id:
                up.organization_id = user.organization_id
                fixed_count += 1
                print(f"  修复: 用户 {user.username} 的岗位，组织ID设为 {user.organization_id}")

        if fixed_count > 0:
            db.session.commit()
            print(f"已修复 {fixed_count} 条记录")
        else:
            print("  无需修复")

        # 2. 创建 UserOrganization 记录
        print("\n【步骤2】创建 UserOrganization 记录")
        users = User.query.filter(
            User.organization_id.isnot(None),
            User.role != '超级管理员'
        ).all()

        for user in users:
            # 检查是否已存在
            existing = UserOrganization.query.filter_by(
                user_id=user.id,
                organization_id=user.organization_id
            ).first()

            if not existing:
                # 创建新记录
                user_org = UserOrganization(
                    user_id=user.id,
                    organization_id=user.organization_id,
                    is_primary=True
                )
                db.session.add(user_org)
                created_count += 1
                print(f"  创建: 用户 {user.username} -> 组织ID {user.organization_id}, is_primary=True")
            else:
                # 确保 is_primary 为 True
                if not existing.is_primary:
                    existing.is_primary = True
                    print(f"  更新: 用户 {user.username} 的主组织标记")

        if created_count > 0:
            db.session.commit()
            print(f"已创建 {created_count} 条记录")
        else:
            print("  无需创建")

        # 3. 验证结果
        print("\n【步骤3】验证修复结果")
        print("-" * 60)

        # 检查还有多少 UserPosition.organization_id 为 None
        remaining = UserPosition.query.filter_by(organization_id=None).count()
        print(f"剩余 organization_id 为 None 的 UserPosition: {remaining} 条")

        # 检查每个用户的 UserOrganization 记录
        users_without_org = []
        for user in User.query.filter(User.role != '超级管理员').all():
            user_orgs = UserOrganization.query.filter_by(user_id=user.id).count()
            if user_orgs == 0 and user.organization_id:
                users_without_org.append(user.username)

        if users_without_org:
            print(f"警告: 以下用户仍然没有 UserOrganization 记录: {', '.join(users_without_org)}")
        else:
            print("OK: 所有用户都有 UserOrganization 记录")

        print("\n" + "=" * 60)
        print("修复完成！")
        print("=" * 60)
        print(f"\n总结:")
        print(f"  - 修复的 UserPosition 记录: {fixed_count} 条")
        print(f"  - 创建的 UserOrganization 记录: {created_count} 条")
        print(f"\n请让用户刷新页面，查看是否能正常访问组织合同。")

if __name__ == '__main__':
    fix_user_organizations()
