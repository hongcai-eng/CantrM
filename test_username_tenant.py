"""测试同一用户名在不同租户下可以共存"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app, db
from models import User, TenantCustomer

def test():
    with app.app_context():
        tenants = TenantCustomer.query.limit(2).all()
        if len(tenants) < 2:
            print("SKIP: 需要至少2个租户才能测试")
            return

        t1, t2 = tenants[0], tenants[1]
        test_username = '_test_zhangsan_'

        # 清理残留
        User.query.filter_by(username=test_username).delete()
        db.session.commit()

        # 在租户1创建用户
        u1 = User(username=test_username, role='普通用户', customer_id=t1.id)
        u1.set_password('test123')
        db.session.add(u1)
        db.session.commit()
        print(f"✓ 在租户「{t1.name}」创建用户 {test_username} 成功")

        # 验证：同租户内重名应被检测到
        dup = User.query.filter_by(username=test_username, customer_id=t1.id).first()
        assert dup is not None, "同租户内应能查到已有用户"
        print(f"✓ 同租户重名检测正常（filter_by username+customer_id 能找到）")

        # 验证：不同租户同名不冲突
        dup_other = User.query.filter_by(username=test_username, customer_id=t2.id).first()
        assert dup_other is None, "不同租户不应查到对方的用户"
        print(f"✓ 不同租户「{t2.name}」查不到该用户，跨租户隔离正常")

        # 在租户2创建同名用户
        u2 = User(username=test_username, role='普通用户', customer_id=t2.id)
        u2.set_password('test123')
        db.session.add(u2)
        db.session.commit()
        print(f"✓ 在租户「{t2.name}」创建同名用户 {test_username} 成功，无冲突")

        # 清理
        User.query.filter_by(username=test_username).delete()
        db.session.commit()
        print("\n所有测试通过")

test()
