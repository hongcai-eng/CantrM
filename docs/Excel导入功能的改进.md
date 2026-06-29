已经完成了Excel导入功能的改进。让我为你总结一下完成的工作：

  📋 完成的修改

  1. 新增字段处理

  在 app.py 的导入功能中，新增了对以下4个字段的处理：
  - 已收付款 - 自动创建收付款记录（Payment）
  - 未收付款 - 用于验证（合同总价 - 已收付款）
  - 已开票 - 自动创建发票记录（Invoice，状态为"已开具"）
  - 未开票 - 用于验证（合同总价 - 已开票）

  2. 修改的文件

  app.py（修改了2处）

  第一处修改（第2176-2181行）：
  # 合同级字段向下填充（处理Excel合并单元格导致的NaN）
  fill_cols = ['合同编号', '客户名称', '项目名称', '合同总价', '签订日期',
               '合同类型', '业务类型', '项目负责人', '销售人员', '状态', '发票税率',
               '已收付款', '未收付款', '已开票', '未开票']  # 新增4个字段

  第二处修改（第2297行之后新增）：
  # 新增：处理已收付款和未收付款
  paid_amount = first_row.get('已收付款', 0)
  if pd.notna(paid_amount) and float(paid_amount) > 0:
      payment = Payment(
          contract_id=contract.id,
          amount=float(paid_amount),
          payment_date=signing_date_val or datetime.now().date(),
          payment_type='导入',
          note='Excel导入时的已收付款'
      )
      db.session.add(payment)

  # 新增：处理已开票和未开票
  invoiced_amount = first_row.get('已开票', 0)
  if pd.notna(invoiced_amount) and float(invoiced_amount) > 0:
      invoice = Invoice(
          contract_id=contract.id,
          amount=float(invoiced_amount),
          received_date=signing_date_val or datetime.now().date(),
          invoice_status='已开具',
          invoice_type='普票',
          note='Excel导入时的已开票'
      )
      db.session.add(invoice)

  templates/import.html（更新了使用说明）

  添加了对新增字段的说明：
  <li><strong>已收付款、未收付款、已开票、未开票</strong>（可选，导入后自动创建对应的收付款和发票记录）</li>

  3. 新增的逻辑

  ✅ 自动创建收付款记录：当Excel中"已收付款"字段大于0时，自动创建一条Payment记录
  - 金额：已收付款金额
  - 日期：使用合同签订日期（无则使用当前日期）
  - 类型：标记为"导入"
  - 备注：自动标注"Excel导入时的已收付款"

  ✅ 自动创建发票记录：当Excel中"已开票"字段大于0时，自动创建一条Invoice记录
  - 金额：已开票金额
  - 日期：使用合同签订日期（无则使用当前日期）
  - 状态：设置为"已开具"
  - 类型：默认"普票"
  - 备注：自动标注"Excel导入时的已开票"

  ✅ 数据验证：导入后，系统会根据Payment和Invoice记录自动计算：
  - 已收付款总额 = 所有Payment记录之和
  - 未收付款 = 合同总价 - 已收付款总额
  - 已开票总额 = 所有状态为"已开具"的Invoice记录之和
  - 未开票 = 合同总价 - 已开票总额

  4. 测试结果

  已使用测试文件 E:\claude\测试文件\合同导入华实.xlsx 进行完整测试：

  ✅ 成功导入 9 条合同记录

  验证结果示例：
  - HSCX-DGS-F-202512 | 总价:¥178000 | 已收:¥169100 | 未收:¥8900 | 已开票:¥0 | 未开票:¥178000
  - HSCX-DGS-F-20251201 | 总价:¥179000 | 已收:¥170050 | 未收:¥8950 | 已开票:¥150000 | 未开票:¥29000

  所有数据都正确同步到了对应的Payment和Invoice表中！

  5. 数据库字段说明

  没有新增数据库字段（完全符合你的要求：只新增，不修改原有字段）

  使用了现有的表结构：
  - Payment 表：存储收付款记录
  - Invoice 表：存储发票记录
  - 通过关联查询自动计算已收/未收、已开票/未开票金额

  6. 使用方法

  1. 登录系统（需要"导入EXCEL"权限）
  2. 访问导入页面：/import
  3. 准备Excel文件，确保包含列：已收付款、未收付款、已开票、未开票
  4. 上传文件，系统会自动：
    - 导入合同基本信息
    - 导入产品信息
    - 创建收付款记录（如果已收付款>0）
    - 创建发票记录（如果已开票>0）

  导入完成后，可在合同详情页面看到完整的收付款和发票记录！