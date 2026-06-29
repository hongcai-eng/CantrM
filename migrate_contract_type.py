"""
数据库迁移脚本：确保 contract_product 表中的合同类型字段存在
此脚本只新增字段，不修改现有数据
"""
from app import app, db
from models import ContractProduct
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # 检查 contract_product 表是否存在 contract_type 字段
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('contract_product')]

            if 'contract_type' not in columns:
                print("正在添加 contract_product.contract_type 字段...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE contract_product ADD COLUMN contract_type VARCHAR(50)"))
                    conn.commit()
                print("✓ contract_product.contract_type 字段添加成功")
            else:
                print("✓ contract_product.contract_type 字段已存在")

            print("\n数据库迁移完成！")

        except Exception as e:
            print(f"迁移过程中出现错误: {e}")
            raise

if __name__ == '__main__':
    migrate()
