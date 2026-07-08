#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量修复：确保所有分配了岗位的用户都有正确的组织关联
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from models import User, UserPosition, UserOrganization

with app.app_context():
    print("=" * 70)
    print("批量修复用户组织关联")
    print("=" * 70)

    # 查找所有用户
    users = User.query.all()

    fixed_count = 0
    skipped_count = 0

    for user in users:
        # 跳过superadmin
        if user.username == 'superadmin' or user.customer_id is None:
            continue

        # 查找用户的岗位分配
        user_positions = UserPosition.query.filter_by(user_id=user.id).all()

        if not user_positions:
            # 没有岗位分配，跳过
            skipped_count += 1
            continue

        # 找到主岗位的组织
        primary_org_id = None
        for up in user_positions:
            if up.is_primary and up.organization_id:
                primary_org_id = up.organization_id
                break

        # 如果没有主岗位，取第一个有组织的岗位
        if not primary_org_id:
            for up in user_positions:
                if up.organization_id:
                    primary_org_id = up.organization_id
                    break

        if not primary_org_id:
            print(f"⚠ {user.username}: 有岗位但都没有指定组织")
            continue

        # 检查是否需要修复
        needs_fix = False

        # 检查 User.organization_id
        if user.organization_id != primary_org_id:
            needs_fix = True

        # 检查 UserOrganization 记录
        user_org = UserOrganization.query.filter_by(
            user_id=user.id,
            organization_id=primary_org_id
        ).first()

        if not user_org:
            needs_fix = True

        if needs_fix:
            print(f"修复: {user.username} (ID:{user.id})")

            # 设置 User.organization_id
            user.organization_id = primary_org_id

            # 添加 UserOrganization 记录
            if not user_org:
                # 先取消之前的主组织
                UserOrganization.query.filter_by(
                    user_id=user.id,
                    is_primary=True
                ).update({'is_primary': False})

                user_org = UserOrganization(
                    user_id=user.id,
                    organization_id=primary_org_id,
                    is_primary=True
                )
                db.session.add(user_org)

            fixed_count += 1

    # 提交所有修改
    if fixed_count > 0:
        db.session.commit()
        print(f"\n✓ 共修复 {fixed_count} 个用户的组织关联")
    else:
        print(f"\n✓ 所有用户的组织关联都正确")

    print(f"跳过 {skipped_count} 个没有岗位的用户")

    print("\n" + "=" * 70)
    print("修复完成！")
    print("=" * 70)
