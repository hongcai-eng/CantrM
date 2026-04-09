import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app import app
from models import User, ContractProduct, Contract

with app.app_context():
    print('测试合同类型筛选：')
    print('=' * 60)

    with app.test_client() as client:
        # 登录
        with client.session_transaction() as sess:
            user = User.query.filter_by(username='admin').first()
            sess['user_id'] = user.id
            sess['username'] = user.username
            sess['role'] = user.role

        # 测试筛选"货物"
        response = client.get('/?contract_type=货物')
        html = response.data.decode('utf-8')

        # 提取统计数字
        import re
        match = re.search(r'合同数量.*?(\d+)', html, re.DOTALL)
        if match:
            count = match.group(1)
            print(f'✓ 筛选"货物"类型合同数量: {count}')

        # 测试筛选"服务"
        response = client.get('/?contract_type=服务')
        html = response.data.decode('utf-8')
        match = re.search(r'合同数量.*?(\d+)', html, re.DOTALL)
        if match:
            count = match.group(1)
            print(f'✓ 筛选"服务"类型合同数量: {count}')

        # 测试筛选"工程"
        response = client.get('/?contract_type=工程')
        html = response.data.decode('utf-8')
        match = re.search(r'合同数量.*?(\d+)', html, re.DOTALL)
        if match:
            count = match.group(1)
            print(f'✓ 筛选"工程"类型合同数量: {count}')

    print('\n验证数据库实际数据：')
    print('=' * 60)
    print(f'ContractProduct 表中 contract_type=货物: {ContractProduct.query.filter_by(contract_type="货物").count()} 条产品记录')
    print(f'ContractProduct 表中 contract_type=服务: {ContractProduct.query.filter_by(contract_type="服务").count()} 条产品记录')
    print(f'ContractProduct 表中 contract_type=工程: {ContractProduct.query.filter_by(contract_type="工程").count()} 条产品记录')

    # 查看包含"货物"类型产品的合同
    contract_ids = [p.contract_id for p in ContractProduct.query.filter_by(contract_type='货物').all()]
    unique_ids = list(set(contract_ids))
    print(f'\n包含"货物"类型产品的合同ID: {unique_ids}')
    print(f'对应的合同数量: {len(unique_ids)}')

    print('\n✅ 筛选功能测试完成')
