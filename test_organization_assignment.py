#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试合同组织分配功能
验证：
1. 合同可以分配给组织
2. 用户可以看到所属组织的合同
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from models import User, Contract, Organization

with app.app_context():
    print("=" * 60)
    print("测试合同组织分配功能")
    print("=" * 60)

    # 查找吴洪才yh用户
    user = User.query.filter_by(username='吴洪才yh', customer_id=3).first()
    if not user:
        print("错误：未找到吴洪才yh用户")
        sys.exit(1)

    print(f"\n用户信息:")
    print(f"  用户名: {user.username}")
    print(f"  组织ID: {user.organization_id}")

    # 查找商务部
    org = db.session.get(Organization, user.organization_id)
    if org:
        print(f"  组织名称: {org.name}")

    # 查找亿海立达的第一个合同
    contract = Contract.query.filter_by(customer_id=3).first()
    if not contract:
        print("\n错误：亿海立达租户没有合同")
        sys.exit(1)

    print(f"\n测试合同:")
    print(f"  合同ID: {contract.id}")
    print(f"  项目名称: {contract.project_name}")
    print(f"  当前所属组织: {contract.organization_id}")

    # 将合同分配给商务部
    print(f"\n将合同分配给商务部...")
    contract.organization_id = user.organization_id
    db.session.commit()
    print(f"✓ 分配成功")

    # 验证用户现在能否看到这个合同
    from app import get_user_accessible_contract_ids

    accessible_ids = get_user_accessible_contract_ids(user.id, user.customer_id)

    print(f"\n验证数据权限:")
    if accessible_ids is None:
        print(f"  用户可访问: 全部合同")
    else:
        print(f"  用户可访问合同数: {len(accessible_ids)}")
        if contract.id in accessible_ids:
            print(f"  ✓ 用户可以看到测试合同 (ID: {contract.id})")
        else:
            print(f"  ✗ 用户看不到测试合同 (ID: {contract.id})")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print("\n下一步:")
    print("1. 使用亿海立达管理员账号登录")
    print("2. 编辑其他合同，在'所属组织/部门'下拉框中选择'商务部'")
    print("3. 保存后，吴洪才yh登录就能看到这些合同了")
    print("=" * 60)
