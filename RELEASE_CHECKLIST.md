# 发布前检查清单

## 📋 发布准备

### 1. 代码检查
- [x] 所有功能已测试通过
- [x] 数据库迁移脚本已验证
- [x] 删除了测试代码和调试信息
- [x] 删除了 admin 用户（旧账号）
- [ ] 修改 app.py 中的 SECRET_KEY（生产环境必须）
- [x] 确认 debug=False（生产环境）

### 2. 文件准备
- [x] DEPLOYMENT_GUIDE.md - 部署指南
- [x] CHANGELOG.md - 更新日志
- [x] deploy.sh - Linux 部署脚本
- [x] deploy.bat - Windows 部署脚本
- [x] gunicorn_config.py - 生产环境配置
- [x] requirements.txt - Python 依赖列表
- [x] migrate_db.py - 数据库迁移脚本

### 3. 数据库检查
- [x] instance/contracts.db 存在
- [x] 数据库包含最新表结构
- [x] 测试数据已清理（如需要）
- [x] 数据库文件权限正确

### 4. 静态文件检查
- [x] static/ 目录包含所有 Logo 文件
- [x] uploads/ 目录存在
- [x] 文件权限正确

---

## 🚀 发布步骤

### 方案 A：本地网络部署（推荐用于内部测试）

1. **打包文件**
   ```bash
   # 创建发布包
   cd E:\claude
   tar -czf cantrm-v2.0.tar.gz cantrm/
   # 或使用 zip
   zip -r cantrm-v2.0.zip cantrm/
   ```

2. **上传到服务器**
   - 使用 FTP/SFTP 工具（如 FileZilla）
   - 或使用 scp 命令：
     ```bash
     scp cantrm-v2.0.tar.gz user@server:/var/www/
     ```

3. **服务器端解压并部署**
   ```bash
   cd /var/www
   tar -xzf cantrm-v2.0.tar.gz
   cd cantrm
   bash deploy.sh
   ```

4. **启动应用**
   ```bash
   source venv/bin/activate
   python app.py
   # 或使用 Gunicorn
   gunicorn -c gunicorn_config.py app:app
   ```

### 方案 B：共享文件夹（局域网）

1. **设置共享文件夹**
   - 将 `E:\claude\cantrm` 设置为网络共享
   - 设置访问权限

2. **同事访问**
   - 映射网络驱动器
   - 直接运行 `deploy.bat`（Windows）

### 方案 C：Git 仓库（推荐用于团队协作）

1. **初始化 Git 仓库**
   ```bash
   cd E:\claude\cantrm
   git init
   git add .
   git commit -m "Release v2.0"
   ```

2. **推送到远程仓库**
   ```bash
   # 添加远程仓库（如 GitLab/GitHub/Gitee）
   git remote add origin https://your-git-server/cantrm.git
   git push -u origin main
   ```

3. **同事克隆并部署**
   ```bash
   git clone https://your-git-server/cantrm.git
   cd cantrm
   bash deploy.sh
   ```

---

## 🔍 部署后验证

### 1. 基础功能测试
- [ ] 访问 http://服务器IP:5000 能正常打开登录页
- [ ] superadmin 能正常登录
- [ ] 租户管理员能正常登录
- [ ] 登录页品牌显示正确

### 2. 核心功能测试
- [ ] 合同列表显示正常
- [ ] 筛选功能正常工作
- [ ] 统计汇总卡片显示正确
- [ ] 导出 Excel 功能正常
- [ ] 统计导出勾选功能正常

### 3. 新功能测试
- [ ] 组织管理页面可访问（客户超管）
- [ ] 创建组织功能正常
- [ ] 人员调动功能正常
- [ ] 品牌设置功能正常

### 4. 数据隔离测试
- [ ] 不同租户看不到对方数据
- [ ] 筛选结果正确
- [ ] 导出数据正确

---

## 📧 通知同事

### 邮件模板

**主题**：合同管理系统 v2.0 发布通知

**正文**：

各位同事：

合同管理系统 v2.0 已发布，请按以下步骤进行测试：

**访问地址**：
http://[服务器IP]:5000

**测试账号**：
- 总超级管理员：superadmin / 654321
- 创鑫汇智：admin1 / 123456
- 亿海立达：admin2 / 123456
- 中科跃达：admin3 / 123456

**重要提示**：
1. 首次访问请按 Ctrl+F5 强制刷新清除缓存
2. 首次登录后请立即修改密码
3. 如遇问题请查看附件《部署指南》

**本次更新内容**：
1. ✅ 登录页和系统内页品牌显示
2. ✅ 合同列表筛选统计汇总
3. ✅ 组织结构管理功能
4. ✅ 修复合同类型筛选问题
5. ✅ 修复统计导出勾选问题

详细更新内容请查看附件《更新日志》。

**测试重点**：
- 合同类型筛选（货物/服务/工程）
- 统计导出勾选功能
- 组织管理功能（客户超管可见）

如有问题请及时反馈。

---

## 📞 技术支持

### 常见问题

**Q1：无法访问系统**
- 检查服务器是否启动
- 检查防火墙是否开放 5000 端口
- 检查 IP 地址是否正确

**Q2：登录后页面显示异常**
- 按 Ctrl+F5 强制刷新
- 清除浏览器缓存
- 尝试使用无痕模式

**Q3：导出功能不起作用**
- 检查浏览器是否阻止下载
- 检查磁盘空间是否充足
- 查看浏览器控制台错误信息

**Q4：数据库错误**
- 确认已执行 migrate_db.py
- 检查数据库文件权限
- 查看错误日志

---

## 🎯 回滚方案

如果新版本出现严重问题，可以回滚到旧版本：

1. **停止服务**
   ```bash
   sudo systemctl stop cantrm
   ```

2. **恢复数据库备份**
   ```bash
   cp backups/contracts_backup.db instance/contracts.db
   ```

3. **切换到旧版本代码**
   ```bash
   git checkout v1.0
   ```

4. **重启服务**
   ```bash
   sudo systemctl start cantrm
   ```

---

**发布负责人**：_____________
**发布日期**：2026-04-09
**版本号**：v2.0
