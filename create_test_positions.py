"""
创建测试岗位数据
"""
from app import app
from models import db, Position, User, UserPosition, Contract, Organization, UserOrganization
from datetime import datetime

def create_test_positions():
    """创建测试岗位"""
    with app.app_context():
        print("\n正在创建测试岗位...")

        # 清理旧的测试数据
        Position.query.filter(Position.name.like('测试%')).delete()
        db.session.commit()

        # 获取第一个租户
        tenant_user = User.query.filter(User.customer_id.isnot(None)).first()
        if not tenant_user:
            print("错误: 没有找到租户用户")
            return

        customer_id = tenant_user.customer_id
        print(f"租户ID: {customer_id}")

        # 1. 创建岗位: 全部合同权限
        pos1 = Position(
            name='测试岗位-全部合同',
            customer_id=customer_id,
            function_permissions='增加,修改,查阅',
            data_scope='all',
            description='测试岗位，可以访问所有合同'
        )
        db.session.add(pos1)

        # 2. 创建岗位: 本组织合同权限
        pos2 = Position(
            name='测试岗位-本组织',
            customer_id=customer_id,
            function_permissions='查阅,修改',
            data_scope='org',
            description='测试岗位，只能访问本组织合同'
        )
        db.session.add(pos2)

        # 3. 创建岗位: 自定义权限
        pos3 = Position(
            name='测试岗位-自定义',
            customer_id=customer_id,
            function_permissions='查阅',
            data_scope='custom',
            description='测试岗位，只能访问被授权的合同'
        )
        db.session.add(pos3)

        # 4. 创建岗位: 仅自己创建的合同
        pos4 = Position(
            name='测试岗位-仅自己',
            customer_id=customer_id,
            function_permissions='增加,查阅',
            data_scope='self',
            description='测试岗位，只能访问自己创建的合同'
        )
        db.session.add(pos4)

        db.session.commit()
        print(f"[OK] 创建了4个测试岗位")

        # 查找租户的普通用户（非超级管理员）
        test_users = User.query.filter(
            User.customer_id == customer_id,
            User.role != '超级管理员'
        ).limit(4).all()

        if len(test_users) >= 1:
            # 为用户1分配全部合同权限
            up1 = UserPosition(user_id=test_users[0].id, position_id=pos1.id)
            db.session.add(up1)
            print(f"[OK] 用户 '{test_users[0].username}' -> 测试岗位-全部合同")

        if len(test_users) >= 2:
            # 为用户2分配本组织权限
            up2 = UserPosition(user_id=test_users[1].id, position_id=pos2.id)
            db.session.add(up2)
            print(f"[OK] 用户 '{test_users[1].username}' -> 测试岗位-本组织")

            # 为用户2分配到组织
            org = Organization.query.filter_by(customer_id=customer_id).first()
            if org:
                uo = UserOrganization(user_id=test_users[1].id, organization_id=org.id)
                db.session.add(uo)
                print(f"  [->] 分配到组织: {org.name}")

        if len(test_users) >= 3:
            # 为用户3分配自定义权限
            up3 = UserPosition(user_id=test_users[2].id, position_id=pos3.id)
            db.session.add(up3)
            print(f"[OK] 用户 '{test_users[2].username}' -> 测试岗位-自定义")

        if len(test_users) >= 4:
            # 为用户4分配仅自己权限
            up4 = UserPosition(user_id=test_users[3].id, position_id=pos4.id)
            db.session.add(up4)
            print(f"[OK] 用户 '{test_users[3].username}' -> 测试岗位-仅自己")

        db.session.commit()
        print(f"\n[OK] 测试数据创建完成!")

        # 显示统计
        print(f"\n统计:")
        print(f"  - 岗位数: {Position.query.count()}")
        print(f"  - 用户-岗位关联: {UserPosition.query.count()}")


if __name__ == '__main__':
    create_test_positions()
