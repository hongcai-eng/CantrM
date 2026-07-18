import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app import app
from models import User

with app.app_context():
    with app.test_client() as client:
        # 登录
        with client.session_transaction() as sess:
            user = User.query.filter_by(username='admin').first()
            sess['user_id'] = user.id
            sess['username'] = user.username
            sess['role'] = user.role

        print('测试合同类型筛选：')
        print('=' * 60)

        # 测试筛选"货物"
        response = client.get('/?contract_type=货物')
        html = response.data.decode('utf-8')

        # 统计表格中的合同行数
        import re
        # 查找所有 "查看" 按钮（每个合同一个）
        view_buttons = re.findall(r'查看</a>', html)
        print(f'✓ 筛选"货物"类型，页面显示合同数: {len(view_buttons)}')

        # 提取统计卡片中的数字
        match = re.search(r'<div style="font-size:20px;font-weight:bold;color:#333;">(\d+)</div>', html)
        if match:
            print(f'✓ 统计卡片显示合同数量: {match.group(1)}')

        # 测试筛选"服务"
        response = client.get('/?contract_type=服务')
        html = response.data.decode('utf-8')
        view_buttons = re.findall(r'查看</a>', html)
        print(f'✓ 筛选"服务"类型，页面显示合同数: {len(view_buttons)}')

        # 测试筛选"工程"
        response = client.get('/?contract_type=工程')
        html = response.data.decode('utf-8')
        view_buttons = re.findall(r'查看</a>', html)
        print(f'✓ 筛选"工程"类型，页面显示合同数: {len(view_buttons)}')

        # 测试不筛选
        response = client.get('/')
        html = response.data.decode('utf-8')
        view_buttons = re.findall(r'查看</a>', html)
        print(f'✓ 不筛选，页面显示合同数: {len(view_buttons)}')

print('\n✅ 测试完成')
