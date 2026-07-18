#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复数据库中缺失的文件引用
将数据库中指向不存在文件的字段清空
"""
import os
from app import app, db
from models import Contract, Payment, Delivery, Invoice

def fix_missing_files(auto_confirm=False):
    """修复缺失的文件引用"""
    upload_folder = app.config['UPLOAD_FOLDER']
    fixed_count = 0

    with app.app_context():
        print("=" * 60)
        print("开始检查并修复缺失的文件引用")
        print("=" * 60)

        # 修复合同文件
        print("\n[1] 检查合同文件...")
        contracts = Contract.query.filter(Contract.file_path != None).filter(Contract.file_path != '').all()
        contract_to_fix = []
        for contract in contracts:
            file_path = os.path.join(upload_folder, contract.file_path)
            if not os.path.exists(file_path):
                contract_to_fix.append(contract)
                print(f"  - 合同ID={contract.id}, 编号={contract.contract_number}, 文件={contract.file_path}")

        if contract_to_fix:
            if not auto_confirm:
                confirm = input(f"\n是否清空这 {len(contract_to_fix)} 个合同的文件路径? (y/n): ")
                if confirm.lower() != 'y':
                    print("跳过合同文件修复")
                    contract_to_fix = []

            if contract_to_fix:
                for contract in contract_to_fix:
                    contract.file_path = None
                    fixed_count += 1
                db.session.commit()
                print(f"[OK] 已清空 {len(contract_to_fix)} 个合同的文件路径")
        else:
            print("  [OK] 所有合同文件完整")

        # 修复付款凭证文件
        print("\n[2] 检查付款凭证文件...")
        payments = Payment.query.filter(Payment.receipt_file != None).filter(Payment.receipt_file != '').all()
        payment_to_fix = []
        for payment in payments:
            file_path = os.path.join(upload_folder, payment.receipt_file)
            if not os.path.exists(file_path):
                payment_to_fix.append(payment)
                print(f"  - 付款ID={payment.id}, 合同ID={payment.contract_id}, 文件={payment.receipt_file}")

        if payment_to_fix:
            if not auto_confirm:
                confirm = input(f"\n是否清空这 {len(payment_to_fix)} 个付款记录的文件路径? (y/n): ")
                if confirm.lower() != 'y':
                    print("跳过付款文件修复")
                    payment_to_fix = []

            if payment_to_fix:
                for payment in payment_to_fix:
                    payment.receipt_file = None
                    fixed_count += 1
                db.session.commit()
                print(f"[OK] 已清空 {len(payment_to_fix)} 个付款记录的文件路径")
        else:
            print("  [OK] 所有付款凭证文件完整")

        # 修复交付文件
        print("\n[3] 检查交付文件...")
        deliveries = Delivery.query.filter(Delivery.delivery_file != None).filter(Delivery.delivery_file != '').all()
        delivery_to_fix = []
        for delivery in deliveries:
            file_path = os.path.join(upload_folder, delivery.delivery_file)
            if not os.path.exists(file_path):
                delivery_to_fix.append(delivery)
                print(f"  - 交付ID={delivery.id}, 合同ID={delivery.contract_id}, 文件={delivery.delivery_file}")

        if delivery_to_fix:
            if not auto_confirm:
                confirm = input(f"\n是否清空这 {len(delivery_to_fix)} 个交付记录的文件路径? (y/n): ")
                if confirm.lower() != 'y':
                    print("跳过交付文件修复")
                    delivery_to_fix = []

            if delivery_to_fix:
                for delivery in delivery_to_fix:
                    delivery.delivery_file = None
                    fixed_count += 1
                db.session.commit()
                print(f"[OK] 已清空 {len(delivery_to_fix)} 个交付记录的文件路径")
        else:
            print("  [OK] 所有交付文件完整")

        # 修复发票文件
        print("\n[4] 检查发票文件...")
        invoices = Invoice.query.filter(Invoice.invoice_file != None).filter(Invoice.invoice_file != '').all()
        invoice_to_fix = []
        for invoice in invoices:
            file_path = os.path.join(upload_folder, invoice.invoice_file)
            if not os.path.exists(file_path):
                invoice_to_fix.append(invoice)
                print(f"  - 发票ID={invoice.id}, 合同ID={invoice.contract_id}, 文件={invoice.invoice_file}")

        if invoice_to_fix:
            if not auto_confirm:
                confirm = input(f"\n是否清空这 {len(invoice_to_fix)} 个发票记录的文件路径? (y/n): ")
                if confirm.lower() != 'y':
                    print("跳过发票文件修复")
                    invoice_to_fix = []

            if invoice_to_fix:
                for invoice in invoice_to_fix:
                    invoice.invoice_file = None
                    fixed_count += 1
                db.session.commit()
                print(f"[OK] 已清空 {len(invoice_to_fix)} 个发票记录的文件路径")
        else:
            print("  [OK] 所有发票文件完整")

    print("\n" + "=" * 60)
    print(f"修复完成！共处理 {fixed_count} 个缺失的文件引用")
    print("=" * 60)
    print("\n建议：")
    print("1. 如果有备份，请恢复缺失的文件到 uploads 目录")
    print("2. 或者重新上传这些文件到对应的记录")
    print("3. 现在系统不会再因为这些文件而报错")

    return fixed_count

if __name__ == '__main__':
    import sys
    auto = '--yes' in sys.argv or '-y' in sys.argv
    fix_missing_files(auto_confirm=auto)
