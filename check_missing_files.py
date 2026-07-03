#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查数据库中记录的文件与实际文件系统的对应关系
找出所有缺失的文件记录
"""
import os
from app import app, db
from models import Contract, Payment, Delivery, Invoice

def check_missing_files():
    """检查所有文件引用，找出缺失的文件"""
    missing_files = []
    upload_folder = app.config['UPLOAD_FOLDER']

    with app.app_context():
        # 检查合同文件
        print("=" * 60)
        print("检查合同文件 (Contract.file_path)")
        print("=" * 60)
        contracts = Contract.query.filter(Contract.file_path != None).filter(Contract.file_path != '').all()
        for contract in contracts:
            file_path = os.path.join(upload_folder, contract.file_path)
            if not os.path.exists(file_path):
                missing_files.append({
                    'type': 'contract',
                    'id': contract.id,
                    'contract_number': contract.contract_number,
                    'customer_name': contract.customer_name,
                    'project_name': contract.project_name,
                    'file_path': contract.file_path,
                    'full_path': file_path
                })
                print(f"[X] 缺失: 合同ID={contract.id}, 编号={contract.contract_number}, 文件={contract.file_path}")
            else:
                print(f"[OK] 存在: 合同ID={contract.id}, 文件={contract.file_path}")

        # 检查付款凭证文件
        print("\n" + "=" * 60)
        print("检查付款凭证文件 (Payment.receipt_file)")
        print("=" * 60)
        payments = Payment.query.filter(Payment.receipt_file != None).filter(Payment.receipt_file != '').all()
        for payment in payments:
            file_path = os.path.join(upload_folder, payment.receipt_file)
            if not os.path.exists(file_path):
                contract = Contract.query.get(payment.contract_id)
                missing_files.append({
                    'type': 'payment',
                    'id': payment.id,
                    'contract_id': payment.contract_id,
                    'contract_number': contract.contract_number if contract else 'N/A',
                    'amount': payment.amount,
                    'file_path': payment.receipt_file,
                    'full_path': file_path
                })
                print(f"[X] 缺失: 付款ID={payment.id}, 合同ID={payment.contract_id}, 金额={payment.amount}, 文件={payment.receipt_file}")
            else:
                print(f"[OK] 存在: 付款ID={payment.id}, 文件={payment.receipt_file}")

        # 检查交付文件
        print("\n" + "=" * 60)
        print("检查交付文件 (Delivery.delivery_file)")
        print("=" * 60)
        deliveries = Delivery.query.filter(Delivery.delivery_file != None).filter(Delivery.delivery_file != '').all()
        for delivery in deliveries:
            file_path = os.path.join(upload_folder, delivery.delivery_file)
            if not os.path.exists(file_path):
                contract = Contract.query.get(delivery.contract_id)
                missing_files.append({
                    'type': 'delivery',
                    'id': delivery.id,
                    'contract_id': delivery.contract_id,
                    'contract_number': contract.contract_number if contract else 'N/A',
                    'content': delivery.content,
                    'file_path': delivery.delivery_file,
                    'full_path': file_path
                })
                print(f"[X] 缺失: 交付ID={delivery.id}, 合同ID={delivery.contract_id}, 文件={delivery.delivery_file}")
            else:
                print(f"[OK] 存在: 交付ID={delivery.id}, 文件={delivery.delivery_file}")

        # 检查发票文件
        print("\n" + "=" * 60)
        print("检查发票文件 (Invoice.invoice_file)")
        print("=" * 60)
        invoices = Invoice.query.filter(Invoice.invoice_file != None).filter(Invoice.invoice_file != '').all()
        for invoice in invoices:
            file_path = os.path.join(upload_folder, invoice.invoice_file)
            if not os.path.exists(file_path):
                contract = Contract.query.get(invoice.contract_id)
                missing_files.append({
                    'type': 'invoice',
                    'id': invoice.id,
                    'contract_id': invoice.contract_id,
                    'contract_number': contract.contract_number if contract else 'N/A',
                    'invoice_number': invoice.invoice_number,
                    'amount': invoice.amount,
                    'file_path': invoice.invoice_file,
                    'full_path': file_path
                })
                print(f"[X] 缺失: 发票ID={invoice.id}, 合同ID={invoice.contract_id}, 发票号={invoice.invoice_number}, 文件={invoice.invoice_file}")
            else:
                print(f"[OK] 存在: 发票ID={invoice.id}, 文件={invoice.invoice_file}")

    # 汇总报告
    print("\n" + "=" * 60)
    print("汇总报告")
    print("=" * 60)
    if missing_files:
        print(f"\n共发现 {len(missing_files)} 个文件缺失:\n")
        for item in missing_files:
            print(f"类型: {item['type']}, ID: {item['id']}, 文件: {item['file_path']}")

        print("\n" + "=" * 60)
        print("修复选项:")
        print("=" * 60)
        print("1. 手动恢复文件到 uploads 目录")
        print("2. 运行修复脚本清空数据库中的缺失文件路径")
        print("   命令: python fix_missing_files.py")
    else:
        print("[OK] 所有文件都完整存在，没有发现缺失！")

    return missing_files

if __name__ == '__main__':
    missing = check_missing_files()
