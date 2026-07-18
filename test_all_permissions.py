#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全面测试：岗位管理和权限系统
测试用户：吴洪才yh1、吴洪才yh2
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db, get_user_data_scope, get_user_accessible_contract_ids
from models import User, Position, UserPosition, Organization, Contract

with app.app_context():
    print("=" * 70)
    print("全面测试：岗位管理和权限系统")
    print("=" * 70)

    # 测试两个用户
    test_users = ['吴洪才yh1', '吴洪才yh2']

    for username in test_users:
        user = User.query.filter_by(username=username, customer_id=3).first()

        if not user:
            print(f"\n✗ 未找到用户: {username}")
            continue

        print(f"\n{'=' * 70}")
        print(f"用户: {username}")
        print(f"{'=' * 70}")

        # 基本信息
        print(f"\n【基本信息】")
        print(f"  用户ID: {user.id}")
        print(f"  角色: {user.role}")
        print(f"  User.organization_id: {user.organization_id}")

        # 组织信息
        if user.organization_id:
            org = db.session.get(Organization, user.organization_id)
            if org:
                print(f"  组织名称: {org.name}")

        # UserOrganization
        from models import UserOrganization
        user_orgs = UserOrganization.query.filter_by(user_id=user.id).all()
        print(f"\n【UserOrganization表】")
        if user_orgs:
            for uo in user_orgs:
                org = db.session.get(Organization, uo.organization_id)
                print(f"  ✓ {org.name if org else '未知'} (主:{uo.is_primary})")
        else:
            print(f"  ✗ 没有记录")

        # 岗位分配
        user_positions = UserPosition.query.filter_by(user_id=user.id).all()
        print(f"\n【岗位分配】")
        print(f"  岗位数: {len(user_positions)}")
        for up in user_positions:
            pos = db.session.get(Position, up.position_id)
            org = db.session.get(Organization, up.organization_id) if up.organization_id else None
            if pos:
                print(f"  - {pos.name} (数据权限:{pos.data_scope})")
                if org:
                    print(f"    组织: {org.name}")
                print(f"    主岗位: {up.is_primary}")

        # 数据权限
        data_scope = get_user_data_scope(user.id)
        print(f"\n【数据权限】")
        print(f"  范围: {data_scope}")

        # 可访问合同
        accessible_ids = get_user_accessible_contract_ids(user.id, user.customer_id)
        if accessible_ids is None:
            print(f"  可访问: 全部合同")
        else:
            print(f"  可访问合同数: {len(accessible_ids)}")

            if len(accessible_ids) > 0:
                contracts = Contract.query.filter(Contract.id.in_(accessible_ids)).limit(3).all()
                print(f"  合同示例:")
                for c in contracts:
                    print(f"    - {c.project_name}")

        # 结论
        print(f"\n【结论】")
        has_position = len(user_positions) > 0
        has_org = len(user_orgs) > 0
        can_access = len(accessible_ids) > 0 if accessible_ids else True

        if has_position and has_org and can_access:
            print(f"  ✓ 配置正常，权限系统工作正常")
        else:
            if not has_position:
                print(f"  ✗ 未分配岗位")
            if not has_org:
                print(f"  ✗ 缺少组织关联 (UserOrganization)")
            if not can_access:
                print(f"  ✗ 无法访问合同")

    # 岗位人员统计
    print(f"\n{'=' * 70}")
    print(f"【岗位人员统计】")
    print(f"{'=' * 70}")

    positions = Position.query.filter_by(customer_id=3).all()
    for pos in positions:
        count = UserPosition.query.filter_by(position_id=pos.id).count()
        print(f"  {pos.name}: {count} 人")

    print(f"\n{'=' * 70}")
    print(f"测试完成！")
    print(f"{'=' * 70}")
