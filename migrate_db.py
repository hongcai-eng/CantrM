"""
数据库迁移脚本 - 添加多租户和多产品支持
执行方式：python migrate_db.py
"""
import sqlite3
import os
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = 'instance/contracts.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print("数据库文件不存在，将在首次运行时自动创建")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("开始数据库迁移...")

    # 1. 创建租户客户表
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenant_customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL UNIQUE,
                description VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] 创建 tenant_customer 表")
    except Exception as e:
        print(f"[ERROR] tenant_customer 表创建失败: {e}")

    # 2. 为 User 表添加 customer_id 字段
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN customer_id INTEGER")
        print("[OK] User 表添加 customer_id 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] User.customer_id 字段已存在")
        else:
            print(f"[ERROR] User 表添加字段失败: {e}")

    # 3. 为 Customer 表添加 customer_id 字段
    try:
        cursor.execute("ALTER TABLE customer ADD COLUMN customer_id INTEGER")
        print("[OK] Customer 表添加 customer_id 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] Customer.customer_id 字段已存在")
        else:
            print(f"[ERROR] Customer 表添加字段失败: {e}")

    # 4. 为 Product 表添加 customer_id 字段
    try:
        cursor.execute("ALTER TABLE product ADD COLUMN customer_id INTEGER")
        print("[OK] Product 表添加 customer_id 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] Product.customer_id 字段已存在")
        else:
            print(f"[ERROR] Product 表添加字段失败: {e}")

    # 5. 为 Contract 表添加 customer_id 字段
    try:
        cursor.execute("ALTER TABLE contract ADD COLUMN customer_id INTEGER")
        print("[OK] Contract 表添加 customer_id 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] Contract.customer_id 字段已存在")
        else:
            print(f"[ERROR] Contract 表添加字段失败: {e}")

    # 6. 创建合同产品关联表
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contract_product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                product_name VARCHAR(200),
                model VARCHAR(100),
                unit VARCHAR(50),
                quantity FLOAT,
                unit_price FLOAT,
                subtotal FLOAT,
                tax_rate FLOAT,
                contract_type VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES contract(id)
            )
        """)
        print("[OK] 创建 contract_product 表")
    except Exception as e:
        print(f"[ERROR] contract_product 表创建失败: {e}")

    # 7. 为 tenant_customer 表添加 company_name 字段
    try:
        cursor.execute("ALTER TABLE tenant_customer ADD COLUMN company_name VARCHAR(200)")
        print("[OK] tenant_customer 表添加 company_name 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] tenant_customer.company_name 字段已存在")
        else:
            print(f"[ERROR] tenant_customer 表添加字段失败: {e}")

    # 8. 为 tenant_customer 表添加 logo_file 字段
    try:
        cursor.execute("ALTER TABLE tenant_customer ADD COLUMN logo_file VARCHAR(200)")
        print("[OK] tenant_customer 表添加 logo_file 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] tenant_customer.logo_file 字段已存在")
        else:
            print(f"[ERROR] tenant_customer 表添加字段失败: {e}")

    # 9. 创建组织结构表
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                description VARCHAR(500),
                parent_id INTEGER,
                customer_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES organization(id),
                FOREIGN KEY (customer_id) REFERENCES tenant_customer(id)
            )
        """)
        print("[OK] 创建 organization 表")
    except Exception as e:
        print(f"[ERROR] organization 表创建失败: {e}")

    # 10. 为 user 表添加 organization_id 字段
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN organization_id INTEGER")
        print("[OK] user 表添加 organization_id 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] user.organization_id 字段已存在")
        else:
            print(f"[ERROR] user 表添加字段失败: {e}")

    # 11. 为 contract 表添加 contract_number 字段
    try:
        cursor.execute("ALTER TABLE contract ADD COLUMN contract_number VARCHAR(100)")
        print("[OK] contract 表添加 contract_number 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] contract.contract_number 字段已存在")
        else:
            print(f"[ERROR] contract 表添加字段失败: {e}")

    # 12. 为 contract_product 表添加 product_type 字段
    try:
        cursor.execute("ALTER TABLE contract_product ADD COLUMN product_type VARCHAR(100)")
        print("[OK] contract_product 表添加 product_type 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] contract_product.product_type 字段已存在")
        else:
            print(f"[ERROR] contract_product 表添加字段失败: {e}")

    # 13. 为 contract 表添加 created_by 字段
    try:
        cursor.execute("ALTER TABLE contract ADD COLUMN created_by VARCHAR(100)")
        print("[OK] contract 表添加 created_by 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] contract.created_by 字段已存在")
        else:
            print(f"[ERROR] contract 表添加字段失败: {e}")

    conn.commit()
    conn.close()
    print("\n数据库迁移完成！")

if __name__ == '__main__':
    migrate()
