"""
为毕少鹏分配项目经理岗位
"""
from app import app
from models import db, User, Position, UserPosition

with app.app_context():
    user = User.query.filter_by(username='毕少鹏').first()
    if not user:
        print("错误: 未找到用户'毕少鹏'")
        exit(1)

    customer_id = user.customer_id
    print(f"用户: {user.username}, 租户ID: {customer_id}")

    # 查找或创建"项目经理"岗位
    position = Position.query.filter_by(
        name='项目经理',
        customer_id=customer_id
    ).first()

    if not position:
        # 创建项目经理岗位
        position = Position(
            name='项目经理',
            customer_id=customer_id,
            function_permissions='增加,修改,删除,查阅,上传,下载',
            data_scope='self',
            description='项目经理，可以管理自己负责的项目合同'
        )
        db.session.add(position)
        db.session.commit()
        print(f"[OK] 创建岗位: {position.name}")
    else:
        print(f"[OK] 找到现有岗位: {position.name}")

    print(f"  - 功能权限: {position.function_permissions}")
    print(f"  - 数据权限: {position.data_scope}")

    # 检查是否已分配
    existing = UserPosition.query.filter_by(
        user_id=user.id,
        position_id=position.id
    ).first()

    if existing:
        print(f"[INFO] 用户已分配到该岗位")
    else:
        # 分配岗位
        up = UserPosition(user_id=user.id, position_id=position.id)
        db.session.add(up)
        db.session.commit()
        print(f"[OK] 已将用户'{user.username}'分配到岗位'{position.name}'")

    # 验证权限
    from app import get_user_function_permissions, has_permission
    perms = get_user_function_permissions(user.id)
    print(f"\n[验证] 用户综合功能权限: {perms}")
    print(f"  - 有'修改'权限: {has_permission(user.id, '修改')}")
    print(f"  - 有'删除'权限: {has_permission(user.id, '删除')}")

    print("\n[完成] 毕少鹏现在可以编辑和删除自己负责的合同了！")
