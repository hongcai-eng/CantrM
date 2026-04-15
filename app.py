from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from datetime import datetime, timedelta
from functools import wraps
import os
import io
import pandas as pd
from models import db, User, TenantCustomer, Organization, Customer, Product, Contract, ContractProduct, Payment, Delivery, Invoice, SysConfig

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contracts.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ── 自定义模板过滤器：去掉浮点数尾部多余的0，如 6.0 → 6，6.5 → 6.5 ──
@app.template_filter('notrailzero')
def notrailzero_filter(val):
    if val is None:
        return ''
    return '{:g}'.format(float(val))


# 模型已移至 models.py


with app.app_context():
    db.create_all()
    # 初始化超级管理员 admin（无租户，可管理所有数据）
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='超级管理员', permissions='all', customer_id=None)
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
    # 新增：初始化 superadmin（总超级管理员，可创建客户超级管理员）
    if not User.query.filter_by(username='superadmin').first():
        sa = User(username='superadmin', role='超级管理员', permissions='all', customer_id=None)
        sa.set_password('654321')
        db.session.add(sa)
        db.session.commit()


@app.context_processor
def inject_company():
    try:
        configs = {c.key: c.value for c in SysConfig.query.all()}
    except Exception:
        configs = {}

    # 默认使用全局配置
    company_name = configs.get('company_name', '')
    company_logo_file = configs.get('company_logo_file', '')

    # 若当前登录用户属于某租户，优先用租户自己的品牌信息
    try:
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user and user.customer_id:
                tenant = TenantCustomer.query.get(user.customer_id)
                if tenant:
                    if tenant.company_name:
                        company_name = tenant.company_name
                    if tenant.logo_file:
                        company_logo_file = tenant.logo_file
    except Exception:
        pass

    current_tenant_name = None
    try:
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user and user.customer_id:
                t = TenantCustomer.query.get(user.customer_id)
                if t:
                    current_tenant_name = t.name
    except Exception:
        pass

    return dict(company_name=company_name, company_logo_file=company_logo_file, current_tenant_name=current_tenant_name)


# ── 辅助：判断当前登录者是否为 superadmin ──
def is_superadmin():
    return session.get('username') == 'superadmin'


# ── 新增：获取当前用户的租户ID ──
def get_current_customer_id():
    """获取当前登录用户的租户客户ID，superadmin返回None"""
    if 'user_id' not in session:
        return None
    user = User.query.get(session['user_id'])
    return user.customer_id if user else None


# ── 新增：判断是否为客户超级管理员 ──
def is_customer_admin():
    """判断当前用户是否为客户超级管理员（admin角色且有customer_id）"""
    if 'user_id' not in session:
        return False
    user = User.query.get(session['user_id'])
    return user and user.role == '超级管理员' and user.customer_id is not None


# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# 权限验证装饰器
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('请先登录', 'warning')
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if user.role == '超级管理员' or user.permissions == 'all':
                return f(*args, **kwargs)
            if user.permissions and permission in user.permissions:
                return f(*args, **kwargs)
            flash('权限不足', 'warning')
            return redirect(url_for('index'))
        return decorated_function
    return decorator


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('登录成功', 'success')
            if username == 'superadmin':
                return redirect(url_for('tenant_management'))
            return redirect(url_for('index'))
        flash('用户名或密码错误', 'warning')
    return render_template('login.html')


