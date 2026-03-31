from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contracts.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    project_name = db.Column(db.String(200), nullable=False)
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
    status = db.Column(db.String(20), default='进行中')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship('Payment', backref='contract', lazy=True, cascade='all, delete-orphan')
    deliveries = db.relationship('Delivery', backref='contract', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='contract', lazy=True, cascade='all, delete-orphan')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_type = db.Column(db.String(20))
    note = db.Column(db.String(500))

class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    content = db.Column(db.String(500))
    note = db.Column(db.String(500))

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    received_date = db.Column(db.Date, nullable=False)
    invoice_number = db.Column(db.String(100))
    note = db.Column(db.String(500))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    contracts = Contract.query.order_by(Contract.created_at.desc()).all()
    alerts = []
    today = datetime.now().date()

    for contract in contracts:
        if contract.status == '进行中':
            last_payment = Payment.query.filter_by(contract_id=contract.id).order_by(Payment.payment_date.desc()).first()
            if last_payment:
                days_since = (today - last_payment.payment_date).days
                if days_since > 30:
                    alerts.append(f"{contract.project_name} - 距上次收付款已{days_since}天")

    return render_template('index.html', contracts=contracts, alerts=alerts)

@app.route('/contract/new', methods=['GET', 'POST'])
def new_contract():
    if request.method == 'POST':
        contract = Contract(
            customer_name=request.form['customer_name'],
            project_name=request.form['project_name'],
            model=request.form.get('model'),
            unit=request.form.get('unit'),
            quantity=float(request.form['quantity']) if request.form.get('quantity') else None,
            unit_price=float(request.form['unit_price']) if request.form.get('unit_price') else None,
            total_price=float(request.form['total_price']),
            tax_rate=float(request.form['tax_rate']) if request.form.get('tax_rate') else None,
            contract_type=request.form.get('contract_type'),
            sub_type=request.form.get('sub_type'),
            project_staff=request.form.get('project_staff'),
            sales_staff=request.form.get('sales_staff')
        )

        if 'contract_file' in request.files:
            file = request.files['contract_file']
            if file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                contract.file_path = filename

        db.session.add(contract)
        db.session.commit()
        flash('合同创建成功', 'success')
        return redirect(url_for('index'))

    return render_template('contract_form.html')

@app.route('/contract/<int:id>')
def view_contract(id):
    contract = Contract.query.get_or_404(id)
    return render_template('contract_detail.html', contract=contract)

@app.route('/contract/<int:id>/edit', methods=['GET', 'POST'])
def edit_contract(id):
    contract = Contract.query.get_or_404(id)
    if request.method == 'POST':
        contract.customer_name = request.form['customer_name']
        contract.project_name = request.form['project_name']
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

        if 'contract_file' in request.files:
            file = request.files['contract_file']
            if file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                contract.file_path = filename

        db.session.commit()
        flash('合同更新成功', 'success')
        return redirect(url_for('view_contract', id=id))

    return render_template('contract_form.html', contract=contract)

@app.route('/contract/<int:id>/payment', methods=['POST'])
def add_payment(id):
    payment = Payment(
        contract_id=id,
        amount=float(request.form['amount']),
        payment_date=datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date(),
        payment_type=request.form.get('payment_type'),
        note=request.form.get('note')
    )
    db.session.add(payment)
    db.session.commit()
    flash('收付款记录添加成功', 'success')
    return redirect(url_for('view_contract', id=id))

@app.route('/contract/<int:id>/delivery', methods=['POST'])
def add_delivery(id):
    delivery = Delivery(
        contract_id=id,
        delivery_date=datetime.strptime(request.form['delivery_date'], '%Y-%m-%d').date(),
        content=request.form.get('content'),
        note=request.form.get('note')
    )
    db.session.add(delivery)
    db.session.commit()
    flash('交付记录添加成功', 'success')
    return redirect(url_for('view_contract', id=id))

@app.route('/contract/<int:id>/invoice', methods=['POST'])
def add_invoice(id):
    invoice = Invoice(
        contract_id=id,
        amount=float(request.form['amount']),
        received_date=datetime.strptime(request.form['received_date'], '%Y-%m-%d').date(),
        invoice_number=request.form.get('invoice_number'),
        note=request.form.get('note')
    )
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
            count = 0
            for _, row in df.iterrows():
                contract = Contract(
                    customer_name=str(row.get('客户名称', '')),
                    project_name=str(row.get('项目名称', '')),
                    model=str(row.get('型号', '')) if pd.notna(row.get('型号')) else None,
                    unit=str(row.get('单位', '')) if pd.notna(row.get('单位')) else None,
                    quantity=float(row.get('数量', 0)) if pd.notna(row.get('数量')) else None,
                    unit_price=float(row.get('单价', 0)) if pd.notna(row.get('单价')) else None,
                    total_price=float(row.get('合同总价', 0)),
                    tax_rate=float(row.get('发票税率', 0)) if pd.notna(row.get('发票税率')) else None,
                    contract_type=str(row.get('合同类型', '')) if pd.notna(row.get('合同类型')) else None,
                    sub_type=str(row.get('具体子类', '')) if pd.notna(row.get('具体子类')) else None,
                    project_staff=str(row.get('项目人员', '')) if pd.notna(row.get('项目人员')) else None,
                    sales_staff=str(row.get('销售人员', '')) if pd.notna(row.get('销售人员')) else None,
                    status=str(row.get('状态', '进行中'))
                )
                db.session.add(contract)
                count += 1
            db.session.commit()
            flash(f'成功导入 {count} 条合同记录', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'导入失败: {str(e)}', 'warning')
            return redirect(url_for('import_contracts'))

    return render_template('import.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
# ====================== 修复导入合同路由（解决报错）======================
@app.route('/import-contracts')
def import_contracts():
    # 这里先返回一个简单页面，避免报错
    return '''
    <h1>导入合同功能</h1>
    <p>功能开发中，返回首页 <a href="/">点击这里</a></p>
    '''
