# 合同管理系统 - 更新日志

## v2.5 (2026-04-17)

### 新增功能

#### 1. 导入Excel支持合同编号
- 导入时新增"合同编号"列，有合同编号时以编号区分合同（支持同一客户多份合同）
- 无合同编号时回退原逻辑（客户名称+项目名称分组）
- 重复检测优先按合同编号查重
- 导入说明页更新列名提示
- **修改文件**：`app.py`（`import_contracts`）、`templates/import.html`

#### 2. 删除收付款整条记录
- 收付款记录表格新增"删除记录"按钮，删除整条记录（含回单文件）
- 删除后自动重新计算合同未付款金额和状态
- 新增路由：`POST /payment/<pid>/delete`
- **修改文件**：`app.py`、`templates/contract_detail.html`

#### 3. 删除交付整条记录
- 交付记录表格新增"删除记录"按钮，删除整条记录（含交付文件）
- 新增路由：`POST /delivery/<did>/delete`
- **修改文件**：`app.py`、`templates/contract_detail.html`

#### 4. 删除发票整条记录
- 发票记录表格新增"删除记录"按钮，删除整条记录（含发票文件）
- 删除后自动重新计算合同未开票金额和状态
- 新增路由：`POST /invoice/<iid>/delete`
- **修改文件**：`app.py`、`templates/contract_detail.html`

#### 5. 产品明细新增"产品类型"列
- 合同详情"产品明细"表格新增"产品类型"列，显示硬件设备/软件/技术服务/技术开发
- **修改文件**：`templates/contract_detail.html`

#### 6. 合同类型移至基础信息，产品明细删除合同类型列
- 基础信息"合同编号"下方新增"合同类型"行
- 产品明细表格删除"合同类型"列
- **修改文件**：`templates/contract_detail.html`

### 修改逻辑

#### 合同状态自动回退
- `auto_update_contract_status` 新增回退逻辑：未满足完结条件时，"已完结"自动回退为"进行中"
- 编辑合同保存后也调用状态重新计算，防止手动设置"已完结"绕过验证
- **修改文件**：`app.py`

---

## v2.4 (2026-04-16)

### 新增功能

#### 1. 收付款回单文件删除
- 合同详情"收付款记录"表格回单列新增"删除"按钮
- 删除前弹窗确认，删除后同步清除磁盘文件和数据库字段
- 新增路由：`POST /payment/<pid>/delete_file`

#### 2. 交付记录文件删除
- 合同详情"交付记录"表格文件列新增"删除"按钮
- 新增路由：`POST /delivery/<did>/delete_file`

#### 3. 发票文件删除
- 合同详情"发票记录"表格发票文件列新增"删除"按钮
- 新增路由：`POST /invoice/<iid>/delete_file`

#### 4. 客户/产品名称未找到时直接跳转
- 新建合同"客户名称"搜索无结果时，下拉显示"去客户管理添加 ↗"链接，点击在新标签页打开客户管理，返回后自动重搜并展示下拉供选择
- 新建合同"产品名称"搜索无结果时，同样逻辑跳转到产品管理页

### 修改文件
- `app.py`：新增 `delete_payment_file`、`delete_delivery_file`、`delete_invoice_file` 三个路由
- `templates/contract_detail.html`：收付款/交付/发票三处文件列新增删除按钮
- `templates/contract_form.html`：客户/产品搜索无结果时改为显示跳转链接（替代原 `window.open` 方案，规避浏览器弹窗拦截）

---

## v2.3 (2026-04-16)

### 新增功能

#### F1. 合同列表新增合同编号列 + 响应式布局
- 合同列表表格首列新增"合同编号"，展示 `contract.contract_number`
- 表格包裹 `overflow-x:auto` 滚动容器，字体缩小至 13px，`white-space:nowrap` 确保单行显示
- **修改文件**：`templates/index.html`

#### F2. 合同详情基础信息字段顺序调整
- "基础信息"表格按需求重排为：合同编号、项目名称、客户名称、项目负责人、签订日期、合同总价、未付款、未开票、合同类型、业务类型、状态
- 保留原有字段：已付款、销售人员、合同文件
- **修改文件**：`templates/contract_detail.html`

#### F3. 产品类型改为下拉选择
- 新建/编辑合同的产品明细中，"产品类型"由文本输入框改为下拉选择
- 选项：硬件设备 / 软件 / 技术服务 / 技术开发（与产品管理页一致）
- 覆盖三处：现有产品循环、默认空产品块、`addProduct()` JS 模板字符串
- **修改文件**：`templates/contract_form.html`

