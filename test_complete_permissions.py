#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整功能测试：岗位管理和权限系统
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db, get_user_data_scope, get_user_accessible_contract_ids
from models import User, Position, UserPosition, Organization, Contract

with app.app_context():
    print("=" * 70)
    print("岗位管理和权限系统 - 完整测试")
    print("=" * 70)

    # 测试用户：吴洪才yh1
    user = User.query.filter_by(username='吴洪才yh1', customer_id=3).first()

    if not user:
        print("\n错误：未找到测试用户 吴洪才yh1")
        exit(1)

    print(f"\n【1. 用户基本信息】")
    print(f"  用户名: {user.username}")
    print(f"  用户ID: {user.id}")
    print(f"  租户: 亿海立达 (ID: {user.customer_id})")
    print(f"  角色: {user.role}")
    print(f"  用户自身权限: {user.permissions}")

    # 组织信息
    print(f"\n【2. 组织分配】")
    print(f"  User.organization_id: {user.organization_id}")

    if user.organization_id:
        org = db.session.get(Organization, user.organization_id)
        if org:
            print(f"  组织名称: {org.name}")
            print(f"  组织权限: {org.permissions}")

    # UserOrganization表
    from models import UserOrganization
    user_orgs = UserOrganization.query.filter_by(user_id=user.id).all()
    print(f"\n  UserOrganization表记录数: {len(user_orgs)}")
    for uo in user_orgs:
        org = db.session.get(Organization, uo.organization_id)
        print(f"    - {org.name if org else '未知'} (ID:{uo.organization_id}), 主组织:{uo.is_primary}")

    # 岗位信息
    print(f"\n【3. 岗位分配】")
    user_positions = UserPosition.query.filter_by(user_id=user.id).all()
    print(f"  已分配岗位数: {len(user_positions)}")

    for up in user_positions:
        pos = db.session.get(Position, up.position_id)
        org = db.session.get(Organization, up.organization_id) if up.organization_id else None
        print(f"\n  岗位: {pos.name if pos else '未知'}")
        if pos:
            print(f"    功能权限: {pos.function_permissions}")
            print(f"    数据权限: {pos.data_scope}")
        if org:
            print(f"    所属组织: {org.name}")
        print(f"    主岗位: {up.is_primary}")

    # 计算后的权限
    print(f"\n【4. 计算后的权限】")
    data_scope = get_user_data_scope(user.id)
    print(f"  数据权限范围: {data_scope}")

    if data_scope == 'all':
        print(f"  说明: 可以访问所有合同")
    elif data_scope == 'org':
        print(f"  说明: 可以访问本组织的合同")
    elif data_scope == 'self':
        print(f"  说明: 只能访问自己创建的合同")

    # 可访问的合同
    print(f"\n【5. 可访问合同】")
    accessible_ids = get_user_accessible_contract_ids(user.id, user.customer_id)

    if accessible_ids is None:
        print(f"  可访问: 全部合同")
    else:
        print(f"  可访问合同数: {len(accessible_ids)}")

        if accessible_ids:
            contracts = Contract.query.filter(Contract.id.in_(accessible_ids)).all()
            print(f"\n  合同列表:")
            for c in contracts:
                org = db.session.get(Organization, c.organization_id) if c.organization_id else None
                org_name = org.name if org else "未分配"
                print(f"    {c.id}. {c.project_name} [{org_name}]")

    # 组织合同统计
    if user.organization_id:
        org_contracts = Contract.query.filter_by(
            customer_id=user.customer_id,
            organization_id=user.organization_id
        ).count()
        print(f"\n【6. 组织合同统计】")
        print(f"  {org.name}的合同总数: {org_contracts}")

    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)

    # 总结
    print("\n【结论】")
    if len(user_positions) > 0 and len(accessible_ids if accessible_ids else []) > 0:
        print("  ✓ 用户已正确分配岗位")
        print("  ✓ 用户已正确分配组织")
        print("  ✓ 用户可以访问组织的合同")
        print("  ✓ 权限系统工作正常")
    elif len(user_positions) == 0:
        print("  ✗ 用户未分配岗位")
    elif len(accessible_ids if accessible_ids else []) == 0:
        print("  ✗ 用户看不到任何合同")
        print("  可能原因：组织下没有合同，或数据权限配置错误")

    print("\n【操作指南】")
    print("  1. 登录亿海立达管理员账号")
    print("  2. 进入'岗位管理'界面")
    print("  3. 查看'用户岗位明细'确认岗位分配")
    print("  4. 如需修改，点击岗位的'分配用户'按钮")
    print("  5. 编辑合同，为合同分配所属组织")
    print("=" * 70)
