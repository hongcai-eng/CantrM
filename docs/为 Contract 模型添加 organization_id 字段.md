

  1. 为 Contract 模型添加 organization_id 字段

  - 在 models.py 中为 Contract 类添加了 organization_id 字段
  - 该字段与 Organization 表建立外键关系

  2. 更新数据库迁移脚本

  - 在 migrate_db.py 中添加了迁移逻辑（步骤14）
  - 成功运行迁移，为 contract 表添加了 organization_id 列

  3. 修复 SQLAlchemy 2.0 弃用警告

  - 将所有 Model.query.get(id) 替换为 db.session.get(Model, id)
  - 共修复了约 20 处调用
  - 涉及的模型：User、TenantCustomer、Contract、Position、Organization

  4. 应用程序验证

  - 应用程序成功启动，没有错误
  - 所有 SQLAlchemy 弃用警告已消除
  - 基于组织的数据权限功能现在应该可以正常工作

  修复的关键问题

  原始错误：
  AttributeError: type object 'Contract' has no attribute 'organization_id'

  现在 Contract 模型已经具有 organization_id 字段，app.py:284 中的代码可以正常工作：
  Contract.organization_id.in_(org_ids)