#### F4. 产品删除按钮隐藏
- 新建/编辑合同产品行的"删除"按钮设置 `display:none`（保留 DOM 结构，不删除逻辑）
- 覆盖三处：现有产品循环、默认空产品块、`addProduct()` JS 模板字符串
- **修改文件**：`templates/contract_form.html`

#### F7. 客户名称未找到 → 跳转客户管理 → 返回自动重搜
- 客户搜索无匹配时，提示文字含"点击去客户管理添加"链接（`target="_blank"`），点击设置 `window._customerJumped = true`
- 窗口重新获得焦点时，若 `_customerJumped` 为真且输入框有值，自动重新搜索并展示下拉
- **修改文件**：`templates/contract_form.html`

#### F8. 产品名称未找到 → 跳转产品管理 → 返回自动重搜
- 产品搜索无匹配时，提示文字含"点击去产品管理添加"链接（`target="_blank"`），点击设置 `input._productJumped = true`
- 窗口重新获得焦点时，若对应产品输入框 `_productJumped` 为真且有值，自动重新搜索并展示下拉
- **修改文件**：`templates/contract_form.html`

#### F9. 租户账号合同列表新增"用户名"列
- 租户用户登录时，合同列表最后一列显示"用户名"（`contract.created_by`），共 13 列
- superadmin 等非租户账号不显示此列，保持原 12 列
- 新增字段：`Contract.created_by`（记录创建合同的用户名）
- 新建合同时自动记录 `session.get('username')` 到 `created_by`
- **修改文件**：`models.py`、`migrate_db.py`（步骤13）、`app.py`、`templates/index.html`

#### F10. 统计分析新增 16 列明细导出 + 页面展示
- 导出弹窗新增"明细数据（16列）"勾选项
- 导出 Excel 时，明细数据写入独立 sheet "明细数据"，16 列为：合同编号、客户名称、项目名称、产品名称、合同总价、发票税率、合同类型、业务类型、项目负责人、销售人员、签订日期、状态、已收付款、未收付款、已开票、未开票
- 多产品合同按产品行展开，单产品合同单行展示
- 统计页筛选表单新增"明细数据"维度勾选，页面同步显示 16 列明细表格（`overflow-x:auto`，12px 字体）
- **修改文件**：`templates/statistics.html`、`app.py`

### 数据库变更

#### 新增字段
- `contract.created_by VARCHAR(100)` — 记录创建合同的用户名（用于多租户合同归属显示）

### 修改文件汇总
- `models.py`：`Contract` 新增 `created_by` 字段
- `migrate_db.py`：新增步骤13，为 `contract` 表添加 `created_by` 字段
- `app.py`：`new_contract` 记录 `created_by`；`index` 传入 `is_tenant_user` 标志；`statistics` 新增 `detail` 维度及 `detail_contracts` 查询；`export_statistics` 新增明细 sheet 导出
- `templates/index.html`：新增合同编号首列、响应式布局、租户账号用户名列
- `templates/contract_detail.html`：基础信息字段顺序调整
- `templates/contract_form.html`：产品类型改下拉、删除按钮隐藏、客户/产品跳转重搜逻辑
- `templates/statistics.html`：新增明细导出勾选、明细页面表格

### 升级说明
- 需执行数据库迁移：`python migrate_db.py`（仅添加 `contract.created_by` 字段，已有数据不受影响）

---

## v2.2 (2026-04-15)

### 新增功能

#### 1. 合同编号
- 新建/编辑合同第一行新增"合同编号"输入框，作为合同唯一标识
- 新增字段：`Contract.contract_number`
- 合同列表导出 Excel 第一列为"合同编号"

#### 2. 合同类型移至合同级别
- "合同类型"从产品信息移至第一行（合同级别），与合同编号并排
- 新建/编辑合同时统一在合同头部选择合同类型

#### 3. 产品类型
- 产品信息中新增"产品类型"文本输入框（替代原产品级合同类型）
- 新增字段：`ContractProduct.product_type`

#### 4. 统计分析导出格式选择
- 导出弹窗新增三种格式选项：
  - 方案A：一个 sheet，各维度纵向排列
  - 方案B：一个 sheet，各维度横向并排（每维度占3列）
  - 方案C：多个 sheet，每个维度单独一个 sheet
