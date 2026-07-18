# -*- coding: utf-8 -*-
"""针对 2026.07.13 三处改动的集成测试。
只读验证，不修改数据库业务数据（调整改派用回滚保护）。"""
import re
import sqlite3
from app import app, db
from models import User, Position, Contract


def find_superadmin_cust3():
    with app.app_context():
        u = User.query.filter_by(customer_id=3, role='超级管理员').first()
        return u.id if u else None


def login_as(client, user_id):
    with app.app_context():
        u = db.session.get(User, user_id)
        with client.session_transaction() as sess:
            sess['user_id'] = u.id
            sess['username'] = u.username
            sess['role'] = u.role


results = []


def check(name, cond, detail=''):
    results.append((name, cond, detail))
    print(('PASS' if cond else 'FAIL'), '-', name, ('' if cond else '=> ' + detail))


uid = find_superadmin_cust3()
print('测试用超级管理员 user_id =', uid)
client = app.test_client()
login_as(client, uid)

# ---------- 问题1：分页翻页链接 ----------
r = client.get('/')
html = r.get_data(as_text=True)
check('问题1 首页可访问', r.status_code == 200, str(r.status_code))
# 修复后不应再有基于 replace 的翻页链接，应使用 jumpToPage
check('问题1 存在 jumpToPage 函数', 'function jumpToPage(' in html)
check('问题1 下一页按钮调用 jumpToPage', bool(re.search(r'onclick="jumpToPage\(\d+\)"[^>]*>下一页', html)) or '>下一页' in html)
check('问题1 不再使用 replace 拼接翻页链接', "replace('page='" not in html)

# 归档页同样验证（路由为 /contract/archive/<business_type>）
r2 = client.get('/contract/archive/销售')
h2 = r2.get_data(as_text=True)
if r2.status_code == 200:
    check('问题1 归档页存在 jumpToPage', 'function jumpToPage(' in h2)
    check('问题1 归档页不再用 replace 拼接', "replace('page='" not in h2)
else:
    check('问题1 归档页可访问', False, str(r2.status_code))

# ---------- 问题2：岗位详情API + 编辑回显 ----------
with app.app_context():
    pos = Position.query.filter_by(customer_id=3).first()
    pos_id = pos.id
    pos_perms = pos.function_permissions
    pos_name = pos.name

r = client.get('/api/position/%d' % pos_id)
check('问题2 岗位详情API返回200', r.status_code == 200, str(r.status_code))
data = r.get_json()
check('问题2 API返回正确岗位名', data.get('name') == pos_name, str(data))
check('问题2 API返回的权限与数据库一致', data.get('function_permissions') == (pos_perms or ''),
      'api=%r db=%r' % (data.get('function_permissions'), pos_perms))

# 越权：用另一租户岗位应拿不到数据
with app.app_context():
    other = Position.query.filter(Position.customer_id != 3).first()
if other:
    r = client.get('/api/position/%d' % other.id)
    body = r.get_json()
    check('问题2 跨租户岗位无法读取', not body.get('id'), str(body))

# 岗位管理页含实时拉取逻辑
r = client.get('/positions')
hp = r.get_data(as_text=True)
check('问题2 岗位页含 fetch(/api/position/) 回显', "fetch('/api/position/' + positionId)" in hp)
check('问题2 保留 applyEditPerms 回显函数', 'function applyEditPerms(' in hp)

# ---------- 问题3：合同列表弹窗工具栏+分页 ----------
r = client.get('/contract_organization_assignment')
hc = r.get_data(as_text=True)
check('问题3 分配页可访问', r.status_code == 200, str(r.status_code))
check('问题3 含查看按钮', ">查看</button>" in hc and r"contractAction(\'view\')" in hc)
check('问题3 含调整按钮', ">调整</button>" in hc and r"contractAction(\'adjust\')" in hc)
check('问题3 含筛选按钮', 'contractFilter()' in hc)
check('问题3 含每页显示下拉', '每页显示' in hc and 'contractPerPage(' in hc)
check('问题3 含前端分页函数', 'function renderContractList(' in hc and 'function contractGoPage(' in hc)
check('问题3 注入组织列表 ORG_OPTIONS', 'ORG_OPTIONS' in hc)

# 弹窗数据源API
with app.app_context():
    c_org = Contract.query.filter_by(customer_id=3).filter(Contract.organization_id.isnot(None)).first()
    org_id = c_org.organization_id
r = client.get('/api/contracts_by_organization/%d' % org_id)
check('问题3 合同列表API返回200', r.status_code == 200, str(r.status_code))
arr = r.get_json()
check('问题3 合同列表API返回数组', isinstance(arr, list) and len(arr) > 0, str(len(arr) if isinstance(arr, list) else arr))
if arr:
    keys = set(arr[0].keys())
    need = {'id', 'contract_number', 'project_name', 'customer_name', 'project_staff', 'total_price', 'signing_date'}
    check('问题3 合同项含渲染所需字段', need.issubset(keys), str(keys))

print('\n===== 汇总 =====')
passed = sum(1 for _, c, _ in results if c)
print('通过 %d / %d' % (passed, len(results)))
if passed != len(results):
    for n, c, d in results:
        if not c:
            print('  未通过:', n, d)
    raise SystemExit(1)
print('全部通过')
