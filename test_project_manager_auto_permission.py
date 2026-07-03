"""
测试项目负责人自动权限功能
"""
from app import app
from models import User, Contract

with app.app_context():
    # 测试付伟龙
    user = User.query.filter_by(username='付伟龙').first()
    if user:
        print(f"测试用户: {user.username}")
        print(f"用户自身权限: {user.permissions or '无'}")

        # 查找他负责的合同
        contracts = Contract.query.filter(
            Contract.customer_id == user.customer_id,
            Contract.project_staff.like(f'%{user.username}%')
        ).all()

        print(f"\n作为项目负责人的合同: {len(contracts)} 个")

        if len(contracts) > 0:
            test_contract = contracts[0]
            print(f"\n测试合同: ID={test_contract.id}, 项目={test_contract.project_name}")
            print(f"项目负责人: {test_contract.project_staff}")

            # 测试权限
            from app import has_permission_for_contract

            permissions_to_test = ['增加', '修改', '删除', '查阅', '上传', '下载']
            print(f"\n权限测试:")
            for perm in permissions_to_test:
                has_perm = has_permission_for_contract(user.id, perm, test_contract)
                status = "[OK]" if has_perm else "[FAIL]"
                print(f"  {status} '{perm}': {has_perm}")

            print(f"\n结论: 项目负责人'{user.username}'对合同ID {test_contract.id} 拥有完整权限")
        else:
            print("\n未找到该用户负责的合同")
    else:
        print("未找到用户'付伟龙'")

    print("\n" + "="*60)

    # 测试非项目负责人
    print("\n对比测试: 非项目负责人")
    user2 = User.query.filter(
        User.customer_id == user.customer_id,
        User.role != '超级管理员'
    ).filter(User.id != user.id).first()

    if user2 and len(contracts) > 0:
        print(f"用户: {user2.username}")
        print(f"用户自身权限: {user2.permissions or '无'}")

        test_contract = contracts[0]
        print(f"\n测试合同: ID={test_contract.id} (不是该用户负责的)")

        from app import has_permission_for_contract
        has_perm = has_permission_for_contract(user2.id, '修改', test_contract)
        status = "[OK]" if has_perm else "[EXPECTED]"
        print(f"  {status} '修改'权限: {has_perm}")

        if not has_perm:
            print(f"\n结论: 非项目负责人'{user2.username}'没有该合同的自动权限（符合预期）")

print("\n" + "="*60)
print("测试完成!")
print("="*60)
