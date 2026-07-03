# 虚拟组织 + 虚拟岗位 + 岗位赋权功能实现方案

## 需求理解

根据用户反馈：
1. **虚拟组织**：跨部门项目组（临时组织，可包含多个部门的人员）
2. **虚拟岗位**：岗位模板（预定义岗位+权限，分配给用户）
3. **岗位赋权**：合同数据权限（查看/编辑特定合同）

## 数据库设计

### 1. 修改 Organization 表
添加 `is_virtual` 字段区分实体组织和虚拟组织：
```python
is_virtual = db.Column(db.Boolean, default=False)  # True=虚拟组织，False=实体组织
```

### 2. 新增 Position 表（岗位模板）
```python
class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 岗位名称：如"项目经理"
    description = db.Column(db.String(500))
    customer_id = db.Column(db.Integer, db.ForeignKey('tenant_customer.id'), nullable=False)
    
    # 功能权限（增加,删除,修改,查阅,上传,下载,导入EXCEL,导出EXCEL）
    function_permissions = db.Column(db.String(500))
    
    # 数据权限类型
    data_scope = db.Column(db.String(50), default='all')  # all=全部, org=本组织, self=仅自己创建, custom=自定义
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 3. 新增 UserPosition 表（用户岗位关联）
一个用户可以有多个岗位，支持跨组织兼任：
```python
class UserPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)  # 在哪个组织担任此岗位
    
    is_primary = db.Column(db.Boolean, default=False)  # 是否为主岗位
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 4. 新增 PositionContractPermission 表（岗位-合同权限）
```python
class PositionContractPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    permission_type = db.Column(db.String(20), default='view')  # view=查看, edit=编辑
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 5. 新增 UserOrganization 表（用户-组织多对多关系）
支持用户同时属于多个组织（实体+虚拟）：
```python
class UserOrganization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)  # 是否为主组织
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## 功能实现

### 1. 虚拟组织管理
- 创建组织时可选择"虚拟组织"类型
- 虚拟组织可以跨越实体部门边界
- 虚拟组织支持添加来自不同实体部门的成员
- 虚拟组织可以设置为"临时"，支持归档/解散

### 2. 岗位模板管理
**页面**: `/positions` (新建)

**功能**：
- 创建岗位模板（如：项目经理、技术负责人、合同审批人）
- 为岗位配置功能权限（增删改查等）
- 为岗位配置数据权限范围（全部/本组织/仅自己/自定义）
- 为岗位指定可访问的特定合同

### 3. 用户岗位分配
**页面**: 在用户管理页面增强

**功能**：
- 为用户分配一个或多个岗位
- 指定用户在哪个组织担任该岗位
- 设置主岗位（用于默认权限判断）
- 查看用户的所有岗位和权限

### 4. 权限计算逻辑
```python
def get_user_permissions(user_id):
    # 1. 获取用户所有岗位
    user_positions = UserPosition.query.filter_by(user_id=user_id).all()
    
    # 2. 合并所有岗位的功能权限
    function_perms = set()
    for up in user_positions:
        position = Position.query.get(up.position_id)
        if position.function_permissions:
            function_perms.update(position.function_permissions.split(','))
    
    # 3. 获取数据权限（可访问的合同列表）
    accessible_contracts = []
    for up in user_positions:
        position = Position.query.get(up.position_id)
        if position.data_scope == 'all':
            accessible_contracts = 'all'
            break
        elif position.data_scope == 'custom':
            # 获取自定义授权的合同
            perms = PositionContractPermission.query.filter_by(position_id=position.id).all()
            accessible_contracts.extend([p.contract_id for p in perms])
    
    return {
        'function_permissions': list(function_perms),
        'accessible_contracts': accessible_contracts
    }
```

### 5. 数据权限过滤
修改合同查询，增加数据权限过滤：
```python
def get_accessible_contracts(user):
    perms = get_user_permissions(user.id)
    
    if perms['accessible_contracts'] == 'all':
        return Contract.query.filter_by(customer_id=user.customer_id)
    else:
        return Contract.query.filter(
            Contract.id.in_(perms['accessible_contracts']),
            Contract.customer_id == user.customer_id
        )
```

## 界面设计

### 1. 组织管理页面增强
- 创建组织时增加"虚拟组织"复选框
- 虚拟组织显示特殊标识（图标/颜色）
- 支持从多个实体组织选人加入虚拟组织

### 2. 新增岗位管理页面
```
/positions
├── 岗位列表
├── 创建岗位
│   ├── 基本信息（名称、描述）
│   ├── 功能权限配置
│   ├── 数据权限范围
│   └── 自定义合同授权
├── 编辑岗位
└── 删除岗位
```

### 3. 用户管理页面增强
- 为用户分配岗位（支持多选）
- 为每个岗位指定所属组织
- 标记主岗位
- 显示用户的综合权限

### 4. 合同详情页面
- 显示当前用户对该合同的权限（查看/编辑）
- 如无权限，显示提示信息

## 数据库迁移脚本

```python
# upgrade_db_virtual_org_position.py
with app.app_context():
    # 1. 为 Organization 表添加 is_virtual 字段
    # 2. 创建 Position 表
    # 3. 创建 UserPosition 表
    # 4. 创建 PositionContractPermission 表
    # 5. 创建 UserOrganization 表
    db.create_all()
```

## 向后兼容

1. **保留现有权限系统**：User.permissions 字段保留，作为兜底权限
2. **逐步迁移**：新用户使用岗位系统，老用户可继续使用旧权限
3. **权限优先级**：岗位权限 > 组织权限 > 用户权限

## 实施步骤

1. ✅ 修改 models.py，添加新表
2. ✅ 创建数据库升级脚本
3. ✅ 实现岗位管理路由和页面
4. ✅ 实现用户岗位分配功能
5. ✅ 修改权限检查逻辑
6. ✅ 修改合同查询，增加数据权限过滤
7. ✅ 创建虚拟组织管理功能
8. ✅ 测试和文档

## 预估工作量

- 数据库设计和迁移：30分钟
- 后端路由实现：2小时
- 前端页面开发：2.5小时
- 权限逻辑重构：1.5小时
- 测试和调试：1小时
- **总计**：约7-8小时

## 风险和注意事项

1. **复杂性**：权限系统会变得更复杂，需要完善的文档
2. **性能**：多表关联查询可能影响性能，需要优化
3. **向后兼容**：需要确保不影响现有用户
4. **测试**：需要充分测试各种权限组合