@app.route('/api/user_branding')
def api_user_branding():
    """根据用户名返回该用户所属租户的品牌信息（公司名称+Logo），登录页用"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'company_name': '', 'logo_url': ''})

    user = User.query.filter_by(username=username).first()
    if not user or not user.customer_id:
        # superadmin 或未关联租户的用户：返回全局配置
        configs = {c.key: c.value for c in SysConfig.query.all()}
        logo_file = configs.get('company_logo_file', '')
        logo_url = f'/static/{logo_file}' if logo_file else ''
        return jsonify({
            'company_name': configs.get('company_name', ''),
            'logo_url': logo_url
        })

    tenant = TenantCustomer.query.get(user.customer_id)
    if not tenant:
        return jsonify({'company_name': '', 'logo_url': ''})

    # 租户有自己的品牌信息则用自己的，否则回退到全局配置
    if tenant.company_name or tenant.logo_file:
        logo_url = f'/static/{tenant.logo_file}' if tenant.logo_file else ''
        return jsonify({
            'company_name': tenant.company_name or '',
            'logo_url': logo_url
        })
    else:
        configs = {c.key: c.value for c in SysConfig.query.all()}
        logo_file = configs.get('company_logo_file', '')
        logo_url = f'/static/{logo_file}' if logo_file else ''
        return jsonify({
            'company_name': configs.get('company_name', ''),
            'logo_url': logo_url
        })


@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    # 新增：superadmin 不应访问合同列表，直接重定向到租户管理
    if is_superadmin():
        flash('总超级管理员请在租户管理界面操作，不可查看租户合同数据', 'warning')
        return redirect(url_for('tenant_management'))

    from sqlalchemy import func
    query = Contract.query

    # 新增：数据隔离 - 非superadmin只能看到自己租户的数据
    customer_id = get_current_customer_id()
    if customer_id is not None:
        query = query.filter(Contract.customer_id == customer_id)

    # 原有筛选条件
    if request.args.get('project_staff'):
        query = query.filter(Contract.project_staff.like(f"%{request.args.get('project_staff')}%"))
    if request.args.get('customer_name'):
        query = query.filter(Contract.customer_name.like(f"%{request.args.get('customer_name')}%"))

    # 修改：合同类型筛选 - 使用 JOIN 查询 ContractProduct 表
    if request.args.get('contract_type'):
        contract_type = request.args.get('contract_type')
        # 使用 JOIN 确保只查询当前 query 范围内的合同
        query = query.join(ContractProduct, Contract.id == ContractProduct.contract_id).filter(
            ContractProduct.contract_type == contract_type
        ).distinct()

    if request.args.get('status'):
        query = query.filter(Contract.status == request.args.get('status'))
    # 新增：业务类型筛选
    if request.args.get('business_type'):
        query = query.filter(Contract.business_type == request.args.get('business_type'))
    # 新增：签订年份筛选
    if request.args.get('signing_year'):
        query = query.filter(func.strftime('%Y', Contract.signing_date) == request.args.get('signing_year'))

    contracts = query.order_by(Contract.created_at.desc()).all()

    # 发票状态筛选
    if request.args.get('invoice_status'):
        filtered = []
        for contract in contracts:
            has_issued = any(i.invoice_status == '已开具' for i in contract.invoices)
            if request.args.get('invoice_status') == '已开具' and has_issued:
                filtered.append(contract)
            elif request.args.get('invoice_status') == '未开具' and not has_issued:
                filtered.append(contract)
        contracts = filtered

    alerts = []
    today = datetime.now().date()

    for contract in contracts:
        if contract.status == '进行中':
            last_payment = Payment.query.filter_by(contract_id=contract.id).order_by(Payment.payment_date.desc()).first()
            if last_payment:
                days_since = (today - last_payment.payment_date).days
                if days_since > 30:
                    alerts.append(f"{contract.project_name} - 距上次收付款已{days_since}天")

    # 预警筛选
    if request.args.get('alert') == 'yes':
        alert_contracts = [a.split(' - ')[0] for a in alerts]
        contracts = [c for c in contracts if c.project_name in alert_contracts]

    # 新增：获取可用年份列表（用于年份筛选下拉）
    years_raw = db.session.query(func.strftime('%Y', Contract.signing_date)).filter(
        Contract.signing_date.isnot(None)
    ).distinct().order_by(func.strftime('%Y', Contract.signing_date).desc()).all()
    available_years = [int(y[0]) for y in years_raw if y[0]]

    # 筛选结果统计汇总
    stats = {
        'count': len(contracts),
        'total_price': sum(c.total_price for c in contracts),
        'total_paid': sum(c.get_total_paid() for c in contracts),
        'total_unpaid': sum(c.get_unpaid_amount() for c in contracts),
        'total_invoiced': sum(c.get_total_invoiced() for c in contracts),
        'total_uninvoiced': sum(c.get_uninvoiced_amount() for c in contracts),
    }

    return render_template('index.html', contracts=contracts, alerts=alerts,
                           available_years=available_years, stats=stats)


# ── 新增：合同列表导出 Excel ──
@app.route('/contract/export')
@login_required
def export_contracts():
    from sqlalchemy import func
    query = Contract.query

    # 新增：租户数据隔离
    customer_id = get_current_customer_id()
    if customer_id is not None:
        query = query.filter(Contract.customer_id == customer_id)

    if request.args.get('project_staff'):
        query = query.filter(Contract.project_staff.like(f"%{request.args.get('project_staff')}%"))
    if request.args.get('customer_name'):
        query = query.filter(Contract.customer_name.like(f"%{request.args.get('customer_name')}%"))

    # 修改：合同类型筛选 - 使用 JOIN 查询 ContractProduct 表
    if request.args.get('contract_type'):
        contract_type = request.args.get('contract_type')
        query = query.join(ContractProduct, Contract.id == ContractProduct.contract_id).filter(
            ContractProduct.contract_type == contract_type
        ).distinct()

    if request.args.get('status'):
        query = query.filter(Contract.status == request.args.get('status'))
    if request.args.get('business_type'):
        query = query.filter(Contract.business_type == request.args.get('business_type'))
    if request.args.get('signing_year'):
        query = query.filter(func.strftime('%Y', Contract.signing_date) == request.args.get('signing_year'))

    contracts = query.order_by(Contract.created_at.desc()).all()

    data = []
    for c in contracts:
        products = ContractProduct.query.filter_by(contract_id=c.id).all()
        if products:
            for cp in products:
                data.append({
                    '合同编号': c.contract_number or '',
                    '客户名称': c.customer_name,
                    '项目名称': c.project_name,
                    '产品名称': cp.product_name or '',
                    '型号': cp.model or '',
                    '单位': cp.unit or '',
                    '数量': cp.quantity,
                    '单价': cp.unit_price,
                    '合同总价': c.total_price,
                    '发票税率': cp.tax_rate,
                    '合同类型': c.contract_type or '',
                    '业务类型': c.business_type or '',
                    '项目负责人': c.project_staff or '',
                    '销售人员': c.sales_staff or '',
                    '签订日期': str(c.signing_date) if c.signing_date else '',
                    '状态': c.status or '',
                    '已收付款': c.get_total_paid(),
                    '未收付款': c.get_unpaid_amount(),
                    '已开票': c.get_total_invoiced(),
                    '未开票': c.get_uninvoiced_amount(),
                })
        else:
            data.append({
                '合同编号': c.contract_number or '',
                '客户名称': c.customer_name,
                '项目名称': c.project_name,
                '产品名称': c.product_name or '',
                '型号': c.model or '',
                '单位': c.unit or '',
                '数量': c.quantity,
                '单价': c.unit_price,
                '合同总价': c.total_price,
                '发票税率': c.tax_rate,
                '合同类型': c.contract_type or '',
                '业务类型': c.business_type or '',
                '项目负责人': c.project_staff or '',
                '销售人员': c.sales_staff or '',
                '签订日期': str(c.signing_date) if c.signing_date else '',
                '状态': c.status or '',
                '已收付款': c.get_total_paid(),
                '未收付款': c.get_unpaid_amount(),
                '已开票': c.get_total_invoiced(),
                '未开票': c.get_uninvoiced_amount(),
            })

    # 按指定列顺序输出
    columns = ['合同编号', '客户名称', '项目名称', '产品名称', '型号', '单位', '数量', '单价',
               '合同总价', '发票税率', '合同类型', '业务类型', '项目负责人', '销售人员',
               '签订日期', '状态', '已收付款', '未收付款', '已开票', '未开票']
    df = pd.DataFrame(data, columns=columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='合同列表')
    buf.seek(0)
    filename = f"合同导出_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    return send_file(buf, download_name=filename, as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/users')
@login_required
def users():
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))

    # 新增：superadmin 不应查看租户人员，重定向到租户管理
    if is_superadmin():
        flash('请在租户管理界面管理各租户的用户', 'warning')
        return redirect(url_for('tenant_management'))

    # 新增：客户超级管理员只能看到自己租户下的用户
    customer_id = get_current_customer_id()
    if customer_id is not None:
        users = User.query.filter(User.customer_id == customer_id).all()
    else:
        # superadmin可以看到所有用户
        tenant_id = request.args.get('tenant_id')
        if tenant_id:
            users = User.query.filter(User.customer_id == int(tenant_id)).all()
        else:
            users = User.query.all()

    # 新增：获取租户客户列表（仅superadmin可见）
    tenants = TenantCustomer.query.all() if is_superadmin() else []

    return render_template('users.html', users=users, is_superadmin=is_superadmin(),
                         is_customer_admin=is_customer_admin(), tenants=tenants)


# 新增：租户管理路由（仅superadmin可访问）
@app.route('/tenants')
@login_required
def tenant_management():
    if not is_superadmin():
        flash('权限不足：只有总超级管理员可以管理租户', 'warning')
        return redirect(url_for('index'))
    tenants = TenantCustomer.query.order_by(TenantCustomer.created_at.desc()).all()
    return render_template('tenant_management.html', tenants=tenants)


@app.route('/tenant/<int:tenant_id>/users')
@login_required
def tenant_users(tenant_id):
    """superadmin 查看某租户的用户列表"""
    if not is_superadmin():
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    tenant = TenantCustomer.query.get_or_404(tenant_id)
    users = User.query.filter_by(customer_id=tenant_id).all()
    return render_template('tenant_users.html', tenant=tenant, users=users)



@app.route('/tenant/create', methods=['POST'])
@login_required
def create_tenant():
    if not is_superadmin():
        flash('权限不足', 'warning')
        return redirect(url_for('index'))

    tenant_name = request.form['tenant_name']
    description = request.form.get('description', '')
    admin_username = request.form['admin_username']
    admin_password = request.form['admin_password']
    admin_role = request.form.get('admin_role', '超级管理员')
    selected_perms = request.form.getlist('permissions')
    if selected_perms:
        permissions_str = ','.join(selected_perms)
    else:
        permissions_str = 'all'

    # 检查租户名称是否重复
    if TenantCustomer.query.filter_by(name=tenant_name).first():
        flash('租户名称已存在', 'warning')
        return redirect(url_for('tenant_management'))

    # 检查管理员账号是否重复
    existing_user = User.query.filter_by(username=admin_username).first()
    if existing_user:
        # 如果该账号关联的租户已不存在（孤儿账号），自动清除并允许继续
        if existing_user.customer_id is not None and TenantCustomer.query.get(existing_user.customer_id) is None:
            db.session.delete(existing_user)
            db.session.flush()
        else:
            flash(f'管理员账号"{admin_username}"已存在，请换一个账号名称', 'warning')
            return redirect(url_for('tenant_management'))

    # 创建租户
    tenant = TenantCustomer(name=tenant_name, description=description)
    db.session.add(tenant)
    db.session.flush()

    # 创建该租户的管理员（角色和权限由表单指定）
    admin = User(
        username=admin_username,
        role=admin_role,
        permissions=permissions_str,
        customer_id=tenant.id
    )
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()

    flash(f'租户"{tenant_name}"创建成功，管理员账号：{admin_username}', 'success')
    return redirect(url_for('tenant_management'))


# 新增：设置租户品牌信息（公司名称+Logo）
@app.route('/tenant/<int:tenant_id>/branding', methods=['POST'])
@login_required
def tenant_branding(tenant_id):
    if not is_superadmin():
        flash('权限不足', 'warning')
        return redirect(url_for('index'))

    tenant = TenantCustomer.query.get_or_404(tenant_id)
    tenant.company_name = request.form.get('company_name', '').strip()

    # 处理 Logo 文件上传
    if 'logo_file' in request.files:
        f = request.files['logo_file']
        if f.filename:
            ext = os.path.splitext(f.filename)[1]
            logo_filename = f'tenant_{tenant_id}_logo{ext}'
            f.save(os.path.join('static', logo_filename))
            tenant.logo_file = logo_filename

    db.session.commit()
    flash(f'租户"{tenant.name}"的品牌信息已更新', 'success')
    return redirect(url_for('tenant_management'))


@app.route('/user/<int:id>/reset_password', methods=['POST'])
@login_required
def reset_user_password(id):
    """superadmin 重置租户用户密码"""
    if not is_superadmin():
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    user.set_password(request.form['password'])
    db.session.commit()
    flash(f'用户"{user.username}"密码已重置', 'success')
    return redirect(url_for('tenant_users', tenant_id=user.customer_id))



@app.route('/tenant/<int:tenant_id>/edit', methods=['POST'])
@login_required
def tenant_edit(tenant_id):
    if not is_superadmin():
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    tenant = TenantCustomer.query.get_or_404(tenant_id)
    tenant.name = request.form.get('tenant_name', tenant.name).strip()
    tenant.description = request.form.get('description', tenant.description)

    # 新增：支持修改管理员账号和密码
    new_username = request.form.get('admin_username', '').strip()
    new_password = request.form.get('admin_password', '').strip()
    if new_username or new_password:
        admin = User.query.filter_by(customer_id=tenant_id).first()
        if admin:
            if new_username and new_username != admin.username:
                if User.query.filter_by(username=new_username).first():
                    flash(f'账号"{new_username}"已存在', 'warning')
                    return redirect(url_for('tenant_management'))
                admin.username = new_username
            if new_password:
                admin.set_password(new_password)

    db.session.commit()
    flash('租户信息已更新', 'success')
    return redirect(url_for('tenant_management'))


@app.route('/tenant/<int:tenant_id>/delete', methods=['POST'])
@login_required
def tenant_delete(tenant_id):
    if not is_superadmin():
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    tenant = TenantCustomer.query.get_or_404(tenant_id)
    name = tenant.name
    User.query.filter_by(customer_id=tenant_id).delete(synchronize_session='fetch')
    db.session.flush()
    db.session.delete(tenant)
    db.session.commit()
    flash(f'租户"{name}"已删除', 'success')
    return redirect(url_for('tenant_management'))


# ========== 组织结构管理 ==========

@app.route('/organizations')
@login_required
def organizations():
    """组织结构列表（客户超级管理员可访问）"""
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))

    customer_id = get_current_customer_id()
    if customer_id is None:
        flash('superadmin 无需管理组织结构', 'warning')
        return redirect(url_for('index'))

    # 获取当前租户的所有组织（树形结构）
    orgs = Organization.query.filter_by(customer_id=customer_id).order_by(Organization.created_at).all()

    # 获取当前租户的所有用户
    users = User.query.filter_by(customer_id=customer_id).all()

    return render_template('organizations.html', organizations=orgs, users=users)


@app.route('/organization/create', methods=['POST'])
@login_required
def create_organization():
    """创建组织"""
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))

    customer_id = get_current_customer_id()
    if customer_id is None:
        flash('superadmin 无需创建组织', 'warning')
        return redirect(url_for('index'))

    name = request.form['name']
    description = request.form.get('description', '')
    parent_id = request.form.get('parent_id')

    if parent_id and parent_id.strip():
        parent_id = int(parent_id)
    else:
        parent_id = None

    org = Organization(
        name=name,
        description=description,
        parent_id=parent_id,
        customer_id=customer_id
    )
    db.session.add(org)
    db.session.commit()

    flash(f'组织"{name}"创建成功', 'success')
    return redirect(url_for('organizations'))


@app.route('/organization/<int:org_id>/edit', methods=['POST'])
@login_required
def edit_organization(org_id):
    """编辑组织"""
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))

    customer_id = get_current_customer_id()
    org = Organization.query.get_or_404(org_id)

    # 验证权限：只能编辑自己租户的组织
    if org.customer_id != customer_id:
        flash('权限不足', 'warning')
        return redirect(url_for('organizations'))

    org.name = request.form['name']
    org.description = request.form.get('description', '')
    parent_id = request.form.get('parent_id')

    if parent_id and parent_id.strip():
        org.parent_id = int(parent_id)
    else:
        org.parent_id = None

    db.session.commit()
    flash(f'组织"{org.name}"已更新', 'success')
    return redirect(url_for('organizations'))


@app.route('/organization/<int:org_id>/delete', methods=['POST'])
@login_required
def delete_organization(org_id):
    """删除组织"""
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))

    customer_id = get_current_customer_id()
    org = Organization.query.get_or_404(org_id)

    # 验证权限
    if org.customer_id != customer_id:
        flash('权限不足', 'warning')
        return redirect(url_for('organizations'))

    # 检查是否有子组织
    if org.children:
        flash('该组织下有子组织，无法删除', 'warning')
        return redirect(url_for('organizations'))

    # 检查是否有成员
    if org.members:
        flash('该组织下有成员，无法删除', 'warning')
        return redirect(url_for('organizations'))

    db.session.delete(org)
    db.session.commit()
    flash('组织已删除', 'success')
    return redirect(url_for('organizations'))


@app.route('/organization/transfer', methods=['POST'])
@login_required
def transfer_user():
    """人员调动（调入/调出组织）"""
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))

    customer_id = get_current_customer_id()
    user_id = int(request.form['user_id'])
    target_org_id = request.form.get('target_org_id')

    user = User.query.get_or_404(user_id)

    # 验证权限：只能调动自己租户的用户
    if user.customer_id != customer_id:
        flash('权限不足', 'warning')
        return redirect(url_for('organizations'))

    if target_org_id and target_org_id.strip():
        target_org_id = int(target_org_id)
        # 验证目标组织属于当前租户
        target_org = Organization.query.get(target_org_id)
        if not target_org or target_org.customer_id != customer_id:
            flash('目标组织不存在或权限不足', 'warning')
            return redirect(url_for('organizations'))
        user.organization_id = target_org_id
        flash(f'用户"{user.username}"已调入组织"{target_org.name}"', 'success')
    else:
        # 调出组织（设为 None）
        user.organization_id = None
        flash(f'用户"{user.username}"已调出组织', 'success')

    db.session.commit()
    return redirect(url_for('organizations'))


@app.route('/user/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    if request.method == 'POST':
        role = request.form['role']
        # 只有 superadmin 可以创建超级管理员角色用户
        if role == '超级管理员' and not is_superadmin():
            flash('权限不足：只有 superadmin 可以创建超级管理员账户', 'warning')
            return redirect(url_for('users'))

        # 新增：客户超级管理员创建的用户自动继承其customer_id
        customer_id = get_current_customer_id()
        if customer_id is not None and role == '超级管理员':
            flash('客户超级管理员不能创建超级管理员账户', 'warning')
            return redirect(url_for('users'))

        # superadmin创建客户超级管理员时需要指定租户
        if is_superadmin() and role == '超级管理员' and request.form.get('customer_id'):
            customer_id = int(request.form['customer_id'])

        user = User(
            username=request.form['username'],
            role=role,
            permissions=','.join(request.form.getlist('permissions')),
            customer_id=customer_id
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('用户创建成功', 'success')
        return redirect(url_for('users'))

    tenants = TenantCustomer.query.all() if is_superadmin() else []
    return render_template('user_form.html', is_superadmin=is_superadmin(),
                         is_customer_admin=is_customer_admin(), tenants=tenants)


@app.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    # 非 superadmin 不能编辑超级管理员账户
    if user.role == '超级管理员' and not is_superadmin():
        flash('权限不足：只有 superadmin 可以修改超级管理员账户', 'warning')
        return redirect(url_for('users'))
    # superadmin 自身不可修改角色
    if user.username == 'superadmin' and not is_superadmin():
        flash('权限不足', 'warning')
        return redirect(url_for('users'))
    if request.method == 'POST':
        new_role = request.form['role']
        if new_role == '超级管理员' and not is_superadmin():
            flash('权限不足：只有 superadmin 可以设置超级管理员角色', 'warning')
            return redirect(url_for('users'))
        user.username = request.form['username']
        user.role = new_role
        user.permissions = ','.join(request.form.getlist('permissions'))
        if request.form.get('password'):
            user.set_password(request.form['password'])
        db.session.commit()
        flash('用户更新成功', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', user=user, is_superadmin=is_superadmin())


@app.route('/user/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    if user.username in ('admin', 'superadmin'):
        flash('不能删除系统内置管理员账户', 'warning')
        return redirect(url_for('users'))
    # 非 superadmin 不能删除超级管理员用户
    if user.role == '超级管理员' and not is_superadmin():
        flash('权限不足：只有 superadmin 可以删除超级管理员账户', 'warning')
        return redirect(url_for('users'))
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功', 'success')
    return redirect(url_for('users'))


@app.route('/customers')
@login_required
def customers():
    query = Customer.query

    # 新增：数据隔离
    customer_id = get_current_customer_id()
    if customer_id is not None:
        query = query.filter(Customer.customer_id == customer_id)

    if request.args.get('name'):
        query = query.filter(Customer.name.like(f"%{request.args.get('name')}%"))
    if request.args.get('province'):
        query = query.filter(Customer.province.like(f"%{request.args.get('province')}%"))
    customers = query.order_by(Customer.province, Customer.name).all()
    return render_template('customers.html', customers=customers)


@app.route('/customer/new', methods=['POST'])
@login_required
@permission_required('增加')
def new_customer():
    customer = Customer(
        name=request.form['name'],
        province=request.form.get('province'),
        region=request.form.get('region'),
        credit_code=request.form.get('credit_code'),
        customer_id=get_current_customer_id()  # 新增：自动关联租户
    )
    db.session.add(customer)
    db.session.commit()
    flash('客户添加成功', 'success')
    return redirect(url_for('customers'))


@app.route('/customer/<int:id>/edit', methods=['POST'])
@login_required
@permission_required('修改')
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    customer.name = request.form['name']
    customer.province = request.form.get('province')
    customer.region = request.form.get('region')
    customer.credit_code = request.form.get('credit_code')
    db.session.commit()
    flash('客户更新成功', 'success')
    return redirect(url_for('customers'))


@app.route('/customer/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('删除')
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash('客户删除成功', 'success')
    return redirect(url_for('customers'))


@app.route('/api/customers/search')
@login_required
def search_customers():
    query = request.args.get('q', '')
    q = Customer.query.filter(Customer.name.like(f'%{query}%'))

    # 新增：数据隔离
    customer_id = get_current_customer_id()
    if customer_id is not None:
        q = q.filter(Customer.customer_id == customer_id)

    customers = q.limit(10).all()
    return jsonify([{'id': c.id, 'name': c.name, 'province': c.province} for c in customers])


# ── 新增：项目负责人关键字搜索（从合同记录中提取，支持逗号分隔的多人） ──
@app.route('/api/project_staff/search')
@login_required
def search_project_staff():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    # 新增：租户数据隔离
    q = db.session.query(Contract.project_staff)
    customer_id = get_current_customer_id()
    if customer_id is not None:
        q = q.filter(Contract.customer_id == customer_id)

    rows = q.filter(
        Contract.project_staff.isnot(None),
        Contract.project_staff != '',
        Contract.project_staff.like(f'%{query}%')
    ).all()
    names = set()
    for (staff_str,) in rows:
        if staff_str:
            for name in staff_str.split(','):
                name = name.strip()
                if name and query.lower() in name.lower():
                    names.add(name)
    return jsonify(sorted(list(names))[:10])


@app.route('/products')
@login_required
def products():
    query = Product.query

    # 新增：数据隔离
    customer_id = get_current_customer_id()
    if customer_id is not None:
        query = query.filter(Product.customer_id == customer_id)

    if request.args.get('name'):
        query = query.filter(Product.name.like(f"%{request.args.get('name')}%"))
    if request.args.get('category'):
        query = query.filter(Product.category == request.args.get('category'))
    if request.args.get('model'):
        query = query.filter(Product.model.like(f"%{request.args.get('model')}%"))
    products = query.order_by(Product.category, Product.name).all()
    return render_template('products.html', products=products)


@app.route('/product/new', methods=['POST'])
@login_required
@permission_required('增加')
def new_product():
    product = Product(
        name=request.form['name'],
        category=request.form['category'],
        model=request.form.get('model'),
        unit=request.form.get('unit'),
        # 新增字段
        tax_rate=float(request.form['tax_rate']) if request.form.get('tax_rate') else None,
        ref_quantity=float(request.form['ref_quantity']) if request.form.get('ref_quantity') else None,
        ref_unit_price=float(request.form['ref_unit_price']) if request.form.get('ref_unit_price') else None,
        customer_id=get_current_customer_id()  # 新增：自动关联租户
    )
    db.session.add(product)
    db.session.commit()
    flash('产品添加成功', 'success')
    return redirect(url_for('products'))


@app.route('/product/<int:id>/edit', methods=['POST'])
@login_required
@permission_required('修改')
def edit_product(id):
    product = Product.query.get_or_404(id)
    product.name = request.form['name']
    product.category = request.form['category']
    product.model = request.form.get('model')
    product.unit = request.form.get('unit')
    # 新增字段
    product.tax_rate = float(request.form['tax_rate']) if request.form.get('tax_rate') else None
    product.ref_quantity = float(request.form['ref_quantity']) if request.form.get('ref_quantity') else None
    product.ref_unit_price = float(request.form['ref_unit_price']) if request.form.get('ref_unit_price') else None
    db.session.commit()
    flash('产品更新成功', 'success')
    return redirect(url_for('products'))


@app.route('/product/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('删除')
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('产品删除成功', 'success')
    return redirect(url_for('products'))


@app.route('/api/products/search')
@login_required
def search_products():
    query = request.args.get('q', '')
    q = Product.query.filter(Product.name.like(f'%{query}%'))

    # 新增：数据隔离
    customer_id = get_current_customer_id()
    if customer_id is not None:
        q = q.filter(Product.customer_id == customer_id)

    products = q.limit(10).all()
    return jsonify([{
        'id': p.id, 'name': p.name, 'model': p.model, 'unit': p.unit,
        'tax_rate': p.tax_rate, 'ref_quantity': p.ref_quantity, 'ref_unit_price': p.ref_unit_price
    } for p in products])


# ── 新增：自动更新合同状态（已收付款>=合同总价 且 已开票>=合同总价 则标记已完结）──
def auto_update_contract_status(contract):
    """检查合同是否满足完结条件，并自动更新状态"""
    total_paid = contract.get_total_paid()
    total_invoiced = contract.get_total_invoiced()
    if contract.total_price > 0 and total_paid >= contract.total_price and total_invoiced >= contract.total_price:
        if contract.status != '已完结':
            contract.status = '已完结'
    # 注意：不自动从"已完结"回退到"进行中"，避免误操作


# ── 新增：将合同中的产品名称同步到 Product 表（新产品则创建，已有则跳过）──
def sync_products_to_table(product_names, models, units, tax_rates, customer_id):
    """将新建/编辑合同中的产品名称同步到产品管理表"""
    for i, pname in enumerate(product_names):
        pname = pname.strip() if pname else ''
        if not pname:
            continue
        existing = Product.query.filter_by(name=pname, customer_id=customer_id).first()
        if not existing:
            model_val = models[i].strip() if i < len(models) and models[i] else None
            unit_val = units[i].strip() if i < len(units) and units[i] else None
            tax_val = None
            if i < len(tax_rates) and tax_rates[i]:
                try:
                    tax_val = float(tax_rates[i])
                except (ValueError, TypeError):
                    tax_val = None
            new_product = Product(
                name=pname,
                category='其他',  # 默认分类，用户可在产品管理页修改
                model=model_val or None,
                unit=unit_val or None,
                tax_rate=tax_val,
                customer_id=customer_id
            )
            db.session.add(new_product)


@app.route('/statistics')
@login_required
def statistics():
    from sqlalchemy import func
    q = Contract.query

    # 新增：租户数据隔离
    customer_id = get_current_customer_id()
    if customer_id is not None:
        q = q.filter(Contract.customer_id == customer_id)
    # 筛选
    f_staff = request.args.get('f_staff', '')
    f_customer = request.args.get('f_customer', '')
    f_type = request.args.get('f_type', '')
    f_business = request.args.get('f_business', '')
    f_status = request.args.get('f_status', '')
    f_year = request.args.get('f_year', '')   # 新增：年份筛选
    if f_staff:
        q = q.filter(Contract.project_staff.like(f'%{f_staff}%'))
    if f_customer:
        q = q.filter(Contract.customer_name.like(f'%{f_customer}%'))
    if f_type:
        q = q.filter(Contract.contract_type == f_type)
    if f_business:
        q = q.filter(Contract.business_type == f_business)
    if f_status:
        q = q.filter(Contract.status == f_status)
    if f_year:
        q = q.filter(func.strftime('%Y', Contract.signing_date) == f_year)

    # 新增：f_sheets 参数——控制页面上显示哪些维度的统计表格
    # 默认全部显示；用户勾选后只显示选中的
    # 注意：表单 checkbox 以多值形式发送（f_sheets=staff&f_sheets=customer），用 getlist 读取
    all_sheets = ['staff', 'customer', 'type', 'business', 'status']
    selected_sheets = [s for s in request.args.getlist('f_sheets') if s in all_sheets]
    if not selected_sheets:
        selected_sheets = all_sheets  # 默认全部

    stats = {}
    if 'staff' in selected_sheets:
        stats['by_staff'] = q.with_entities(Contract.project_staff, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.project_staff).all()
    if 'customer' in selected_sheets:
        stats['by_customer'] = q.with_entities(Contract.customer_name, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.customer_name).all()
    if 'type' in selected_sheets:
        stats['by_type'] = q.with_entities(Contract.contract_type, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.contract_type).all()
    if 'status' in selected_sheets:
        stats['by_status'] = q.with_entities(Contract.status, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.status).all()
    if 'business' in selected_sheets:
        stats['by_business'] = q.with_entities(Contract.business_type, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.business_type).all()

    filters = {'f_staff': f_staff, 'f_customer': f_customer, 'f_type': f_type,
               'f_business': f_business, 'f_status': f_status, 'f_year': f_year}

    # 新增：获取可用年份列表
    years_raw = db.session.query(func.strftime('%Y', Contract.signing_date)).filter(
        Contract.signing_date.isnot(None)
    ).distinct().order_by(func.strftime('%Y', Contract.signing_date).desc()).all()
    available_years = [int(y[0]) for y in years_raw if y[0]]

    return render_template('statistics.html', stats=stats, filters=filters,
                           available_years=available_years, selected_sheets=selected_sheets)


# ── 新增：统计分析导出 Excel ──
@app.route('/statistics/export')
@login_required
def export_statistics():
    from sqlalchemy import func
    q = Contract.query

    # 新增：租户数据隔离
    customer_id = get_current_customer_id()
    if customer_id is not None:
        q = q.filter(Contract.customer_id == customer_id)
    f_staff = request.args.get('f_staff', '')
    f_customer = request.args.get('f_customer', '')
    f_type = request.args.get('f_type', '')
    f_business = request.args.get('f_business', '')
    f_status = request.args.get('f_status', '')
    f_year = request.args.get('f_year', '')
    if f_staff:
        q = q.filter(Contract.project_staff.like(f'%{f_staff}%'))
    if f_customer:
        q = q.filter(Contract.customer_name.like(f'%{f_customer}%'))
    if f_type:
        q = q.filter(Contract.contract_type == f_type)
    if f_business:
        q = q.filter(Contract.business_type == f_business)
    if f_status:
        q = q.filter(Contract.status == f_status)
    if f_year:
        q = q.filter(func.strftime('%Y', Contract.signing_date) == f_year)

    # 按勾选的sheets参数决定导出哪些sheet
    sheets = request.args.get('sheets', 'staff,customer,type,business,status').split(',')
    layout = request.args.get('layout', 'vertical')  # vertical 或 horizontal

    # 收集各维度数据
    blocks = []  # [(col_name, data), ...]
    if 'staff' in sheets:
        blocks.append(('项目负责人', q.with_entities(Contract.project_staff, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.project_staff).all()))
    if 'customer' in sheets:
        blocks.append(('客户名称', q.with_entities(Contract.customer_name, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.customer_name).all()))
    if 'type' in sheets:
        blocks.append(('合同类型', q.with_entities(Contract.contract_type, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.contract_type).all()))
    if 'business' in sheets:
        blocks.append(('业务类型', q.with_entities(Contract.business_type, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.business_type).all()))
    if 'status' in sheets:
        blocks.append(('履约状态', q.with_entities(Contract.status, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.status).all()))

    import openpyxl
    buf = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '统计分析'

    if layout == 'multisheet':
        # 方案C：每个维度单独一个 sheet
        first = True
        for col_name, data in blocks:
            ws = wb.active if first else wb.create_sheet()
            ws.title = col_name
            first = False
            ws.cell(row=1, column=1, value=col_name)
            ws.cell(row=1, column=2, value='合同数量')
            ws.cell(row=1, column=3, value='合同总额')
            for i, r in enumerate(data, start=2):
                ws.cell(row=i, column=1, value=r[0])
                ws.cell(row=i, column=2, value=r[1])
                ws.cell(row=i, column=3, value=float(r[2]) if r[2] else 0)
    elif layout == 'horizontal':
        # 方案B：横向排列，每维度占3列，列间空1列
        col = 1
        for col_name, data in blocks:
            ws.cell(row=1, column=col, value=col_name)
            ws.cell(row=1, column=col+1, value='合同数量')
            ws.cell(row=1, column=col+2, value='合同总额')
            for i, r in enumerate(data, start=2):
                ws.cell(row=i, column=col, value=r[0])
                ws.cell(row=i, column=col+1, value=r[1])
                ws.cell(row=i, column=col+2, value=float(r[2]) if r[2] else 0)
            col += 4  # 3列数据 + 1列空白
    else:
        # 方案A：纵向排列
        row = 1
        for col_name, data in blocks:
            ws.cell(row=row, column=1, value=col_name)
            ws.cell(row=row, column=2, value='合同数量')
            ws.cell(row=row, column=3, value='合同总额')
            row += 1
            for r in data:
                ws.cell(row=row, column=1, value=r[0])
                ws.cell(row=row, column=2, value=r[1])
                ws.cell(row=row, column=3, value=float(r[2]) if r[2] else 0)
                row += 1
            row += 1  # 空行分隔

    wb.save(buf)
    buf.seek(0)
    filename = f"统计导出_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    return send_file(buf, download_name=filename, as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/contract/new', methods=['GET', 'POST'])
@login_required
@permission_required('增加')
def new_contract():
    if request.method == 'POST':
        # 新增：获取当前用户的租户ID
        customer_id = get_current_customer_id()

        # 创建合同主记录
        contract = Contract(
            contract_number=request.form.get('contract_number'),
            customer_name=request.form['customer_name'],
            project_name=request.form['project_name'],
            total_price=float(request.form['total_price']),
            contract_type=request.form.get('contract_type'),
            project_staff=request.form.get('project_staff'),
            sales_staff=request.form.get('sales_staff'),
            business_type=request.form.get('business_type', '销售'),
            signing_date=datetime.strptime(request.form['signing_date'], '%Y-%m-%d').date() if request.form.get('signing_date') else None,
            customer_id=customer_id  # 新增：关联租户
        )

        # 处理合同文件上传
        if 'contract_file' in request.files:
            file = request.files['contract_file']
            if file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                contract.file_path = filename

        # 自动同步客户信息
        if not Customer.query.filter_by(name=contract.customer_name, customer_id=customer_id).first():
            db.session.add(Customer(name=contract.customer_name, customer_id=customer_id))

        db.session.add(contract)
        db.session.flush()  # 获取contract.id

        # 新增：处理多产品数据
        product_names = request.form.getlist('products[product_name][]')
        contract_types = request.form.getlist('products[contract_type][]')
        product_types = request.form.getlist('products[product_type][]')
        models = request.form.getlist('products[model][]')
        units = request.form.getlist('products[unit][]')
        quantities = request.form.getlist('products[quantity][]')
        unit_prices = request.form.getlist('products[unit_price][]')
        subtotals = request.form.getlist('products[subtotal][]')
        tax_rates = request.form.getlist('products[tax_rate][]')

        # 保存多个产品到 ContractProduct 表
        for i in range(len(product_names)):
            if product_names[i].strip():  # 只保存非空产品
                cp = ContractProduct(
                    contract_id=contract.id,
                    product_name=product_names[i].strip() or None,
                    contract_type=contract_types[i] if i < len(contract_types) else None,
                    product_type=product_types[i].strip() if i < len(product_types) and product_types[i].strip() else None,
                    model=models[i].strip() if i < len(models) and models[i].strip() else None,
                    unit=units[i].strip() if i < len(units) and units[i].strip() else None,
                    quantity=float(quantities[i]) if i < len(quantities) and quantities[i] else None,
                    unit_price=float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else None,
                    subtotal=float(subtotals[i]) if i < len(subtotals) and subtotals[i] else None,
                    tax_rate=float(tax_rates[i]) if i < len(tax_rates) and tax_rates[i] else None
                )
                db.session.add(cp)

        # 新增：将产品名称同步到产品管理表（仅新产品）
        sync_products_to_table(product_names, models, units, tax_rates, customer_id)

        db.session.commit()
        flash('合同创建成功', 'success')
        return redirect(url_for('index'))

    # GET请求：数据隔离
    customer_id = get_current_customer_id()
    if customer_id is not None:
        customers_list = Customer.query.filter_by(customer_id=customer_id).order_by(Customer.name).all()
        products_list = Product.query.filter_by(customer_id=customer_id).order_by(Product.name).all()
    else:
        customers_list = Customer.query.order_by(Customer.name).all()
        products_list = Product.query.order_by(Product.name).all()

    return render_template('contract_form.html', customers_list=customers_list, products_list=products_list)


@app.route('/contract/<int:id>')
def view_contract(id):
    contract = Contract.query.get_or_404(id)
    return render_template('contract_detail.html', contract=contract)


@app.route('/contract/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('删除')
def delete_contract(id):
    contract = Contract.query.get_or_404(id)
    db.session.delete(contract)
    db.session.commit()
    flash('合同已删除', 'success')
    return redirect(url_for('index'))


@app.route('/contract/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('修改')
def edit_contract(id):
    contract = Contract.query.get_or_404(id)

    # 新增：数据隔离检查
    customer_id = get_current_customer_id()
    if customer_id is not None and contract.customer_id != customer_id:
        flash('权限不足：无法访问其他租户的合同', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        contract.customer_name = request.form['customer_name']
        contract.project_name = request.form['project_name']
        contract.contract_number = request.form.get('contract_number')
        contract.contract_type = request.form.get('contract_type')
        contract.total_price = float(request.form['total_price'])
        contract.project_staff = request.form.get('project_staff')
        contract.sales_staff = request.form.get('sales_staff')
        contract.status = request.form.get('status')
        contract.business_type = request.form.get('business_type', '销售')
        contract.signing_date = datetime.strptime(request.form['signing_date'], '%Y-%m-%d').date() if request.form.get('signing_date') else None

        if 'contract_file' in request.files:
            file = request.files['contract_file']
            if file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                contract.file_path = filename

        # 新增：更新多产品数据 - 先删除旧的，再添加新的
        ContractProduct.query.filter_by(contract_id=contract.id).delete()

        product_names = request.form.getlist('products[product_name][]')
        contract_types = request.form.getlist('products[contract_type][]')
        product_types = request.form.getlist('products[product_type][]')
        models = request.form.getlist('products[model][]')
        units = request.form.getlist('products[unit][]')
        quantities = request.form.getlist('products[quantity][]')
        unit_prices = request.form.getlist('products[unit_price][]')
        subtotals = request.form.getlist('products[subtotal][]')
        tax_rates = request.form.getlist('products[tax_rate][]')

        for i in range(len(product_names)):
            if product_names[i].strip():
                cp = ContractProduct(
                    contract_id=contract.id,
                    product_name=product_names[i].strip() or None,
                    contract_type=contract_types[i] if i < len(contract_types) else None,
                    product_type=product_types[i].strip() if i < len(product_types) and product_types[i].strip() else None,
                    model=models[i].strip() if i < len(models) and models[i].strip() else None,
                    unit=units[i].strip() if i < len(units) and units[i].strip() else None,
                    quantity=float(quantities[i]) if i < len(quantities) and quantities[i] else None,
                    unit_price=float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else None,
                    subtotal=float(subtotals[i]) if i < len(subtotals) and subtotals[i] else None,
                    tax_rate=float(tax_rates[i]) if i < len(tax_rates) and tax_rates[i] else None
                )
                db.session.add(cp)

        # 新增：将产品名称同步到产品管理表（仅新产品）
        sync_products_to_table(product_names, models, units, tax_rates, customer_id)

        db.session.commit()
        flash('合同更新成功', 'success')
        return redirect(url_for('view_contract', id=id))

    # GET请求：数据隔离
    if customer_id is not None:
        customers_list = Customer.query.filter_by(customer_id=customer_id).order_by(Customer.name).all()
        products_list = Product.query.filter_by(customer_id=customer_id).order_by(Product.name).all()
    else:
        customers_list = Customer.query.order_by(Customer.name).all()
        products_list = Product.query.order_by(Product.name).all()

    return render_template('contract_form.html', contract=contract, customers_list=customers_list, products_list=products_list)


@app.route('/contract/<int:id>/payment', methods=['POST'])
def add_payment(id):
    payment = Payment(
        contract_id=id,
        amount=float(request.form['amount']),
        payment_date=datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date(),
        payment_type=request.form.get('payment_type'),
        note=request.form.get('note')
    )

    if 'receipt_file' in request.files:
        file = request.files['receipt_file']
        if file.filename:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            payment.receipt_file = filename

    db.session.add(payment)
    db.session.commit()
    # 新增：自动更新合同状态
    contract = Contract.query.get(id)
    if contract:
        auto_update_contract_status(contract)
        db.session.commit()
    flash('收付款记录添加成功', 'success')
    return redirect(url_for('view_contract', id=id))


@app.route('/contract/<int:id>/delivery', methods=['POST'])
@login_required
@permission_required('增加')
def add_delivery(id):
    delivery = Delivery(
        contract_id=id,
        delivery_date=datetime.strptime(request.form['delivery_date'], '%Y-%m-%d').date(),
        content=request.form.get('content'),
        note=request.form.get('note')
    )

    if 'delivery_file' in request.files:
        file = request.files['delivery_file']
        if file.filename:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            delivery.delivery_file = filename

    db.session.add(delivery)
    db.session.commit()
    flash('交付记录添加成功', 'success')
    return redirect(url_for('view_contract', id=id))


@app.route('/contract/<int:id>/invoice', methods=['POST'])
@login_required
@permission_required('增加')
def add_invoice(id):
    invoice = Invoice(
        contract_id=id,
        amount=float(request.form['amount']),
        received_date=datetime.strptime(request.form['received_date'], '%Y-%m-%d').date(),
        invoice_number=request.form.get('invoice_number'),
        note=request.form.get('note'),
        invoice_status=request.form.get('invoice_status', '未开具'),
        invoice_type=request.form.get('invoice_type', '普票'),  # 新增：发票种类
    )

    if 'invoice_file' in request.files:
        file = request.files['invoice_file']
        if file.filename:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            invoice.invoice_file = filename

    db.session.add(invoice)
    db.session.commit()
    # 新增：自动更新合同状态
    contract = Contract.query.get(id)
    if contract:
        auto_update_contract_status(contract)
        db.session.commit()
    flash('发票记录添加成功', 'success')
    return redirect(url_for('view_contract', id=id))


@app.route('/import', methods=['GET', 'POST'])
def import_contracts():
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash('请选择文件', 'warning')
            return redirect(url_for('import_contracts'))

        file = request.files['excel_file']
        if file.filename == '':
            flash('请选择文件', 'warning')
            return redirect(url_for('import_contracts'))

        # 新增：获取当前用户的租户ID
        customer_id = get_current_customer_id()

        file_bytes = file.read()

        try:
            df = pd.read_excel(io.BytesIO(file_bytes))

            required_cols = ['客户名称', '项目名称', '合同总价']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                flash(f'Excel 格式不正确，缺少必填列：{", ".join(missing_cols)}。'
                      f'请检查列名后重新上传。当前识别到的列：{", ".join(df.columns.tolist())}', 'warning')
                return redirect(url_for('import_contracts'))

            # 过滤全空行
            df = df[~(df['客户名称'].isna() & df['项目名称'].isna())]

            # ── 修改：按 (客户名称, 项目名称) 分组，支持多产品同一合同 ──
            from collections import OrderedDict
            contract_groups = OrderedDict()
            for idx, row in df.iterrows():
                cname = str(row.get('客户名称', '')) if pd.notna(row.get('客户名称')) else ''
                pname = str(row.get('项目名称', '')) if pd.notna(row.get('项目名称')) else ''
                key = (cname, pname)
                if key not in contract_groups:
                    contract_groups[key] = []
                contract_groups[key].append((idx, row))

            # 重复导入检测：按合同级别（客户名称+项目名称+合同总价）去重
            duplicates = []
            for (cname, pname), rows in contract_groups.items():
                # 取第一行的合同总价作为合同级别数据
                first_idx, first_row = rows[0]
                total_val = first_row.get('合同总价', 0)
                total_val = float(total_val) if pd.notna(total_val) else 0

                q = Contract.query.filter_by(customer_name=cname, project_name=pname, total_price=total_val)
                if customer_id is not None:
                    q = q.filter_by(customer_id=customer_id)
                exists = q.first()

                if exists:
                    duplicates.append(f"{cname} / {pname} / ¥{total_val}（共{len(rows)}个产品）")

            if duplicates:
                return render_template('import.html', duplicates=duplicates)

            count = 0
            errors = []
            for (cname, pname), rows in contract_groups.items():
                try:
                    # 取第一行作为合同级别数据
                    first_idx, first_row = rows[0]
                    total_val = first_row.get('合同总价', 0)
                    if pd.isna(total_val):
                        total_val = 0
                    staff_val = first_row.get('项目负责人') if '项目负责人' in df.columns else first_row.get('项目人员')
                    business_type_val = str(first_row.get('业务类型', '销售')) if pd.notna(first_row.get('业务类型', None)) else '销售'
                    signing_date_val = None
                    raw_date = first_row.get('签订日期', None)
                    if raw_date is not None and pd.notna(raw_date):
                        try:
                            signing_date_val = pd.to_datetime(raw_date).date()
                        except Exception:
                            signing_date_val = None

                    # 创建合同主记录
                    contract = Contract(
                        customer_name=cname or '未知客户',
                        project_name=pname or '未知项目',
                        total_price=float(total_val),
                        project_staff=str(staff_val) if staff_val is not None and pd.notna(staff_val) else None,
                        sales_staff=str(first_row.get('销售人员', '')) if pd.notna(first_row.get('销售人员', None)) else None,
                        business_type=business_type_val,
                        status=str(first_row.get('状态', '进行中')) if pd.notna(first_row.get('状态', None)) else '进行中',
                        signing_date=signing_date_val,
                        customer_id=customer_id  # 关联租户
                    )
                    db.session.add(contract)
                    db.session.flush()  # 获取 contract.id

                    # 自动同步客户信息
                    if cname and not Customer.query.filter_by(name=cname, customer_id=customer_id).first():
                        db.session.add(Customer(name=cname, customer_id=customer_id))

                    # ── 每一行对应一个产品 ──
                    for row_idx, row in rows:
                        product_name = str(row.get('产品名称', '')) if pd.notna(row.get('产品名称', None)) else None
                        if product_name:
                            cp = ContractProduct(
                                contract_id=contract.id,
                                product_name=product_name,
                                contract_type=str(row.get('合同类型', '')) if pd.notna(row.get('合同类型', None)) else None,
                                model=str(row.get('型号', '')) if pd.notna(row.get('型号', None)) else None,
                                unit=str(row.get('单位', '')) if pd.notna(row.get('单位', None)) else None,
                                quantity=float(row.get('数量', 0)) if pd.notna(row.get('数量', None)) else None,
                                unit_price=float(row.get('单价', 0)) if pd.notna(row.get('单价', None)) else None,
                                tax_rate=float(row.get('发票税率', 0)) if pd.notna(row.get('发票税率', None)) else None
                            )
                            # 计算小计
                            if cp.quantity and cp.unit_price:
                                cp.subtotal = cp.quantity * cp.unit_price
                            db.session.add(cp)

                            # 新增：同步产品到产品管理表
                            if not Product.query.filter_by(name=product_name, customer_id=customer_id).first():
                                model_val = str(row.get('型号', '')) if pd.notna(row.get('型号', None)) else None
                                unit_val = str(row.get('单位', '')) if pd.notna(row.get('单位', None)) else None
                                tax_val = float(row.get('发票税率', 0)) if pd.notna(row.get('发票税率', None)) else None
                                db.session.add(Product(
                                    name=product_name,
                                    category='其他',
                                    model=model_val or None,
                                    unit=unit_val or None,
                                    tax_rate=tax_val,
                                    customer_id=customer_id
                                ))

                    count += 1
                except Exception as row_err:
                    errors.append(f"{cname}/{pname}: {str(row_err)}")

            db.session.commit()
            msg = f'成功导入 {count} 条合同记录'
            if errors:
                msg += f'，{len(errors)} 条跳过：' + '；'.join(errors[:3])
            flash(msg, 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'导入失败: {str(e)}', 'warning')
            return redirect(url_for('import_contracts'))

    return render_template('import.html')


@app.route('/download/<filename>')
@login_required
@permission_required('下载')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)


# 系统配置（公司图标/名称）
@app.route('/sysconfig', methods=['GET', 'POST'])
@login_required
def sysconfig():
    if session.get('role') != '超级管理员':
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    if request.method == 'POST':
        for key in ['company_name', 'company_logo']:
            val = request.form.get(key, '').strip()
            cfg = SysConfig.query.filter_by(key=key).first()
            if cfg:
                cfg.value = val
            else:
                db.session.add(SysConfig(key=key, value=val))
        if 'logo_file' in request.files:
            f = request.files['logo_file']
            if f.filename:
                ext = os.path.splitext(f.filename)[1]
                logo_filename = f'company_logo{ext}'
                f.save(os.path.join('static', logo_filename))
                cfg = SysConfig.query.filter_by(key='company_logo_file').first()
                if cfg:
                    cfg.value = logo_filename
                else:
                    db.session.add(SysConfig(key='company_logo_file', value=logo_filename))
        db.session.commit()
        flash('配置保存成功', 'success')
        return redirect(url_for('sysconfig'))
    configs = {c.key: c.value for c in SysConfig.query.all()}
    return render_template('sysconfig.html', configs=configs)


@app.route('/preview/<filename>')
@login_required
def preview_file(filename):
    user = User.query.get(session['user_id'])
    if user.role != '超级管理员' and user.permissions != 'all' and '查阅' not in (user.permissions or ''):
        flash('权限不足', 'warning')
        return redirect(url_for('index'))
    from flask import Response
    import mimetypes
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    with open(file_path, 'rb') as f:
        response = Response(f.read(), mimetype=mimetype)
        response.headers['Content-Disposition'] = 'inline'
        return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