- 按履约状态统计新增"合同总额"列，与其他维度统一

### 修改文件
- `models.py`：`Contract` 新增 `contract_number`；`ContractProduct` 新增 `product_type`
- `templates/contract_form.html`：新增合同编号、合同类型移位、产品类型字段
- `templates/statistics.html`：导出弹窗新增格式选择；按履约状态表格新增合同总额列
- `app.py`：`new_contract`/`edit_contract` 读取新字段；`export_contracts` 列顺序加合同编号；`export_statistics` 支持三种导出格式



## v2.1 (2026-04-14)

### 🎉 新增功能

#### 1. 产品自动同步
- **功能**：新建/编辑合同时，产品名称自动同步到产品管理表
- **逻辑**：检查产品是否存在，不存在则自动创建（默认分类：其他）
- **新增函数**：`sync_products_to_table()`
- **影响路由**：`new_contract()`, `edit_contract()`

#### 2. 合同状态自动完结
- **功能**：添加收付款或开票后，自动检查是否满足完结条件
- **条件**：已收付款 ≥ 合同总价 且 已开票 ≥ 合同总价
- **新增函数**：`auto_update_contract_status()`
- **影响路由**：`add_payment()`, `add_invoice()`

#### 3. 合同类型聚合显示
- **功能**：合同列表的"合同类型"列从 ContractProduct 表聚合显示
- **效果**：支持"工程/货物/服务"组合显示
- **修改文件**：`templates/index.html` 第 224 行

#### 4. 多产品 Excel 导入
- **功能**：同一合同的多个产品可分多行导入，自动合并为一份合同
- **分组规则**：按 (客户名称, 项目名称) 分组
- **重复检测**：改为合同级别（客户名称 + 项目名称 + 合同总价）
- **重写路由**：`import_contracts()`
- **使用技术**：`collections.OrderedDict` 保持行顺序

#### 5. 多产品 Excel 导出
- **功能**：每个 ContractProduct 展开为一行导出
- **列顺序**：固定 19 列（移除"具体子类"）
  - 客户名称、项目名称、产品名称、型号、单位、数量、单价
  - 合同总价、发票税率、合同类型、业务类型
  - 项目负责人、销售人员、签订日期、状态
  - 已收付款、未收付款、已开票、未开票
- **重写路由**：`export_contracts()`

#### 6. 统计维度勾选
- **功能**：统计页新增维度勾选控件，控制页面显示和导出
- **可选维度**：
  - 按项目负责人
  - 按客户
  - 按合同类型
  - 按业务类型
  - 按履约状态
- **修改文件**：`templates/statistics.html`
- **修改路由**：`statistics()`

### 🐛 Bug 修复

#### 1. 统计维度多选问题
- **问题**：勾选多个维度时只显示第一个
- **原因**：使用 `request.args.get('f_sheets')` 只能读取第一个值
- **解决**：改用 `request.args.getlist('f_sheets')` 正确处理多选 checkbox
- **影响路由**：`statistics()`

### 🔧 代码优化

#### 1. 新增辅助函数
```python
# app.py
def sync_products_to_table(product_names, models, units, tax_rates, customer_id)
def auto_update_contract_status(contract)
```

#### 2. 模板优化
- `index.html`：合同类型使用 Jinja2 过滤器链聚合显示
- `statistics.html`：所有统计表格包裹条件判断
- `import.html`：更新多产品导入说明文字

### 🗃️ 数据库变更
- **无新增字段**：所有功能均基于现有字段实现

### 📝 文档更新
- 新增 `CHANGELOG.md` 本次更新记录

### ⚠️ 重要提示
1. **无需数据库迁移**：本次更新未修改数据库结构
2. **向后兼容**：完全兼容 v2.0 数据
3. **Excel 格式**：导入时注意多产品行的客户名称和项目名称必须一致

### 🧪 测试状态
- ✅ 语法检查通过
- ✅ 产品同步功能正常
- ✅ 状态自动完结正常
- ✅ 多产品导入导出正常
- ✅ 统计维度勾选正常
- ✅ 所有路由 HTTP 200

---

## v2.0 (2026-04-09)

### 🎉 新增功能

#### 1. 品牌管理
- **登录页动态品牌显示**：切换账号时自动显示对应租户的公司名称和 Logo
- **系统内页品牌显示**：租户用户登录后，所有页面顶部显示该租户品牌
- **租户品牌设置**：superadmin 可为每个租户设置独立的公司名称和 Logo
- 新增 API：`/api/user_branding` - 根据用户名返回品牌信息

