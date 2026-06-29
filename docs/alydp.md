# 合同管理系统 - 部署日志

# 变更日志 (alydp)


## v3.1 (2026-05-05)

操作总结：

✅ 安装工具：成功安装 unzip 解压工具。
✅ 定位文件：找到上传的压缩包 /CantrM.zip。
✅ 解压覆盖：将新代码解压并移动到 /opt/CantrM 目录，覆盖旧版本。
✅ 重启服务：停止旧进程并以后台模式重新启动应用（PID: 38675）。
当前状态：

应用程序正在运行。
最新日志将输出到 /opt/CantrM/nohup.out。


验证结果：
• ✅ 进程状态：python3 app.py 进程已运行 (PID: 39536)
• ✅ 端口监听：TCP 5000 端口已监听 (0.0.0.0:5000 LISTEN)
问题根因总结：
1. 原启动脚本使用 python 命令，但系统只安装了 python3
2. Python 环境缺少 Flask 依赖包 (ModuleNotFoundError: No module named 'flask')
3. 系统启用了 PEP 668 保护，需要使用 --break-system-packages 参数安装依赖
已执行修复：
1. 使用 pip3 install -r requirements.txt --break-system-packages 安装所有依赖
2. 使用正确的 python3 命令重新启动服务
服务现在应该可以正常访问了（端口 5000）。


## v3.1 (2026-05-05)

### 优化功能

#### 1. 手机端响应式适配
- 导航栏新增汉堡菜单按钮（☰），手机端点击展开/收起菜单
- 手机端表单从两列布局改为单列
- 手机端表格支持横向滑动查看
- 手机端字体、内边距适配小屏幕
- **修改文件**：`templates/base.html`

阿里云存放路径：/opt/CantrM
Git 远程仓库已正确配置为 https://github.com/hongcai-eng/CantrM。
将执行 git pull 命令拉取最新的代码更新

---
2
3## [2026-05-01] - ECS 实例访问问题修复
4
5### 实例信息
6- **实例 ID**
: i-2ze51pstzfemfnvsc5sy
7- **实例名称**
: 合同管理系统
8- **地域**
: cn-beijing (北京)
9- **公网 IP**
: 39.96.197.212
10- **操作系统**
: Ubuntu 24.04 64位
11
12### 问题描述
13
实例状态为 Running，但无法通过 SSH 登录，也无法访问 HTTP 服务 (端口 5000)。
14
15### 根本原因
161. **SSH 密码认证被禁用**: `/etc/ssh/sshd_config` 中 `PasswordAuthentication` 设置为 `no`
172. **安全组规则限制**: 安全组入方向规则对特定 IP (111.194.200.191) 的 22 端口访问策略为 `drop`
18
19### 解决方案
201.
 ✅ 启用 SSH 密码认证
21
```bash
22
   sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
23
   sed -i 's/^#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
24   systemctl restart ssh
 
2. ✅ 重置实例登录密码
• 通过阿里云云助手在线重置密码功能完成
验证结果
• SSH 登录：成功
• HTTP 服务访问：http://39.96.197.212:5000 ✅ 可正常访问
后续建议
• 首次登录后建议立即修改为强密码
• 检查并更新安全组规则，确保允许信任 IP 的 22 端口和 5000 端口访问
• 考虑配置密钥对登录以提高安全性

