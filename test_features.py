"""
测试脚本：验证组织管理和品牌功能
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app, db
from models import User, TenantCustomer, Organization

def test_features():
    with app.app_context():
        print("=" * 60)
        print("测试 1: 验证数据库表结构")
        print("=" * 60)

        # 检查 Organization 表
        orgs = Organization.query.all()
        print(f"✓ Organization 表可访问，当前记录数: {len(orgs)}")

        # 检查 User.organization_id 字段
        users = User.query.all()
        print(f"✓ User 表可访问，当前用户数: {len(users)}")
        for u in users[:3]:
            print(f"  - {u.username}: organization_id={u.organization_id}")

        # 检查 TenantCustomer 品牌字段
        tenants = TenantCustomer.query.all()
        print(f"✓ TenantCustomer 表可访问，当前租户数: {len(tenants)}")
        for t in tenants:
            print(f"  - {t.name}: company_name={t.company_name}, logo_file={t.logo_file}")

        print("\n" + "=" * 60)
        print("测试 2: 创建测试组织")
        print("=" * 60)

        # 找一个有租户的用户
        tenant_user = User.query.filter(User.customer_id != None).first()
        if tenant_user:
            customer_id = tenant_user.customer_id
            tenant = TenantCustomer.query.get(customer_id)
            print(f"✓ 使用租户: {tenant.name} (ID: {customer_id})")

            # 创建测试组织
            test_org = Organization.query.filter_by(
                name='测试部门',
                customer_id=customer_id
            ).first()

            if not test_org:
                test_org = Organization(
                    name='测试部门',
                    description='自动化测试创建的组织',
                    customer_id=customer_id
                )
                db.session.add(test_org)
                db.session.commit()
                print(f"✓ 创建测试组织: {test_org.name} (ID: {test_org.id})")
            else:
                print(f"✓ 测试组织已存在: {test_org.name} (ID: {test_org.id})")

            # 创建子组织
            sub_org = Organization.query.filter_by(
                name='测试子部门',
                customer_id=customer_id
            ).first()

            if not sub_org:
                sub_org = Organization(
                    name='测试子部门',
                    description='测试层级结构',
                    parent_id=test_org.id,
                    customer_id=customer_id
                )
                db.session.add(sub_org)
                db.session.commit()
                print(f"✓ 创建子组织: {sub_org.name} (父组织: {test_org.name})")
            else:
                print(f"✓ 子组织已存在: {sub_org.name}")

            print("\n" + "=" * 60)
            print("测试 3: 人员调动")
            print("=" * 60)

            # 将用户分配到组织
            if tenant_user.organization_id != test_org.id:
                tenant_user.organization_id = test_org.id
                db.session.commit()
                print(f"✓ 用户 {tenant_user.username} 调入组织 {test_org.name}")
            else:
                print(f"✓ 用户 {tenant_user.username} 已在组织 {test_org.name}")

            # 验证关联
            print(f"✓ 组织 {test_org.name} 成员数: {len(test_org.members)}")
            for member in test_org.members:
                print(f"  - {member.username} ({member.role})")
        else:
            print("⚠ 未找到租户用户，跳过组织测试")

        print("\n" + "=" * 60)
        print("测试 4: API 接口测试")
        print("=" * 60)

        with app.test_client() as client:
            # 测试品牌 API
            response = client.get('/api/user_branding?username=admin')
            data = response.get_json()
            print(f"✓ /api/user_branding?username=admin")
            print(f"  company_name: {data.get('company_name')}")
            print(f"  logo_url: {data.get('logo_url')}")

            if tenant_user:
                response = client.get(f'/api/user_branding?username={tenant_user.username}')
                data = response.get_json()
                print(f"✓ /api/user_branding?username={tenant_user.username}")
                print(f"  company_name: {data.get('company_name')}")
                print(f"  logo_url: {data.get('logo_url')}")

        print("\n" + "=" * 60)
        print("测试 5: 统计功能验证")
        print("=" * 60)

        from models import Contract
        contracts = Contract.query.limit(5).all()
        print(f"✓ 合同总数: {Contract.query.count()}")

        if contracts:
            total_price = sum(c.total_price for c in contracts[:5])
            total_paid = sum(c.get_total_paid() for c in contracts[:5])
            total_unpaid = sum(c.get_unpaid_amount() for c in contracts[:5])
            print(f"✓ 前5条合同统计:")
            print(f"  合同总金额: ¥{total_price:.2f}")
            print(f"  已收付款: ¥{total_paid:.2f}")
            print(f"  未收付款: ¥{total_unpaid:.2f}")

        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)

if __name__ == '__main__':
    test_features()