#### 2. 合同列表增强
- **筛选统计汇总**：新增统计卡片显示 6 项指标
  - 合同数量
  - 合同总金额
  - 已收付款 / 未收付款
  - 已开票 / 未开票
- **表格列优化**：新增"项目负责人"、"签订日期"、"业务类型"列
- **筛选条件**：支持 6 个筛选条件（项目负责人、客户名称、合同类型、业务类型、履约状态、签订年份）
- **导出功能**：导出时自动带上所有筛选条件

#### 3. 组织结构管理
- **组织管理**：客户超级管理员可创建、编辑、删除组织
- **层级结构**：支持父子组织关系
- **人员调动**：支持将用户调入/调出组织
- **组织成员明细**：显示每个组织的成员列表
- **权限控制**：完整的租户数据隔离
- 新增数据表：`organization`
- 新增字段：`user.organization_id`

#### 4. 统计分析增强
- **筛选功能**：支持按项目负责人、客户名称、合同类型、业务类型、履约状态、签订年份筛选
- **导出勾选**：可选择导出哪些统计项（按项目负责人、按客户、按合同类型、按业务类型、按履约状态）
- **关键词搜索**：项目负责人和客户名称支持自动补全

### 🐛 Bug 修复

#### 1. 合同类型筛选问题
- **问题**：筛选"货物"类型时没有结果
- **原因**：多产品合同升级后，数据在 `ContractProduct` 表，但筛选查询的是 `Contract` 表
- **解决**：改用 JOIN 查询 `ContractProduct` 表
- **影响路由**：`/` (index) 和 `/contract/export`

#### 2. 统计导出勾选问题
- **问题**：勾选导出内容不起作用，总是导出全部
- **原因**：URL 拼接方式可能产生重复参数或格式错误
- **解决**：使用 `URLSearchParams` API 正确处理查询参数
- **影响文件**：`templates/statistics.html`

### 🗃️ 数据库变更

#### 新增表
- `organization` - 组织结构表
  - `id` - 主键
  - `name` - 组织名称
  - `description` - 描述
  - `parent_id` - 父组织ID（支持层级）
  - `customer_id` - 租户ID（数据隔离）
  - `created_at` - 创建时间

#### 新增字段
- `tenant_customer.company_name` - 租户公司名称
- `tenant_customer.logo_file` - 租户 Logo 文件名
- `user.organization_id` - 用户所属组织ID

### 🔧 优化改进

#### 1. 代码优化
- 优化 `inject_company` context processor，支持租户品牌优先显示
- 统一合同类型筛选逻辑，使用 JOIN 查询
- 改进 URL 参数处理，避免重复参数

#### 2. 用户体验
- 登录页品牌动态加载，提升用户体验
- 统计汇总卡片实时更新，数据一目了然
- 导出功能增加"正在生成"和"下载完成"提示

#### 3. 权限控制
- 组织管理功能仅客户超级管理员可访问
- 租户管理功能仅 superadmin 可访问
- 完整的数据隔离验证

### 🗑️ 删除内容
- 删除用户 `admin`（密码为 "1" 的旧账号）

### 📝 文档更新
- 新增 `DEPLOYMENT_GUIDE.md` - 完整的部署指南
- 新增 `deploy.sh` - Linux 快速部署脚本
- 新增 `deploy.bat` - Windows 快速部署脚本
- 新增 `gunicorn_config.py` - 生产环境配置
- 更新 `TEST_REPORT.md` - 测试报告

### ⚠️ 重要提示

1. **数据库迁移**：升级前必须执行 `python migrate_db.py`
2. **浏览器缓存**：更新后请按 Ctrl+F5 强制刷新清除缓存
3. **密码安全**：首次登录后请立即修改所有默认密码
4. **生产环境**：请修改 `app.py` 中的 `SECRET_KEY`

### 🧪 测试状态
- ✅ 所有功能测试通过
- ✅ 数据隔离验证通过
- ✅ 筛选功能正常
- ✅ 导出功能正常
- ✅ 组织管理功能正常

---

## v1.0 (2026-04-07)

### 初始版本功能
- 多租户架构
- 合同管理（增删改查）
- 客户管理
- 产品管理
- 用户管理
- 统计分析
- Excel 导入导出
- 多产品合同支持

---

**升级建议**：建议所有用户升级到 v2.0，享受新功能和 Bug 修复。
