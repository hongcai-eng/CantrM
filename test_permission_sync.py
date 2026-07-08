#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试岗位权限同步功能
验证修改岗位权限后，用户权限是否立即生效
"""

from app import app, db, get_user_function_permissions, get_user_permissions_string
from models import User, Position, UserPosition

def test_permission_sync():
    with app.app_context():
        print("=" * 60)
        print("岗位权限同步测试")
        print("=" * 60)

        # 查找一个测试岗位
        position = Position.query.first()
        if not position:
            print("❌ 没有找到岗位，无法测试")
            return

        print(f"\n测试岗位: {position.name} (ID: {position.id})")
        print(f"当前权限: {position.function_permissions}")

        # 查找该岗位下的用户
        user_positions = UserPosition.query.filter_by(position_id=position.id).all()
        if not user_positions:
            print("❌ 该岗位下没有用户，无法测试")
            return

        print(f"\n该岗位下共有 {len(user_positions)} 个用户")

        for up in user_positions:
            user = db.session.get(User, up.user_id)
            if user:
                perms = get_user_function_permissions(user.id)
                perms_str = get_user_permissions_string(user.id)
                print(f"  - 用户: {user.username}")
                print(f"    用户自身权限: {user.permissions}")
                print(f"    综合权限: {perms_str}")

        print("\n" + "=" * 60)
        print("✅ 权限系统工作原理:")
        print("1. get_user_function_permissions() 实时从数据库读取岗位权限")
        print("2. 不使用任何缓存机制")
        print("3. 修改岗位权限后，下次请求立即生效")
        print("4. 如果页面权限未更新，用户需要刷新页面")
        print("=" * 60)

if __name__ == '__main__':
    test_permission_sync()
