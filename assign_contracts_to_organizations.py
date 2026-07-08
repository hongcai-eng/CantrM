#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量分配合同到组织
解决合同未分配组织导致用户看不到的问题
"""

from app import app, db
from models import Contract, Organization, User

def assign_contracts_to_organizations():
    with app.app_context():
        print("=" * 60)
        print("批量分配合同到组织")
        print("=" * 60)

        # 1. 查找未分配组织的合同
        unassigned_contracts = Contract.query.filter_by(organization_id=None).all()
        print(f"\n找到 {len(unassigned_contracts)} 个未分配组织的合同")

        if len(unassigned_contracts) == 0:
            print("所有合同都已分配组织，无需处理")
            return

        # 2. 列出所有组织
        organizations = Organization.query.all()
        print(f"\n可用的组织列表:")
        for org in organizations:
            print(f"  {org.id}. {org.name}")

        # 3. 提供选项
        print("\n" + "=" * 60)
        print("请选择分配方式:")
        print("=" * 60)
        print("1. 全部分配到同一个组织")
        print("2. 根据项目负责人自动分配")
        print("3. 根据创建人自动分配")
        print("4. 手动逐个分配（适合少量合同）")
        print("5. 导出未分配合同列表到Excel，手动分配后导入")

        choice = input("\n请输入选择 (1-5): ").strip()

        if choice == '1':
            # 全部分配到同一个组织
            org_id = input(f"请输入组织ID (1-{len(organizations)}): ").strip()
            if not org_id.isdigit():
                print("错误: 请输入数字")
                return

            org_id = int(org_id)
            org = db.session.get(Organization, org_id)
            if not org:
                print("错误: 组织不存在")
                return

            confirm = input(f"确认将 {len(unassigned_contracts)} 个合同全部分配到 '{org.name}'? (y/n): ")
            if confirm.lower() == 'y':
                for contract in unassigned_contracts:
                    contract.organization_id = org_id
                db.session.commit()
                print(f"已将 {len(unassigned_contracts)} 个合同分配到 '{org.name}'")

        elif choice == '2':
            # 根据项目负责人自动分配
            print("\n根据项目负责人的组织自动分配...")
            assigned_count = 0

            for contract in unassigned_contracts:
                if contract.project_staff:
                    # 取第一个项目负责人
                    staff_name = contract.project_staff.split(',')[0].strip()
                    user = User.query.filter_by(username=staff_name).first()

                    if user and user.organization_id:
                        contract.organization_id = user.organization_id
                        assigned_count += 1
                        print(f"  合同 {contract.contract_number} -> 组织ID {user.organization_id} (项目负责人: {staff_name})")

            if assigned_count > 0:
                db.session.commit()
                print(f"\n已自动分配 {assigned_count} 个合同")
                print(f"剩余 {len(unassigned_contracts) - assigned_count} 个合同未分配（无项目负责人或负责人无组织）")
            else:
                print("未能自动分配任何合同")

        elif choice == '3':
            # 根据创建人自动分配
            print("\n根据创建人的组织自动分配...")
            assigned_count = 0

            for contract in unassigned_contracts:
                if contract.created_by:
                    user = db.session.get(User, contract.created_by)

                    if user and user.organization_id:
                        contract.organization_id = user.organization_id
                        assigned_count += 1
                        print(f"  合同 {contract.contract_number} -> 组织ID {user.organization_id} (创建人: {user.username})")

            if assigned_count > 0:
                db.session.commit()
                print(f"\n已自动分配 {assigned_count} 个合同")
                print(f"剩余 {len(unassigned_contracts) - assigned_count} 个合同未分配")
            else:
                print("未能自动分配任何合同")

        elif choice == '4':
            # 手动逐个分配
            print("\n手动分配模式（输入 'q' 退出）")

            for i, contract in enumerate(unassigned_contracts[:20], 1):  # 只显示前20个
                print(f"\n[{i}/{len(unassigned_contracts)}] 合同: {contract.contract_number}")
                print(f"  项目名称: {contract.project_name}")
                print(f"  客户: {contract.customer_name}")
                print(f"  项目负责人: {contract.project_staff or '无'}")

                org_id = input(f"  分配到组织ID (1-{len(organizations)}, 留空跳过, q退出): ").strip()

                if org_id.lower() == 'q':
                    break

                if org_id and org_id.isdigit():
                    org_id = int(org_id)
                    org = db.session.get(Organization, org_id)
                    if org:
                        contract.organization_id = org_id
                        print(f"  已分配到: {org.name}")

            db.session.commit()
            print("\n手动分配完成")

        elif choice == '5':
            # 导出到Excel
            print("\n导出未分配合同列表...")
            import pandas as pd

            data = []
            for contract in unassigned_contracts:
                data.append({
                    '合同ID': contract.id,
                    '合同编号': contract.contract_number,
                    '项目名称': contract.project_name,
                    '客户名称': contract.customer_name,
                    '项目负责人': contract.project_staff,
                    '组织ID': '',  # 空白，等待填写
                    '组织名称': ''  # 参考
                })

            df = pd.DataFrame(data)
            filename = 'unassigned_contracts.xlsx'
            df.to_excel(filename, index=False)

            print(f"已导出到 {filename}")
            print("\n请在Excel中填写'组织ID'列，然后使用导入功能批量分配")

        else:
            print("无效的选择")

        print("\n" + "=" * 60)
        print("完成！")
        print("=" * 60)

if __name__ == '__main__':
    assign_contracts_to_organizations()
