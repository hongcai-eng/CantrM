from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import io
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contracts.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ── 自定义模板过滤器：去掉浮点数尾部多余的0，如 6.0 → 6，6.5 → 6.5 ──
@app.template_filter('notrailzero')
def notrailzero_filter(val):
    if val is None:
        return ''
    return '{:g}'.format(float(val))


# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    permissions = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# 客户信息模型
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    province = db.Column(db.String(50))
    region = db.Column(db.String(50))
    credit_code = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 产品信息模型
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100))
    unit = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 新增字段
    tax_rate = db.Column(db.Float)        # 产品默认税率
    ref_quantity = db.Column(db.Float)    # 参考数量
    ref_unit_price = db.Column(db.Float)  # 参考单价


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    project_name = db.Column(db.String(200), nullable=False)
    product_name = db.Column(db.String(200))
    model = db.Column(db.String(100))
    unit = db.Column(db.String(50))
    quantity = db.Column(db.Float)
    unit_price = db.Column(db.Float)
    total_price = db.Column(db.Float, nullable=False)
    tax_rate = db.Column(db.Float)
    contract_type = db.Column(db.String(50))
    sub_type = db.Column(db.String(100))
    project_staff = db.Column(db.String(200))
    sales_staff = db.Column(db.String(100))
    file_path = db.Column(db.String(500))
    signing_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='进行中')
    business_type = db.Column(db.String(20), default='销售')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship('Payment', backref='contract', lazy=True, cascade='all, delete-orphan')
    deliveries = db.relationship('Delivery', backref='contract', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='contract', lazy=True, cascade='all, delete-orphan')

    def get_total_paid(self):
        return sum(p.amount for p in self.payments)

    def get_unpaid_amount(self):
        return self.total_price - self.get_total_paid()

    def get_total_invoiced(self):
        return sum(i.amount for i in self.invoices if i.invoice_status == '已开具')

    def get_uninvoiced_amount(self):
        return self.total_price - self.get_total_invoiced()


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_type = db.Column(db.String(20))
    note = db.Column(db.String(500))
    receipt_file = db.Column(db.String(500))


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    content = db.Column(db.String(500))
    note = db.Column(db.String(500))
    delivery_file = db.Column(db.String(500))


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    received_date = db.Column(db.Date, nullable=False)
    invoice_number = db.Column(db.String(100))
    note = db.Column(db.String(500))
    invoice_file = db.Column(db.String(500))
    invoice_status = db.Column(db.String(20), default='未开具')
    invoice_type = db.Column(db.String(20), default='普票')  # 新增：专票/普票


# 系统配置模型
class SysConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500))


with app.app_context():
    db.create_all()
    # 初始化超级管理员 admin
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='超级管理员', permissions='all')
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
    # 新增：初始化 superadmin（可管理 admin 用户）
    if not User.query.filter_by(username='superadmin').first():
        sa = User(username='superadmin', role='超级管理员', permissions='all')
        sa.set_password('654321')
        db.session.add(sa)
        db.session.commit()


@app.context_processor
def inject_company():
    try:
        configs = {c.key: c.value for c in SysConfig.query.all()}
    except Exception:
        configs = {}
    return dict(company_name=configs.get('company_name', ''), company_logo_file=configs.get('company_logo_file', ''))


# ── 辅助：判断当前登录者是否为 superadmin ──
def is_superadmin():
    return session.get('username') == 'superadmin'


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
            return redirect(url_for('index'))
        flash('用户名或密码错误', 'warning')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    from sqlalchemy import func
    query = Contract.query

    # 原有筛选条件
    if request.args.get('project_staff'):
        query = query.filter(Contract.project_staff.like(f"%{request.args.get('project_staff')}%"))
    if request.args.get('customer_name'):
        query = query.filter(Contract.customer_name.like(f"%{request.args.get('customer_name')}%"))
    if request.args.get('contract_type'):
        query = query.filter(Contract.contract_type == request.args.get('contract_type'))
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

    return render_template('index.html', contracts=contracts, alerts=alerts, available_years=available_years)


