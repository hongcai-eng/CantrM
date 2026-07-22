#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查用户权限的调试脚本"""

from app import app, db
from models import User, Position, UserPosition

def check_user_permissions(username):
    """检查指定用户的权限"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"用户 {username} 不存在")
            return

        print(f"\n========== 用户信息 ==========")
        print(f"用户名: {user.username}")
        print(f"角色: {user.role}")
        print(f"用户自身权限: {user.permissions}")
        print(f"租户ID: {user.customer_id}")

        # 获取用户岗位
        user_positions = UserPosition.query.filter_by(user_id=user.id).all()

        if not user_positions:
            print(f"\n该用户没有分配岗位")
        else:
            print(f"\n========== 岗位信息 ==========")
            for up in user_positions:
                position = db.session.get(Position, up.position_id)
                if position:
                    print(f"岗位名称: {position.name}")
                    print(f"岗位权限: {position.function_permissions}")
                    print(f"是否主岗位: {up.is_primary}")
                    print(f"---")

        # 计算综合权限
        print(f"\n========== 综合权限 ==========")
        all_perms = set()

        # 用户自身权限
        if user.permissions and user.permissions != 'all':
            all_perms.update(user.permissions.split(','))
        elif user.permissions == 'all':
            print("用户有全部权限 (all)")
            return

        # 岗位权限
        for up in user_positions:
            position = db.session.get(Position, up.position_id)
            if position and position.function_permissions:
                position_perms = position.function_permissions.split(',')
                all_perms.update(position_perms)

        print(f"合并后的权限列表:")
        for perm in sorted(all_perms):
            print(f"  - {perm}")

        # 检查导入EXCEL权限
        print(f"\n========== 权限检查 ==========")
        has_import = '导入EXCEL' in all_perms
        print(f"是否有'导入EXCEL'权限: {has_import}")

        # 显示权限字符串的原始格式（检查空格等问题）
        print(f"\n========== 原始权限字符串（用于调试） ==========")
        for perm in sorted(all_perms):
            print(f"  '{perm}' (长度: {len(perm)}, repr: {repr(perm)})")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python check_user_permission.py <用户名>")
        print("例如: python check_user_permission.py 梁靓亮")
        sys.exit(1)

    username = sys.argv[1]
    check_user_permissions(username)
