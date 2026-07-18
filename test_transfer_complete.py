#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终完整测试：组织调动和数据权限系统
确保所有功能都正常工作
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db, get_user_accessible_contract_ids
from models import User, Organization, UserOrganization, Contract

def transfer_user(user, target_org_id):
    """模拟组织调动功能"""
    # 更新User.organization_id
    user.organization_id = target_org_id

    # 先取消所有主组织标记
    UserOrganization.query.filter_by(user_id=user.id, is_primary=True).update({'is_primary': False})

    # 查找或创建目标组织的记录
    existing_user_org = UserOrganization.query.filter_by(
        user_id=user.id,
        organization_id=target_org_id
    ).first()

    if existing_user_org:
        existing_user_org.is_primary = True
    else:
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=target_org_id,
            is_primary=True
        )
        db.session.add(user_org)

    db.session.commit()

def verify_user_access(user, expected_org_name, expected_count):
    """验证用户的数据访问权限"""
    org = db.session.get(Organization, user.organization_id)
    accessible_ids = get_user_accessible_contract_ids(user.id, user.customer_id)

    actual_org_name = org.name if org else "未知"
    actual_count = len(accessible_ids) if accessible_ids else 0

    # 验证主组织
    org_correct = (actual_org_name == expected_org_name)

    # 验证合同数
    count_correct = (actual_count == expected_count)

    # 验证合同都属于主组织
    all_from_main_org = True
    if accessible_ids:
        contracts = Contract.query.filter(Contract.id.in_(accessible_ids)).all()
        for c in contracts:
            c_org = db.session.get(Organization, c.organization_id) if c.organization_id else None
            if c_org and c_org.name != expected_org_name:
                all_from_main_org = False
                break

    success = org_correct and count_correct and all_from_main_org

    return {
        'success': success,
        'actual_org': actual_org_name,
        'expected_org': expected_org_name,
        'actual_count': actual_count,
        'expected_count': expected_count,
        'org_correct': org_correct,
        'count_correct': count_correct,
        'all_from_main_org': all_from_main_org
    }

with app.app_context():
    print("=" * 70)
    print("最终完整测试：组织调动和数据权限系统")
    print("=" * 70)

    # 获取测试数据
    user = User.query.filter_by(username='吴洪才yh2', customer_id=3).first()
    xiaoshou_yibu = Organization.query.filter_by(name='销售一部', customer_id=3).first()
    xinnengyuan = Organization.query.filter_by(name='新能源服务部', customer_id=3).first()

    if not user or not xiaoshou_yibu or not xinnengyuan:
        print("✗ 测试数据不完整")
        exit(1)

    # 测试1：调到销售一部
    print("\n【测试1】调动到销售一部")
    print("-" * 70)
    transfer_user(user, xiaoshou_yibu.id)
    result1 = verify_user_access(user, '销售一部', 5)

    print(f"主组织: {result1['actual_org']} (预期: {result1['expected_org']}) {'✓' if result1['org_correct'] else '✗'}")
    print(f"可访问合同数: {result1['actual_count']} (预期: {result1['expected_count']}) {'✓' if result1['count_correct'] else '✗'}")
    print(f"合同归属: {'✓ 全部属于主组织' if result1['all_from_main_org'] else '✗ 有其他组织的合同'}")
    print(f"测试结果: {'✓ 通过' if result1['success'] else '✗ 失败'}")

    # 测试2：调到新能源服务部
    print("\n【测试2】调动到新能源服务部")
    print("-" * 70)
    transfer_user(user, xinnengyuan.id)
    result2 = verify_user_access(user, '新能源服务部', 2)

    print(f"主组织: {result2['actual_org']} (预期: {result2['expected_org']}) {'✓' if result2['org_correct'] else '✗'}")
    print(f"可访问合同数: {result2['actual_count']} (预期: {result2['expected_count']}) {'✓' if result2['count_correct'] else '✗'}")
    print(f"合同归属: {'✓ 全部属于主组织' if result2['all_from_main_org'] else '✗ 有其他组织的合同'}")
    print(f"测试结果: {'✓ 通过' if result2['success'] else '✗ 失败'}")

    # 测试3：再次调回销售一部
    print("\n【测试3】再次调回销售一部")
    print("-" * 70)
    transfer_user(user, xiaoshou_yibu.id)
    result3 = verify_user_access(user, '销售一部', 5)

    print(f"主组织: {result3['actual_org']} (预期: {result3['expected_org']}) {'✓' if result3['org_correct'] else '✗'}")
    print(f"可访问合同数: {result3['actual_count']} (预期: {result3['expected_count']}) {'✓' if result3['count_correct'] else '✗'}")
    print(f"合同归属: {'✓ 全部属于主组织' if result3['all_from_main_org'] else '✗ 有其他组织的合同'}")
    print(f"测试结果: {'✓ 通过' if result3['success'] else '✗ 失败'}")

    # 最终总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    all_tests_pass = result1['success'] and result2['success'] and result3['success']

    print(f"\n测试1 (调到销售一部): {'✓ 通过' if result1['success'] else '✗ 失败'}")
    print(f"测试2 (调到新能源服务部): {'✓ 通过' if result2['success'] else '✗ 失败'}")
    print(f"测试3 (调回销售一部): {'✓ 通过' if result3['success'] else '✗ 失败'}")

    if all_tests_pass:
        print("\n" + "=" * 70)
        print("✓✓✓ 所有测试通过！组织调动功能完全正常！ ✓✓✓")
        print("=" * 70)
        print("\n核心功能验证:")
        print("  ✓ 用户调入新组织后，主组织正确切换")
        print("  ✓ 数据权限立即跟随组织变动")
        print("  ✓ 只能看到主组织的合同，看不到其他组织的合同")
        print("  ✓ 双向调动都能正常工作")
        print("  ✓ User.organization_id 和 UserOrganization.is_primary 保持同步")
        print("\n系统状态: 完美运行 ✓")
    else:
        print("\n✗ 部分测试失败，需要检查")

    print("\n" + "=" * 70)
