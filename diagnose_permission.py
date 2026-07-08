#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
权限问题诊断脚本
用于检查用户为什么看不到组织合同
"""

from app import app, db, get_user_data_scope, get_user_accessible_contract_ids
from models import User, Position, UserPosition, Organization, Contract, UserOrganization

def diagnose_permission_issue():
    with app.app_context():
        print("=" * 80)
        print("权限问题诊断")
        print("=" * 80)

        # 1. 查找所有非管理员用户
        users = User.query.filter(User.role != '超级管理员').all()

        if not users:
            print("❌ 没有找到普通用户")
            return

        print(f"\n找到 {len(users)} 个普通用户\n")

        for user in users[:5]:  # 只检查前5个
            print("-" * 80)
            print(f"用户: {user.username} (ID: {user.id})")
            print("-" * 80)

            # 2. 检查用户的组织归属
            print(f"\n【组织归属】")
            print(f"  User.organization_id: {user.organization_id}")
            if user.organization_id:
                org = db.session.get(Organization, user.organization_id)
                print(f"  所属组织: {org.name if org else '组织已删除'}")
            else:
                print(f"  ⚠️  用户没有主组织")

            # 3. 检查用户的岗位
            print(f"\n【岗位信息】")
            user_positions = UserPosition.query.filter_by(user_id=user.id).all()
            print(f"  岗位数量: {len(user_positions)}")

            if not user_positions:
                print(f"  ❌ 用户没有任何岗位！")
                continue

            for up in user_positions:
                position = db.session.get(Position, up.position_id)
                if position:
                    print(f"\n  岗位: {position.name}")
                    print(f"    - 数据权限范围: {position.data_scope}")
                    print(f"    - 功能权限: {position.function_permissions}")
                    print(f"    - UserPosition.organization_id: {up.organization_id}")
                    print(f"    - is_primary: {up.is_primary}")

                    if position.data_scope == 'org' and not up.organization_id:
                        print(f"    ⚠️  问题：岗位要求'本组织合同'，但UserPosition没有组织ID！")

            # 4. 检查 UserOrganization 表
            print(f"\n【UserOrganization 表】")
            user_orgs = UserOrganization.query.filter_by(user_id=user.id).all()
            print(f"  记录数: {len(user_orgs)}")
            for uo in user_orgs:
                org = db.session.get(Organization, uo.organization_id)
                print(f"    - 组织: {org.name if org else '已删除'}, is_primary: {uo.is_primary}")

            # 5. 计算数据权限
            print(f"\n【权限计算结果】")
            data_scope = get_user_data_scope(user.id)
            print(f"  数据权限范围: {data_scope}")

            # 6. 查看可访问的合同
            if user.customer_id:
                accessible = get_user_accessible_contract_ids(user.id, user.customer_id)
                if accessible is None:
                    print(f"  可访问合同: 全部")
                else:
                    print(f"  可访问合同数量: {len(accessible)}")
                    if len(accessible) == 0:
                        print(f"  ❌ 用户无法访问任何合同！")

            # 7. 检查组织是否有合同
            if user.organization_id:
                org_contracts = Contract.query.filter_by(
                    organization_id=user.organization_id,
                    customer_id=user.customer_id
                ).all()
                print(f"\n【组织合同】")
                print(f"  该组织的合同数: {len(org_contracts)}")
                if len(org_contracts) > 0:
                    print(f"  示例合同:")
                    for c in org_contracts[:3]:
                        print(f"    - {c.contract_number}: {c.project_name}")

            print("\n")

        print("=" * 80)
        print("诊断总结")
        print("=" * 80)
        print("\n常见问题：")
        print("1. ❌ UserPosition.organization_id 为 None（岗位没有关联组织）")
        print("2. ❌ User.organization_id 为 None（用户没有主组织）")
        print("3. ❌ UserOrganization 表中没有 is_primary=True 的记录")
        print("4. ❌ 合同的 organization_id 为 None（合同没有分配到组织）")
        print("\n解决方法：")
        print("1. 进入'岗位管理' → '分配用户'")
        print("2. 移除用户的岗位")
        print("3. 重新分配，务必选择'所属组织'")
        print("4. 勾选'设为主岗位'")
        print("5. 保存后，用户刷新页面即可看到组织合同")

if __name__ == '__main__':
    diagnose_permission_issue()
