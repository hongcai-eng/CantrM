# 修复 customer.business_type 字段缺失问题

## 问题描述
访问客户管理相关页面时出现错误：
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: customer.business_type
```

## 原因
数据库中的 `customer` 表缺少 `business_type` 字段，但代码已经升级使用了该字段。

## 解决方案

### 方法一：运行迁移脚本（推荐）

1. 停止应用（如果正在运行）
2. 在项目根目录下执行：
   ```bash
   python migrate_simple.py
   ```
3. 看到以下输出表示成功：
   ```
   [OK] customer.business_type 字段添加成功
   [SUCCESS] 数据库迁移完成！
   ```
4. 重启应用

### 方法二：手动 SQL 修复

如果迁移脚本无法运行，可以手动执行 SQL：

1. 使用 SQLite 工具连接到 `instance/contracts.db`
2. 执行以下 SQL：
   ```sql
   ALTER TABLE customer ADD COLUMN business_type VARCHAR(20) DEFAULT '销售';
   ```
3. 验证字段是否添加成功：
   ```sql
   PRAGMA table_info(customer);
   ```
4. 重启应用

### 方法三：使用 Python 直接修复

创建一个临时脚本 `fix_db.py`：
```python
import sqlite3

conn = sqlite3.connect('instance/contracts.db')
cursor = conn.cursor()

# 检查字段是否存在
cursor.execute("PRAGMA table_info(customer)")
columns = [col[1] for col in cursor.fetchall()]

if 'business_type' not in columns:
    print("正在添加 business_type 字段...")
    cursor.execute("ALTER TABLE customer ADD COLUMN business_type VARCHAR(20) DEFAULT '销售'")
    conn.commit()
    print("字段添加成功！")
else:
    print("字段已存在，无需添加")

conn.close()
```

然后运行：
```bash
python fix_db.py
```

## 验证修复

修复后，启动应用并访问客户管理页面，应该不再报错。

## 注意事项

1. **备份数据库**：修复前建议先备份 `instance/contracts.db` 文件
2. **旧数据处理**：已有客户的 `business_type` 会默认设置为"销售"
3. **多个数据库**：如果有多个环境（测试、生产），每个环境都需要执行迁移

## 预防措施

以后部署新版本时，记得：
1. 查看项目中是否有 `migrate_*.py` 脚本
2. 查看 `docs/` 目录下的升级说明文档
3. 先在测试环境执行迁移，确认无误后再上生产

---
生成时间：2026-06-30
