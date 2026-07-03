"""
测试权限系统功能
"""
from app import app
from models import db, User, Position, UserPosition, Organization, UserOrganization, Contract

def test_function_permissions():
    """测试功能权限整合"""
    print("\n" + "="*60)
    print("测试1: 功能权限整合")
    print("="*60)

    with app.app_context():
        from app import get_user_function_permissions, has_permission

        # 测试超级管理员
        admin = User.query.filter_by(username='admin').first()
        if admin:
            perms = get_user_function_permissions(admin.id)
            print(f"\n超级管理员 'admin' 的权限: {perms}")
            print(f"  - 是否有'增加'权限: {has_permission(admin.id, '增加')}")
            print(f"  - 是否有'删除'权限: {has_permission(admin.id, '删除')}")

        # 查找有岗位的普通用户
        user_with_position = db.session.query(User).join(
            UserPosition, User.id == UserPosition.user_id
        ).filter(User.role != '超级管理员').first()

        if user_with_position:
            print(f"\n普通用户 '{user_with_position.username}' 的权限:")
            perms = get_user_function_permissions(user_with_position.id)
            print(f"  - 综合权限: {perms}")

            # 检查各项权限
            for perm in ['增加', '删除', '修改', '查阅']:
                has = has_permission(user_with_position.id, perm)
                print(f"  - 是否有'{perm}'权限: {has}")
        else:
            print("\n未找到有岗位的普通用户")


def test_data_permissions():
    """测试数据权限过滤"""
    print("\n" + "="*60)
    print("测试2: 数据权限过滤")
    print("="*60)

    with app.app_context():
        from app import get_user_data_scope, get_user_accessible_contract_ids

        # 测试超级管理员
        admin = User.query.filter_by(username='admin').first()
        if admin:
            scope = get_user_data_scope(admin.id)
            print(f"\n超级管理员 'admin' 的数据权限范围: {scope}")

        # 查找有岗位的普通用户
        user_with_position = db.session.query(User).join(
            UserPosition, User.id == UserPosition.user_id
        ).filter(User.role != '超级管理员').first()

        if user_with_position:
            scope = get_user_data_scope(user_with_position.id)
            print(f"\n普通用户 '{user_with_position.username}' 的数据权限范围: {scope}")

            if user_with_position.customer_id:
                accessible_ids = get_user_accessible_contract_ids(
                    user_with_position.id,
                    user_with_position.customer_id
                )

                if accessible_ids is None:
                    print(f"  - 可访问: 全部合同")
                elif len(accessible_ids) == 0:
                    print(f"  - 可访问: 无合同")
                else:
                    print(f"  - 可访问: {len(accessible_ids)} 个合同")
                    print(f"  - 合同ID: {accessible_ids[:5]}{'...' if len(accessible_ids) > 5 else ''}")


def test_database_stats():
    """显示数据库统计信息"""
    print("\n" + "="*60)
    print("数据库统计")
    print("="*60)

    with app.app_context():
        user_count = User.query.count()
        position_count = Position.query.count()
        user_position_count = UserPosition.query.count()
        contract_count = Contract.query.count()
        org_count = Organization.query.count()

        print(f"\n用户数: {user_count}")
        print(f"岗位数: {position_count}")
        print(f"用户-岗位关联数: {user_position_count}")
        print(f"合同数: {contract_count}")
        print(f"组织数: {org_count}")

        # 显示岗位详情
        if position_count > 0:
            print("\n岗位详情:")
            positions = Position.query.all()
            for pos in positions:
                print(f"  - {pos.name}:")
                print(f"      功能权限: {pos.function_permissions or '无'}")
                print(f"      数据权限: {pos.data_scope}")
                user_count = UserPosition.query.filter_by(position_id=pos.id).count()
                print(f"      用户数: {user_count}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("权限系统测试")
    print("="*60)

    try:
        test_database_stats()
        test_function_permissions()
        test_data_permissions()

        print("\n" + "="*60)
        print("测试完成!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