# ── 新增：合同列表导出 Excel ──
@app.route('/contract/export')
@login_required
def export_contracts():
    from sqlalchemy import func
    query = Contract.query

    if request.args.get('project_staff'):
        query = query.filter(Contract.project_staff.like(f"%{request.args.get('project_staff')}%"))
    if request.args.get('customer_name'):
        query = query.filter(Contract.customer_name.like(f"%{request.args.get('customer_name')}%"))
    if request.args.get('contract_type'):
        query = query.filter(Contract.contract_type == request.args.get('contract_type'))
    if request.args.get('status'):
        query = query.filter(Contract.status == request.args.get('status'))
    if request.args.get('business_type'):
        query = query.filter(Contract.business_type == request.args.get('business_type'))
    if request.args.get('signing_year'):
        query = query.filter(func.strftime('%Y', Contract.signing_date) == request.args.get('signing_year'))

    contracts = query.order_by(Contract.created_at.desc()).all()

    data = []
    for c in contracts:
        data.append({
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
            '具体子类': c.sub_type or '',
            '项目负责人': c.project_staff or '',
            '销售人员': c.sales_staff or '',
            '签订日期': str(c.signing_date) if c.signing_date else '',
            '状态': c.status or '',
            '已收付款': c.get_total_paid(),
            '未收付款': c.get_unpaid_amount(),
            '已开票': c.get_total_invoiced(),
            '未开票': c.get_uninvoiced_amount(),
        })

    df = pd.DataFrame(data)
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
    users = User.query.all()
    return render_template('users.html', users=users, is_superadmin=is_superadmin())


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
        user = User(
            username=request.form['username'],
            role=role,
            permissions=','.join(request.form.getlist('permissions'))
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('用户创建成功', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', is_superadmin=is_superadmin())


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
        credit_code=request.form.get('credit_code')
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
    customers = Customer.query.filter(Customer.name.like(f'%{query}%')).limit(10).all()
    return jsonify([{'id': c.id, 'name': c.name, 'province': c.province} for c in customers])


# ── 新增：项目负责人关键字搜索（从合同记录中提取，支持逗号分隔的多人） ──
@app.route('/api/project_staff/search')
@login_required
def search_project_staff():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    rows = db.session.query(Contract.project_staff).filter(
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
    products = Product.query.filter(Product.name.like(f'%{query}%')).limit(10).all()
    return jsonify([{
        'id': p.id, 'name': p.name, 'model': p.model, 'unit': p.unit,
        'tax_rate': p.tax_rate, 'ref_quantity': p.ref_quantity, 'ref_unit_price': p.ref_unit_price
    } for p in products])


@app.route('/statistics')
@login_required
def statistics():
    from sqlalchemy import func
    q = Contract.query
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

    stats = {
        'by_staff': q.with_entities(Contract.project_staff, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.project_staff).all(),
        'by_customer': q.with_entities(Contract.customer_name, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.customer_name).all(),
        'by_type': q.with_entities(Contract.contract_type, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.contract_type).all(),
        'by_status': q.with_entities(Contract.status, func.count(Contract.id)).group_by(Contract.status).all(),
        'by_business': q.with_entities(Contract.business_type, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.business_type).all(),
    }
    filters = {'f_staff': f_staff, 'f_customer': f_customer, 'f_type': f_type,
               'f_business': f_business, 'f_status': f_status, 'f_year': f_year}

    # 新增：获取可用年份列表
    years_raw = db.session.query(func.strftime('%Y', Contract.signing_date)).filter(
        Contract.signing_date.isnot(None)
    ).distinct().order_by(func.strftime('%Y', Contract.signing_date).desc()).all()
    available_years = [int(y[0]) for y in years_raw if y[0]]

    return render_template('statistics.html', stats=stats, filters=filters, available_years=available_years)


# ── 新增：统计分析导出 Excel ──
@app.route('/statistics/export')
@login_required
def export_statistics():
    from sqlalchemy import func
    q = Contract.query
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

    by_staff = q.with_entities(Contract.project_staff, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.project_staff).all()
    by_customer = q.with_entities(Contract.customer_name, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.customer_name).all()
    by_type = q.with_entities(Contract.contract_type, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.contract_type).all()
    by_business = q.with_entities(Contract.business_type, func.count(Contract.id), func.sum(Contract.total_price)).group_by(Contract.business_type).all()
    by_status = q.with_entities(Contract.status, func.count(Contract.id)).group_by(Contract.status).all()

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        pd.DataFrame(by_staff, columns=['项目负责人', '合同数量', '合同总额']).to_excel(writer, index=False, sheet_name='按项目负责人')
        pd.DataFrame(by_customer, columns=['客户名称', '合同数量', '合同总额']).to_excel(writer, index=False, sheet_name='按客户')
        pd.DataFrame(by_type, columns=['合同类型', '合同数量', '合同总额']).to_excel(writer, index=False, sheet_name='按合同类型')
        pd.DataFrame(by_business, columns=['业务类型', '合同数量', '合同总额']).to_excel(writer, index=False, sheet_name='按业务类型')
        pd.DataFrame(by_status, columns=['状态', '合同数量']).to_excel(writer, index=False, sheet_name='按履约状态')
    buf.seek(0)
    filename = f"统计导出_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    return send_file(buf, download_name=filename, as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/contract/new', methods=['GET', 'POST'])
@login_required
@permission_required('增加')
def new_contract():
    if request.method == 'POST':
        contract = Contract(
            customer_name=request.form['customer_name'],
            project_name=request.form['project_name'],
            product_name=request.form.get('product_name'),
            model=request.form.get('model'),
            unit=request.form.get('unit'),
            quantity=float(request.form['quantity']) if request.form.get('quantity') else None,
            unit_price=float(request.form['unit_price']) if request.form.get('unit_price') else None,
            total_price=float(request.form['total_price']),
            tax_rate=float(request.form['tax_rate']) if request.form.get('tax_rate') else None,
            contract_type=request.form.get('contract_type'),
            sub_type=request.form.get('sub_type'),
            project_staff=request.form.get('project_staff'),
            sales_staff=request.form.get('sales_staff'),
            business_type=request.form.get('business_type', '销售'),
            signing_date=datetime.strptime(request.form['signing_date'], '%Y-%m-%d').date() if request.form.get('signing_date') else None
        )

        if 'contract_file' in request.files:
            file = request.files['contract_file']
            if file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                contract.file_path = filename

        if not Customer.query.filter_by(name=contract.customer_name).first():
            db.session.add(Customer(name=contract.customer_name))

        db.session.add(contract)
        db.session.commit()
        flash('合同创建成功', 'success')
        return redirect(url_for('index'))

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
    if request.method == 'POST':
        contract.customer_name = request.form['customer_name']
        contract.project_name = request.form['project_name']
        contract.product_name = request.form.get('product_name')
        contract.model = request.form.get('model')
        contract.unit = request.form.get('unit')
        contract.quantity = float(request.form['quantity']) if request.form.get('quantity') else None
        contract.unit_price = float(request.form['unit_price']) if request.form.get('unit_price') else None
        contract.total_price = float(request.form['total_price'])
        contract.tax_rate = float(request.form['tax_rate']) if request.form.get('tax_rate') else None
        contract.contract_type = request.form.get('contract_type')
        contract.sub_type = request.form.get('sub_type')
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

        db.session.commit()
        flash('合同更新成功', 'success')
        return redirect(url_for('view_contract', id=id))

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

        try:
            df = pd.read_excel(file)

            # 新增：校验必填列是否存在
            required_cols = ['客户名称', '项目名称', '合同总价']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                flash(f'Excel 格式不正确，缺少必填列：{", ".join(missing_cols)}。'
                      f'请检查列名后重新上传。当前识别到的列：{", ".join(df.columns.tolist())}', 'warning')
                return redirect(url_for('import_contracts'))

            count = 0
            errors = []
            for idx, row in df.iterrows():
                try:
                    total_val = row.get('合同总价', 0)
                    if pd.isna(total_val):
                        total_val = 0
                    # 兼容"项目负责人"和"项目人员"两种列名
                    staff_val = row.get('项目负责人') if '项目负责人' in df.columns else row.get('项目人员')
                    contract = Contract(
                        customer_name=str(row.get('客户名称', '')) if pd.notna(row.get('客户名称')) else '未知客户',
                        project_name=str(row.get('项目名称', '')) if pd.notna(row.get('项目名称')) else '未知项目',
                        product_name=str(row.get('产品名称', '')) if pd.notna(row.get('产品名称', None)) else None,
                        model=str(row.get('型号', '')) if pd.notna(row.get('型号', None)) else None,
                        unit=str(row.get('单位', '')) if pd.notna(row.get('单位', None)) else None,
                        quantity=float(row.get('数量', 0)) if pd.notna(row.get('数量', None)) else None,
                        unit_price=float(row.get('单价', 0)) if pd.notna(row.get('单价', None)) else None,
                        total_price=float(total_val),
                        tax_rate=float(row.get('发票税率', 0)) if pd.notna(row.get('发票税率', None)) else None,
                        contract_type=str(row.get('合同类型', '')) if pd.notna(row.get('合同类型', None)) else None,
                        sub_type=str(row.get('具体子类', '')) if pd.notna(row.get('具体子类', None)) else None,
                        project_staff=str(staff_val) if staff_val is not None and pd.notna(staff_val) else None,
                        sales_staff=str(row.get('销售人员', '')) if pd.notna(row.get('销售人员', None)) else None,
                        business_type=str(row.get('业务类型', '销售')) if pd.notna(row.get('业务类型', None)) else '销售',
                        status=str(row.get('状态', '进行中')) if pd.notna(row.get('状态', None)) else '进行中',
                        signing_date=pd.to_datetime(row.get('签订日期')).date() if pd.notna(row.get('签订日期', None)) else None,
                    )
                    db.session.add(contract)
                    count += 1
                except Exception as row_err:
                    errors.append(f"第{idx+2}行: {str(row_err)}")
            db.session.commit()
            msg = f'成功导入 {count} 条合同记录'
            if errors:
                msg += f'，{len(errors)} 行跳过：' + '；'.join(errors[:3])
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
