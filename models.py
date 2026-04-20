from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# 用户模型 - 新增 customer_id 字段实现多租户
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    permissions = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 新增：客户ID，用于多租户隔离（superadmin为None，客户超管和普通用户有值）
    customer_id = db.Column(db.Integer, db.ForeignKey('tenant_customer.id'), nullable=True)
    # 新增：组织ID，用于组织结构管理
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# 新增：租户客户表（用于多租户隔离）
class TenantCustomer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 新增：每个租户的品牌信息
    company_name = db.Column(db.String(200))
    logo_file = db.Column(db.String(200))
    # 关联的用户
    users = db.relationship('User', backref='tenant', lazy=True)


# 新增：组织结构表（支持层级，租户隔离）
class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    parent_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('tenant_customer.id'), nullable=False)
    permissions = db.Column(db.String(500))  # 新增：组织权限（增加,删除,修改,查阅,上传,下载）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 关联
    children = db.relationship('Organization', backref=db.backref('parent', remote_side=[id]), lazy=True)
    members = db.relationship('User', backref='organization', lazy=True)


# 客户信息模型 - 新增 customer_id 字段
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    province = db.Column(db.String(50))
    region = db.Column(db.String(50))
    credit_code = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 新增：所属租户客户ID
    customer_id = db.Column(db.Integer, db.ForeignKey('tenant_customer.id'), nullable=True)


# 产品信息模型 - 新增 customer_id 字段
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100))
    unit = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tax_rate = db.Column(db.Float)
    ref_quantity = db.Column(db.Float)
    ref_unit_price = db.Column(db.Float)
    # 新增：所属租户客户ID
    customer_id = db.Column(db.Integer, db.ForeignKey('tenant_customer.id'), nullable=True)


# 新增：合同产品关联表（支持一个合同包含多个产品）
class ContractProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    product_name = db.Column(db.String(200))
    model = db.Column(db.String(100))
    unit = db.Column(db.String(50))
    quantity = db.Column(db.Float)
    unit_price = db.Column(db.Float)
    subtotal = db.Column(db.Float)
    tax_rate = db.Column(db.Float)
    # 新增：每个产品可以有自己的合同类型
    contract_type = db.Column(db.String(50))  # 工程/货物/服务
    product_type = db.Column(db.String(100))  # 新增：产品类型
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(100))  # 新增：合同编号
    customer_name = db.Column(db.String(200), nullable=False)
    project_name = db.Column(db.String(200), nullable=False)
    # 保留原有字段用于兼容，但主要使用 ContractProduct
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
    # 新增：所属租户客户ID
    customer_id = db.Column(db.Integer, db.ForeignKey('tenant_customer.id'), nullable=True)
    # 新增：创建人用户名
    created_by = db.Column(db.String(100))

    payments = db.relationship('Payment', backref='contract', lazy=True, cascade='all, delete-orphan')
    deliveries = db.relationship('Delivery', backref='contract', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='contract', lazy=True, cascade='all, delete-orphan')
    # 新增：关联的产品列表
    products = db.relationship('ContractProduct', backref='contract', lazy=True, cascade='all, delete-orphan')

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
    invoice_type = db.Column(db.String(20), default='普票')


class SysConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500))
